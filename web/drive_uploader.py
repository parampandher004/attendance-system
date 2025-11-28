from googleapiclient.discovery import build
from google.oauth2 import service_account
from googleapiclient.http import MediaFileUpload
from drive_service import get_drive_service

import io

def upload_to_drive(local_path, file_name, PARENT_FOLDER_ID=None):

    service = get_drive_service()

    file_metadata = {
        "name": file_name,
        "parents": [PARENT_FOLDER_ID]
    }
    media = MediaFileUpload(local_path, resumable=True)


    uploaded_file = service.files().create(
        body=file_metadata,
        media_body=media,
        fields="id"
    ).execute()

    return uploaded_file.get("id")