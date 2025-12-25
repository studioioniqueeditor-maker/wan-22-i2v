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
        """Uploads a file to the bucket and returns a URL (signed if possible, else public)."""
        blob = self.bucket.blob(destination_blob_name)
        
        blob.upload_from_filename(source_file_name)
        
        # Try to generate a signed URL
        try:
            import datetime
            url = blob.generate_signed_url(
                version="v4",
                expiration=datetime.timedelta(minutes=60),
                method="GET"
            )
            return url
        except Exception as e:
            print(f"Warning: Could not generate signed URL ({e}). Returning public URL.")
            # Fallback to public URL structure
            return f"https://storage.googleapis.com/{self.bucket_name}/{destination_blob_name}"

    def upload_file_get_uri(self, source_file_name, destination_blob_name):
        """Uploads a file to the bucket and returns the gs:// URI."""
        blob = self.bucket.blob(destination_blob_name)
        blob.upload_from_filename(source_file_name)
        return f"gs://{self.bucket_name}/{destination_blob_name}"
