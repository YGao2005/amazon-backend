import os
import uuid
import logging
from typing import Optional
import firebase_admin
from firebase_admin import storage
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

class FirebaseStorageService:
    def __init__(self):
        self.bucket_name = os.getenv("FIREBASE_STORAGE_BUCKET")
        self.bucket = None
        
        try:
            # Get the default bucket or use the specified bucket name
            if self.bucket_name:
                self.bucket = storage.bucket(self.bucket_name)
            else:
                self.bucket = storage.bucket()
            logger.info("Firebase Storage initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize Firebase Storage: {e}")

    async def upload_image(self, image_data: bytes, folder: str = "recipe_images", 
                          filename: str = None) -> Optional[str]:
        """
        Upload an image to Firebase Storage.
        
        Args:
            image_data: Raw image bytes
            folder: Storage folder path
            filename: Optional custom filename (will generate UUID if not provided)
            
        Returns:
            Public URL of the uploaded image or None if failed
        """
        if not self.bucket:
            logger.error("Firebase Storage not initialized")
            return None

        try:
            # Generate filename if not provided
            if not filename:
                filename = f"{uuid.uuid4()}.jpg"
            
            # Create the full path
            blob_path = f"{folder}/{filename}"
            
            # Create blob and upload
            blob = self.bucket.blob(blob_path)
            blob.upload_from_string(
                image_data,
                content_type='image/jpeg'
            )
            
            # Make the blob publicly accessible
            blob.make_public()
            
            # Return the public URL
            return blob.public_url
            
        except Exception as e:
            logger.error(f"Failed to upload image to Firebase Storage: {e}")
            return None

    async def upload_recipe_image(self, image_data: bytes, recipe_id: str) -> Optional[str]:
        """
        Upload a recipe image with a specific naming convention.
        
        Args:
            image_data: Raw image bytes
            recipe_id: ID of the recipe
            
        Returns:
            Public URL of the uploaded image or None if failed
        """
        filename = f"recipe_{recipe_id}_{uuid.uuid4().hex[:8]}.jpg"
        return await self.upload_image(image_data, "recipe_images", filename)

    async def upload_ingredient_scan_image(self, image_data: bytes, user_id: str) -> Optional[str]:
        """
        Upload an ingredient scan image.
        
        Args:
            image_data: Raw image bytes
            user_id: ID of the user
            
        Returns:
            Public URL of the uploaded image or None if failed
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"scan_{user_id}_{timestamp}_{uuid.uuid4().hex[:8]}.jpg"
        return await self.upload_image(image_data, "ingredient_scans", filename)

    async def delete_image(self, image_url: str) -> bool:
        """
        Delete an image from Firebase Storage using its public URL.
        
        Args:
            image_url: Public URL of the image to delete
            
        Returns:
            True if successful, False otherwise
        """
        if not self.bucket:
            logger.error("Firebase Storage not initialized")
            return False

        try:
            # Extract the blob path from the URL
            # Firebase Storage URLs have format: https://storage.googleapis.com/bucket-name/path/to/file
            if "storage.googleapis.com" in image_url:
                # Extract path after bucket name
                parts = image_url.split(f"{self.bucket.name}/")
                if len(parts) > 1:
                    blob_path = parts[1].split("?")[0]  # Remove query parameters
                    
                    # Delete the blob
                    blob = self.bucket.blob(blob_path)
                    blob.delete()
                    
                    logger.info(f"Successfully deleted image: {blob_path}")
                    return True
            
            logger.error(f"Invalid Firebase Storage URL format: {image_url}")
            return False
            
        except Exception as e:
            logger.error(f"Failed to delete image from Firebase Storage: {e}")
            return False

    async def get_signed_url(self, blob_path: str, expiration_hours: int = 24) -> Optional[str]:
        """
        Generate a signed URL for private access to a blob.
        
        Args:
            blob_path: Path to the blob in storage
            expiration_hours: Hours until the URL expires
            
        Returns:
            Signed URL or None if failed
        """
        if not self.bucket:
            logger.error("Firebase Storage not initialized")
            return None

        try:
            blob = self.bucket.blob(blob_path)
            
            # Generate signed URL
            expiration = datetime.utcnow() + timedelta(hours=expiration_hours)
            signed_url = blob.generate_signed_url(expiration=expiration)
            
            return signed_url
            
        except Exception as e:
            logger.error(f"Failed to generate signed URL: {e}")
            return None

    def get_bucket_info(self) -> dict:
        """Get information about the storage bucket."""
        if not self.bucket:
            return {"error": "Firebase Storage not initialized"}
        
        return {
            "bucket_name": self.bucket.name,
            "initialized": True
        }

# Create singleton instance
firebase_storage_service = FirebaseStorageService()