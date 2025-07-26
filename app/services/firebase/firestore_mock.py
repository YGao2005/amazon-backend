"""
Mock Firebase service for testing purposes
This allows the API to run without Firebase dependencies
"""
from typing import Dict, Any, List, Optional

class MockFirebaseService:
    def __init__(self):
        # In-memory storage for testing
        self.data = {}
    
    async def create_document(self, collection: str, document_id: str, data: Dict[str, Any]) -> bool:
        """Create a new document in mock storage"""
        try:
            if collection not in self.data:
                self.data[collection] = {}
            self.data[collection][document_id] = data
            return True
        except Exception as e:
            print(f"Error creating document: {e}")
            return False
    
    async def get_document(self, collection: str, document_id: str) -> Optional[Dict[str, Any]]:
        """Get a document from mock storage"""
        try:
            if collection in self.data and document_id in self.data[collection]:
                return self.data[collection][document_id]
            return None
        except Exception as e:
            print(f"Error getting document: {e}")
            return None
    
    async def update_document(self, collection: str, document_id: str, data: Dict[str, Any]) -> bool:
        """Update a document in mock storage"""
        try:
            if collection not in self.data:
                self.data[collection] = {}
            if document_id not in self.data[collection]:
                self.data[collection][document_id] = {}
            self.data[collection][document_id].update(data)
            return True
        except Exception as e:
            print(f"Error updating document: {e}")
            return False
    
    async def delete_document(self, collection: str, document_id: str) -> bool:
        """Delete a document from mock storage"""
        try:
            if collection in self.data and document_id in self.data[collection]:
                del self.data[collection][document_id]
            return True
        except Exception as e:
            print(f"Error deleting document: {e}")
            return False
    
    async def get_collection(self, collection: str, limit: Optional[int] = None) -> List[Dict[str, Any]]:
        """Get all documents from a collection"""
        try:
            if collection not in self.data:
                return []
            
            docs = [{"id": doc_id, **doc_data} for doc_id, doc_data in self.data[collection].items()]
            
            if limit:
                docs = docs[:limit]
            
            return docs
        except Exception as e:
            print(f"Error getting collection: {e}")
            return []

# Create a singleton instance
firebase_service = MockFirebaseService()