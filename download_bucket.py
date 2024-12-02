import os
import sys
import threading

import boto3


class ProgressPercentage(object):

    def __init__(self, client, bucket, filename):
        self._filename = filename
        self._size = client.head_object(Bucket=bucket, Key=filename)["ContentLength"]
        self._seen_so_far = 0
        self._lock = threading.Lock()

    def __call__(self, bytes_amount):
        # To simplify, assume this is hooked up to a single filename
        with self._lock:
            self._seen_so_far += bytes_amount
            percentage = (self._seen_so_far / self._size) * 100
            sys.stdout.write(
                "\r%s  %s / %s  (%.2f%%)"
                % (self._filename, self._seen_so_far, self._size, percentage)
            )
            sys.stdout.flush()


def download_bucket(bucket_name, local_folder):

    s3_client = boto3.client("s3")
    continuation_token = None
    all_files = []

    while True:
        if continuation_token:
            response = s3_client.list_objects_v2(
                Bucket=bucket_name, ContinuationToken=continuation_token
            )
        else:
            response = s3_client.list_objects_v2(Bucket=bucket_name)

        # Check if 'Contents' key is in the response
        if "Contents" in response:
            for obj in response["Contents"]:
                all_files.append(obj["Key"])

        # Check if there are more files to list
        if response.get("IsTruncated"):  # Check if there are more results
            continuation_token = response.get("NextContinuationToken")
        else:
            break

    for object_name in all_files:

        object_arr = object_name.split("/")

        local_path = os.path.join(local_folder, *object_arr)

        # check if the file already exists in local
        if os.path.exists(local_path):
            print(f"{local_path} already exists in local")
            continue

        # create the folder if it does not exist
        os.makedirs(os.path.dirname(local_path), exist_ok=True)

        s3_client.download_file(
            bucket_name,
            object_name,
            local_path,
            Callback=ProgressPercentage(s3_client, bucket_name, object_name),
        )

        print()


if __name__ == "__main__":

    import argparse

    parser = argparse.ArgumentParser()

    parser.add_argument(
        "--bucket",
        type=str,
        required=True,
        help="the bucket name to download from",
    )

    parser.add_argument(
        "--local",
        type=str,
        required=True,
        help="the target folder to download to",
    )

    args = parser.parse_args()

    download_bucket(
        args.bucket,
        args.local,
    )
