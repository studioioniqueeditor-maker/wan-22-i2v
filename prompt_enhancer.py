import os
from groq import Groq

class PromptEnhancer:
    def __init__(self, api_key=None, model="llama-3.3-70b-versatile"):
        self.api_key = api_key or os.getenv("GROQ_API_KEY")
        if not self.api_key:
            raise ValueError("GROQ_API_KEY must be provided or set as an environment variable.")
        
        self.client = Groq(api_key=self.api_key)
        self.model = model

    def enhance(self, original_prompt):
        """
        Enhances a short user prompt into a detailed cinematic description.
        """
        system_prompt = (
            "You are a cinematic prompt engineer. Your goal is to transform short, simple descriptions "
            "into rich, detailed, and visually evocative prompts for an Image-to-Video AI model. "
            "Focus on lighting, textures, camera movement, and atmosphere. Keep the result under 100 words. "
            "Respond ONLY with the enhanced prompt text."
        )

        try:
            completion = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": f"Enhance this prompt: {original_prompt}"}
                ],
                temperature=0.7,
                max_tokens=150,
            )
            return completion.choices[0].message.content.strip()
        except Exception as e:
            # Re-raise to be handled by the caller or test
            raise e
