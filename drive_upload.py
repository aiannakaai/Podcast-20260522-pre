import os

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload

from config import DRIVE_FOLDER_NAME, OAUTH_SCOPE


def _get_drive_service():
    creds = Credentials(
        token=None,
        refresh_token=os.environ["GOOGLE_REFRESH_TOKEN"],
        token_uri="https://oauth2.googleapis.com/token",
        client_id=os.environ["GOOGLE_CLIENT_ID"],
        client_secret=os.environ["GOOGLE_CLIENT_SECRET"],
        scopes=[OAUTH_SCOPE],
    )
    creds.refresh(Request())
    return build("drive", "v3", credentials=creds)


def _get_or_create_folder(service, name: str, parent_id: str = None) -> str:
    """フォルダを取得、なければ作成して ID を返す"""
    query = f"name='{name}' and mimeType='application/vnd.google-apps.folder' and trashed=false"
    if parent_id:
        query += f" and '{parent_id}' in parents"

    results = service.files().list(q=query, fields="files(id, name)").execute()
    files = results.get("files", [])
    if files:
        return files[0]["id"]

    metadata = {"name": name, "mimeType": "application/vnd.google-apps.folder"}
    if parent_id:
        metadata["parents"] = [parent_id]

    folder = service.files().create(body=metadata, fields="id").execute()
    return folder["id"]


def upload_podcast(mp3_path: str, version: str, date_str: str) -> str:
    """MP3 を Google Drive の Podcasts/{version}_{date} フォルダにアップロード"""
    print("Google Drive に認証中...")
    service = _get_drive_service()

    print(f"フォルダ '{DRIVE_FOLDER_NAME}' を確認中...")
    podcasts_folder_id = _get_or_create_folder(service, DRIVE_FOLDER_NAME)

    subfolder_name = f"{version}_{date_str}"
    print(f"サブフォルダ '{subfolder_name}' を確認中...")
    subfolder_id = _get_or_create_folder(service, subfolder_name, podcasts_folder_id)

    print(f"MP3 をアップロード中: {mp3_path}")
    file_metadata = {"name": "podcast.mp3", "parents": [subfolder_id]}
    media = MediaFileUpload(mp3_path, mimetype="audio/mpeg")
    uploaded = service.files().create(
        body=file_metadata,
        media_body=media,
        fields="id, webViewLink",
    ).execute()

    link = uploaded.get("webViewLink", "")
    print(f"アップロード完了: {link}")
    return link
