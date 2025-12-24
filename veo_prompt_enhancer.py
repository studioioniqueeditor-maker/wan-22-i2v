from google import genai
from google.genai import types
import os

class VeoPromptEnhancer:
    def __init__(self, project_id="gen-lang-client-0268770038", location="us-central1"):
        self.project_id = project_id
        self.location = location
        self.client = None

    def _get_client(self):
        if not self.client:
            pid = self.project_id or os.environ.get("GOOGLE_CLOUD_PROJECT")
            if not pid:
                raise ValueError("Project ID must be provided or set in GOOGLE_CLOUD_PROJECT environment variable.")
            self.client = genai.Client(vertexai=True, project=pid, location=self.location)
        return self.client

    def enhance(self, prompt, image_bytes=None, keywords=None):
        client = self._get_client()
        
        gemini_system_instruction = (
            "You are an expert prompt engineer for Google's Veo model. "
            "Analyze the provided image (if any) and user prompt to generate a single, cohesive, "
            "and cinematic prompt. Integrate requested motion and audio effects. "
            "Output ONLY the final prompt text."
        )

        formatted_keywords = ", ".join(keywords) if keywords else ""
        gemini_user_query = f"Mandatory Keywords: {formatted_keywords}. User Prompt: {prompt}"

        contents = []
        if image_bytes:
            contents.append(types.Part.from_bytes(data=image_bytes, mime_type="image/png"))
        
        contents.append(gemini_user_query)

        try:
            # Using gemini-1.5-flash as a standard available model
            gemini_model = "gemini-2.5-flash" 
            
            gemini_response = client.models.generate_content(
                model=gemini_model,
                contents=contents,
                config=types.GenerateContentConfig(system_instruction=gemini_system_instruction)
            )
            return gemini_response.text
        except Exception as e:
            print(f"Veo Prompt Enhancement failed: {e}")
            # Fallback to simple concatenation if enhancement fails
            if formatted_keywords:
                return f"{prompt}. Cinematic style. Keywords: {formatted_keywords}."
            return prompt