import os
from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build

SCOPES = ['https://www.googleapis.com/auth/drive', 'https://www.googleapis.com/auth/documents']

def get_gdocs_service():
    creds_path = os.environ.get('GOOGLE_APPLICATION_CREDENTIALS', 'credentials.json')
    if not os.path.exists(creds_path):
        raise FileNotFoundError(f"Google credentials not found at {creds_path}")
    
    creds = Credentials.from_service_account_file(creds_path, scopes=SCOPES)
    drive_service = build('drive', 'v3', credentials=creds)
    docs_service = build('docs', 'v1', credentials=creds)
    return drive_service, docs_service

def upload_to_gdocs(title, content):
    drive_service, docs_service = get_gdocs_service()
    
    # Create a new document
    doc_metadata = {'name': title, 'mimeType': 'application/vnd.google-apps.document'}
    doc = drive_service.files().create(body=doc_metadata, fields='id').execute()
    doc_id = doc.get('id')
    
    # Insert content
    requests = [
        {
            'insertText': {
                'location': {
                    'index': 1,
                },
                'text': content
            }
        }
    ]
    docs_service.documents().batchUpdate(documentId=doc_id, body={'requests': requests}).execute()
    
    # Make it accessible to anyone with the link
    permission = {
        'type': 'anyone',
        'role': 'reader'
    }
    drive_service.permissions().create(fileId=doc_id, body=permission).execute()
    
    return f"https://docs.google.com/document/d/{doc_id}/edit"
