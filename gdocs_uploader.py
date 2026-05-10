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
    
    doc_id = os.environ.get("DOCUMENT_ID")
    if not doc_id:
        raise ValueError("DOCUMENT_ID environment variable is missing!")
        
    formatted_content = f"{title}\n{'='*len(title)}\n{content}\n\n" + ("-" * 40) + "\n\n"
    
    insert_text_req = {
        'insertText': {
            'location': {
                'index': 1
            },
            'text': formatted_content
        }
    }
    
    docs_service.documents().batchUpdate(
        documentId=doc_id, 
        body={'requests': [insert_text_req]}
    ).execute()
    
    return f"https://docs.google.com/document/d/{doc_id}/edit"
