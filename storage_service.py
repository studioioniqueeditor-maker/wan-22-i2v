import os
from google.cloud import storage

class StorageService:
    def __init__(self):
        self.bucket_name = os.getenv("GCS_BUCKET_NAME")
        if not self.bucket_name:
            raise ValueError("GCS_BUCKET_NAME environment variable is required.")
        
        # Get credentials path from env or use default location
        credentials_path = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")
        
        # For Cloud Run, credentials_path might not be set but default credentials work
        # For local/Docker, we need to find gcs-key.json
        if not credentials_path:
            # Try multiple fallback locations
            possible_paths = [
                os.path.join(os.getcwd(), "gcs-key.json"),  # Current working directory
                os.path.join(os.path.dirname(os.path.abspath(__file__)), "gcs-key.json"),  # Same dir as this file
                "/app/gcs-key.json",  # Docker container path
            ]
            for path in possible_paths:
                if os.path.exists(path):
                    credentials_path = path
                    break
        
        # Initialize the client
        try:
            if credentials_path and os.path.exists(credentials_path):
                # Use explicit service account credentials (local/Docker)
                from google.oauth2 import service_account
                credentials = service_account.Credentials.from_service_account_file(credentials_path)
                self.client = storage.Client(credentials=credentials, project=credentials.project_id)
            else:
                # Use default credentials (Cloud Run with Workload Identity)
                self.client = storage.Client()
        except Exception as e:
            raise ValueError(f"Failed to initialize GCS client: {e}")
        
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

    def download_blob_to_stream(self, blob_name, destination_stream):
        """Downloads a blob to a file-like object."""
        blob = self.bucket.blob(blob_name)
        if not blob.exists():
            return False
        blob.download_to_file(destination_stream)
        destination_stream.seek(0)
        return True
