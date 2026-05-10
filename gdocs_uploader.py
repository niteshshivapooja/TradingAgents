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
        
    # 1. Create a new Tab
    create_tab_req = {
        'createTab': {
            'tabProperties': {
                'title': title
            }
        }
    }
    
    response = docs_service.documents().batchUpdate(
        documentId=doc_id, 
        body={'requests': [create_tab_req]}
    ).execute()
    
    # Extract the new Tab ID
    new_tab_id = response['replies'][0]['createTab']['tabId']
    
    # 2. Insert content into the new Tab
    insert_text_req = {
        'insertText': {
            'location': {
                'index': 1,
                'tabId': new_tab_id
            },
            'text': content
        }
    }
    
    docs_service.documents().batchUpdate(
        documentId=doc_id, 
        body={'requests': [insert_text_req]}
    ).execute()
    
    return f"https://docs.google.com/document/d/{doc_id}/edit#tab={new_tab_id}"
