import firebase_admin
from firebase_admin import credentials, firestore, storage
from typing import Dict, Any, List, Optional
import json

from app.core.config import settings

class FirebaseService:
    def __init__(self):
        self.db = None
        self.bucket = None
        self._initialize_firebase()
    
    def _initialize_firebase(self):
        """Initialize Firebase app with credentials"""
        try:
            # Check if Firebase app is already initialized
            firebase_admin.get_app()
        except ValueError:
            # Initialize Firebase app
            cred_dict = settings.firebase_credentials
            cred = credentials.Certificate(cred_dict)
            firebase_admin.initialize_app(cred, {
                'storageBucket': f"{settings.FIREBASE_PROJECT_ID}.appspot.com"
            })
        
        # Initialize Firestore and Storage
        self.db = firestore.client()
        self.bucket = storage.bucket()
    
    # Firestore operations
    async def create_document(self, collection: str, document_id: str, data: Dict[str, Any]) -> bool:
        """Create a new document in Firestore"""
        try:
            doc_ref = self.db.collection(collection).document(document_id)
            doc_ref.set(data)
            return True
        except Exception as e:
            print(f"Error creating document: {e}")
            return False
    
    async def get_document(self, collection: str, document_id: str) -> Optional[Dict[str, Any]]:
        """Get a document from Firestore"""
        try:
            doc_ref = self.db.collection(collection).document(document_id)
            doc = doc_ref.get()
            if doc.exists:
                return doc.to_dict()
            return None
        except Exception as e:
            print(f"Error getting document: {e}")
            return None
    
    async def update_document(self, collection: str, document_id: str, data: Dict[str, Any]) -> bool:
        """Update a document in Firestore"""
        try:
            doc_ref = self.db.collection(collection).document(document_id)
            doc_ref.update(data)
            return True
        except Exception as e:
            print(f"Error updating document: {e}")
            return False
    
    async def delete_document(self, collection: str, document_id: str) -> bool:
        """Delete a document from Firestore"""
        try:
            doc_ref = self.db.collection(collection).document(document_id)
            doc_ref.delete()
            return True
        except Exception as e:
            print(f"Error deleting document: {e}")
            return False
    
    async def get_collection(self, collection: str, limit: Optional[int] = None) -> List[Dict[str, Any]]:
        """Get all documents from a collection"""
        try:
            query = self.db.collection(collection)
            if limit:
                query = query.limit(limit)
            
            docs = query.stream()
            return [{"id": doc.id, **doc.to_dict()} for doc in docs]
        except Exception as e:
            print(f"Error getting collection: {e}")
            return []
    
    async def query_collection(self, collection: str, field: str, operator: str, value: Any) -> List[Dict[str, Any]]:
        """Query a collection with filters"""
        try:
            query = self.db.collection(collection).where(field, operator, value)
            docs = query.stream()
            return [{"id": doc.id, **doc.to_dict()} for doc in docs]
        except Exception as e:
            print(f"Error querying collection: {e}")
            return []
    
    # Storage operations
    async def upload_image(self, file_path: str, blob_name: str) -> Optional[str]:
        """Upload an image to Firebase Storage"""
        try:
            blob = self.bucket.blob(blob_name)
            blob.upload_from_filename(file_path)
            blob.make_public()
            return blob.public_url
        except Exception as e:
            print(f"Error uploading image: {e}")
            return None
    
    async def delete_image(self, blob_name: str) -> bool:
        """Delete an image from Firebase Storage"""
        try:
            blob = self.bucket.blob(blob_name)
            blob.delete()
            return True
        except Exception as e:
            print(f"Error deleting image: {e}")
            return False

# Create a singleton instance
firebase_service = FirebaseService()