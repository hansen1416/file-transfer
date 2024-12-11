import os.path

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

# If modifying these scopes, delete the file token.json.
SCOPES = ["https://www.googleapis.com/auth/drive.metadata.readonly"]


def authenticate_drive_api():
    """Shows basic usage of the Drive v3 API.
    Prints the names and ids of the first 10 files the user has access to.
    """
    creds = None
    # The file token.json stores the user's access and refresh tokens, and is
    # created automatically when the authorization flow completes for the first
    # time.
    if os.path.exists("token.json"):
        creds = Credentials.from_authorized_user_file("token.json", SCOPES)
    # If there are no (valid) credentials available, let the user log in.
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file("credentials.json", SCOPES)
            creds = flow.run_local_server(port=0)
        # Save the credentials for the next run
        with open("token.json", "w") as token:
            token.write(creds.to_json())

    return build("drive", "v3", credentials=creds)


# Function to list files recursively with their paths
def list_files(service, folder_id, current_path="", file_list=[]):
    query = f"'{folder_id}' in parents"
    results = (
        service.files()
        .list(q=query, pageSize=1000, fields="nextPageToken, files(id, name, mimeType)")
        .execute()
    )
    items = results.get("files", [])

    for item in items:
        # Construct the full path
        full_path = f"{current_path}/{item['name']}" if current_path else item["name"]
        # print(f"Found file: {full_path} (ID: {item['id']})")

        if item["mimeType"] == "application/vnd.google-apps.folder":
            # If the item is a folder, call the function recursively with the updated path
            list_files(service, item["id"], full_path, file_list)
        else:
            if item["mimeType"] == "application/vnd.google-apps.shortcut":
                pass
            else:
                file_list.append(
                    {"name": item["name"], "id": item["id"], "path": full_path}
                )


if __name__ == "__main__":
    # Authenticate and create the Drive API service
    service = authenticate_drive_api()

    # Replace 'YOUR_FOLDER_ID' with the ID of the folder you want to list
    # motion-x id
    folder_id = "1jn51yiS0Savdsw6M67kkv2lXNOITNKfU"
    # motion-x++ id
    folder_id = "1Tquahp2HWBP_R2tNi5cxsVJ3oEJ8F0Xx"

    file_list = []

    list_files(service, folder_id, file_list=file_list)

    print("List of files:", file_list)
