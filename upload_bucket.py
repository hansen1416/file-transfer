import os
import sys
import threading
import logging
import pathlib
from typing import List

import boto3
from botocore.exceptions import ClientError
from boto3.s3.transfer import TransferConfig


class ProgressPercentage(object):

    def __init__(self, filename):
        self._filename = filename
        self._size = float(os.path.getsize(filename))
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


def check_object_exists(s3_client, bucket_name, object_key):
    try:
        response = s3_client.head_object(Bucket=bucket_name, Key=object_key)

        # return the file size
        return int(response["ContentLength"])
    except ClientError:
        return 0


def upload_file(file_name, bucket, object_name=None, s3_client=None, config=None):
    """Upload a file to an S3 bucket

    :param file_name: File to upload
    :param bucket: Bucket to upload to
    :param object_name: S3 object name. If not specified then file_name is used
    :return: True if file was uploaded, else False
    """
    # Upload the file

    if s3_client is None:
        s3_client = boto3.client("s3")

    if config is None:
        config = TransferConfig(
            multipart_threshold=1 * 1024**3,
            max_concurrency=4,
            multipart_chunksize=10 * 1024**2,
            use_threads=True,
        )

    cloud_size = check_object_exists(s3_client, bucket, object_name)
    local_size = os.path.getsize(file_name)

    if cloud_size == local_size:
        print(f"{object_name} already exists in s3")
        return

    # If S3 object_name was not specified, use file_name
    if object_name is None:
        object_name = os.path.basename(file_name)

    try:
        s3_client.upload_file(
            file_name,
            bucket,
            object_name,
            ExtraArgs={"StorageClass": "INTELLIGENT_TIERING"},
            Callback=ProgressPercentage(file_name),
            Config=config,
        )

    except ClientError as e:
        logging.error(e)
        return False
    return True


def upload_folder(local_folder, bucket):

    local_path = os.path.abspath(local_folder)

    if not os.path.exists(local_path):
        print(f"{local_path} does not exist")
        sys.exit(1)

    # get all files in the folder recursively
    all_files: List[str] = [
        str(f) for f in pathlib.Path(local_path).rglob("*") if f.is_file()
    ]

    path_delimiter = os.path.sep
    all_s3_path = []

    for filepath in all_files:
        # remove the prefix `folder_path` from the file path
        sub_path = filepath[len(local_path) + 1 :]

        all_s3_path.append("/".join(sub_path.split(path_delimiter)))

    s3_client = boto3.client("s3")

    config = TransferConfig(
        multipart_threshold=1 * 1024**3,
        max_concurrency=4,
        multipart_chunksize=10 * 1024**2,
        use_threads=True,
    )

    # upload all files
    for i, filepath in enumerate(all_files):

        s3_path = all_s3_path[i]

        upload_file(
            filepath,
            bucket,
            object_name=s3_path,
            s3_client=s3_client,
            config=config,
        )


if __name__ == "__main__":

    import argparse

    parser = argparse.ArgumentParser()

    parser.add_argument(
        "--bucket",
        type=str,
        required=True,
        help="the bucket name to upload to",
    )

    parser.add_argument(
        "--local",
        type=str,
        required=True,
        help="the local folder to upload from",
    )

    args = parser.parse_args()

    upload_folder(args.local, args.bucket)
