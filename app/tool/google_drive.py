import asyncio
from typing import List, Dict, Any
from app.tool.base import BaseTool

# Google Drive API imports
from googleapiclient.discovery import build
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
import os

# Notion API imports
import requests

# Tool for Google Drive
class GoogleDriveTool(BaseTool):
    name: str = "google_drive_tool"
    description: str = """Interact with Google Drive API to manage files and folders.
    Use this tool to list files, upload, download, and search files in Google Drive.
    Requires authentication and proper credentials setup."""
    parameters: dict = {
        "type": "object",
        "properties": {
            "action": {
                "type": "string",
                "description": "(required) The action to perform (e.g., 'list_files', 'search_files').",
            },
            "query": {
                "type": "string",
                "description": "(optional) The search query for files (e.g., 'filename.pdf', 'important document').",
            },
            "file_id": {
                "type": "string",
                "description": "(optional) The ID of the file to download or manage.",
            },
            "scopes": {
                "type": "array",
                "items": {"type": "string"},
                "description": "(optional) List of scopes needed for the action. Defaults to read-only access.",
                "default": ["https://www.googleapis.com/auth/drive.metadata.readonly"],
            },
        },
        "required": ["action"],
    }

    async def execute(self, action: str, query: str = None, file_id: str = None, scopes: List[str] = None) -> Dict[str, Any]:
        """
        Execute a Google Drive API call and return the response.
        """
        try:
            # Run the API call in a thread pool to prevent blocking
            loop = asyncio.get_event_loop()
            response = await loop.run_in_executor(
                None,
                lambda: self._fetch_google_drive_data(action, query, file_id, scopes),
            )
            return response
        except Exception as e:
            return {"error": str(e)}

    def _fetch_google_drive_data(self, action: str, query: str = None, file_id: str = None, scopes: List[str] = None) -> Dict[str, Any]:
        """
        Helper function to fetch data from the Google Drive API synchronously.
        """
        creds = None
        # The file token.json stores the user's access and refresh tokens, and is
        # created automatically when the authorization flow completes for the first
        # time.
        if os.path.exists('token.json'):
            creds = Credentials.from_authorized_user_file('token.json', scopes)
        # If there are no (valid) credentials available, let the user log in.
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                try:
                    creds.refresh(Request())
                except Exception as e:
                    print(f"Error refreshing credentials: {e}")
                    return {"error": "Could not refresh credentials. Please re-authenticate."}
            else:
                flow = InstalledAppFlow.from_client_secrets_file(
                    'credentials.json', scopes)
                creds = flow.run_local_server(port=0)
            # Save the credentials for the next run
            with open('token.json', 'w') as token:
                token.write(creds.to_json())

        try:
            service = build('drive', 'v3', credentials=creds)

            if action == "list_files":
                results = service.files().list(pageSize=10, fields="nextPageToken, files(id, name)").execute()
                items = results.get('files', [])
                return {"files": items}
            elif action == "search_files":
                if not query:
                    return {"error": "Search query is required."}
                results = service.files().list(q=f"name contains '{query}'", fields="nextPageToken, files(id, name)").execute()
                items = results.get('files', [])
                return {"files": items}
            elif action == "download_file":
                if not file_id:
                    return {"error": "File ID is required for downloading."}
                results = service.files().get_media(fileId=file_id).execute()
                return {"file_content": results}  # This will return raw content; handling depends on use case
            else:
                return {"error": f"Unsupported action: {action}"}
        except Exception as e:
            return {"error": str(e)}

