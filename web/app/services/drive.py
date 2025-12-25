import os
import io
from googleapiclient.http import MediaIoBaseDownload
from app.services.drive_service import get_drive_service 
from app.services.drive_uploader import upload_to_drive

def get_profile_image_bytes(folder_id):
    if not folder_id:
        return None
        
    service = get_drive_service()
    query = f"'{folder_id}' in parents and name = 'profile.jpg' and trashed = false"
    results = service.files().list(q=query, fields="files(id, name)").execute()
    
    if results["files"]:
        request = service.files().get_media(fileId=results["files"][0]["id"])
        fh = io.BytesIO()
        downloader = MediaIoBaseDownload(fh, request)
        done = False
        while not done:
            status, done = downloader.next_chunk()
        fh.seek(0)
        return fh.read()
    return None