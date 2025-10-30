"""Gemini API service."""
from google import genai
from google.genai import types
from app.config import settings


class GeminiService:
    """Service for interacting with Google Gemini API."""
    
    def __init__(self):
        """Initialize Gemini client."""
        self.client = genai.Client(api_key=settings.GEMINI_API_KEY)
        self.model_id = "gemini-2.0-flash-exp"
    
    def generate_response(self, hash_value: str, expected_value: str) -> str:
        """
        Generate response from Gemini API with custom prompt.
        
        Args:
            hash_value: Hash identifier from request
            expected_value: Expected value from request
            
        Returns:
            Generated response text from Gemini
        """
        # Custom prompt that can be edited later
        # TODO: This prompt should be customized based on requirements
        prompt = f"""
You are a helpful AI assistant. 

Given the following information:
- Hash: {hash_value}
- Expected: {expected_value}

Please analyze and provide a detailed response.
"""
        
        try:
            response = self.client.models.generate_content(
                model=self.model_id,
                contents=prompt
            )
            
            # Extract text from response
            if response.text:
                return response.text
            else:
                return "No response generated from Gemini API"
                
        except Exception as e:
            raise Exception(f"Gemini API error: {str(e)}")


# Global Gemini service instance
gemini_service = GeminiService()
