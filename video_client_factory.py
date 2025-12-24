from generate_video_client import WanVideoClient
from vertex_ai_veo_client import VertexAIVeoClient
import os

class VideoClientFactory:
    @staticmethod
    def get_client(model_name, **kwargs):
        if model_name == "wan2.1":
            return WanVideoClient(
                runpod_endpoint_id=kwargs.get("runpod_endpoint_id"),
                runpod_api_key=kwargs.get("runpod_api_key")
            )
        elif model_name == "veo3.1":
            project_id = "gen-lang-client-0268770038"
            location = os.getenv("GOOGLE_CLOUD_LOCATION", "us-central1")
            return VertexAIVeoClient(project_id, location)
        else:
            raise ValueError(f"Unknown model: {model_name}")
