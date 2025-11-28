from googleapiclient.http import MediaIoBaseDownload
from drive_service import get_drive_service
import io

def download_image(file_id, save_path):
    print(f"Downloading fileID = {file_id}")

    service = get_drive_service()
    request = service.files().get_media(fileId=file_id)

    fh = io.FileIO(save_path, "wb")
    downloader = MediaIoBaseDownload(fh, request)

    done = False
    while not done:
        status, done = downloader.next_chunk()

    return save_path

