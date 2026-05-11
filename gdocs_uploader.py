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

def upload_to_gdocs(title, content=None, sections=None):
    drive_service, docs_service = get_gdocs_service()
    
    doc_id = os.environ.get("DOCUMENT_ID")
    if not doc_id:
        raise ValueError("DOCUMENT_ID environment variable is missing!")
        
    full_text = ""
    header_ranges = []
    
    # We insert at index 1
    current_idx = 1
    
    # Title
    title_text = f"{title}\n\n"
    full_text += title_text
    header_ranges.append((current_idx, current_idx + len(title_text), 'HEADING_1'))
    current_idx += len(title_text)
    
    if sections:
        for header, body in sections:
            header_text = f"{header}\n"
            full_text += header_text
            header_ranges.append((current_idx, current_idx + len(header_text), 'HEADING_2'))
            current_idx += len(header_text)
            
            body_text = f"{body}\n\n"
            full_text += body_text
            current_idx += len(body_text)
    elif content:
        full_text += f"{content}\n\n"
        current_idx += len(f"{content}\n\n")
        
    separator = ("-" * 40) + "\n\n"
    full_text += separator
    current_idx += len(separator)
    
    requests = [
        {
            'insertText': {
                'location': {'index': 1},
                'text': full_text
            }
        }
    ]
    
    for start, end, style in header_ranges:
        requests.append({
            'updateParagraphStyle': {
                'range': {
                    'startIndex': start,
                    'endIndex': end
                },
                'paragraphStyle': {
                    'namedStyleType': style
                },
                'fields': 'namedStyleType'
            }
        })
    
    docs_service.documents().batchUpdate(
        documentId=doc_id, 
        body={'requests': requests}
    ).execute()
    
    return f"https://docs.google.com/document/d/{doc_id}/edit"
