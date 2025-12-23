import os
from google.cloud import storage

class StorageService:
    def __init__(self):
        self.bucket_name = os.getenv("GCS_BUCKET_NAME")
        if not self.bucket_name:
            raise ValueError("GCS_BUCKET_NAME environment variable is required.")
        
        # Initialize the client (it will pick up credentials from env automatically)
        self.client = storage.Client()
        self.bucket = self.client.bucket(self.bucket_name)

    def upload_file(self, source_file_name, destination_blob_name):
        """Uploads a file to the bucket."""
        blob = self.bucket.blob(destination_blob_name)
        
        blob.upload_from_filename(source_file_name)
        
        # For this prototype, we'll assume the bucket is public or we return the public URL.
        # If the bucket is not public, we might need to generate a signed URL.
        # But `blob.public_url` is a standard property.
        return blob.public_url
