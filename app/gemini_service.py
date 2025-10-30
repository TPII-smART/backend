"""Gemini API service."""
from google import genai
from google.genai import types
from typing import Tuple, Literal
from app.config import settings


class GeminiService:
    """Service for interacting with Google Gemini API."""
    
    def __init__(self):
        """Initialize Gemini client."""
        self.client = genai.Client(api_key=settings.GEMINI_API_KEY)
        self.model_id = "gemini-2.0-flash-exp"
    
    def generate_response(self, hash_value: str, expected_value: str) -> Tuple[Literal['TRUSTED', 'UNTRUSTED', 'UNKNOWN'], str]:
        """
        Generate response from Gemini API with custom prompt.
        
        Args:
            hash_value: Hash identifier from request
            expected_value: Expected value from request
            
        Returns:
            Tuple of (badge, details) where badge is one of 'TRUSTED', 'UNTRUSTED', 'UNKNOWN'
            and details is the analysis text from Gemini
        """
        # Custom prompt that can be edited later
        # TODO: This prompt should be customized based on requirements
        prompt = f"""
You are a security analysis AI assistant. 

Given the following information:
- Hash: {hash_value}
- Expected: {expected_value}

Analyze the data and determine if it should be classified as TRUSTED, UNTRUSTED, or UNKNOWN.
Provide your classification and detailed reasoning.

Format your response as:
CLASSIFICATION: [TRUSTED/UNTRUSTED/UNKNOWN]
DETAILS: [Your detailed analysis]
"""
        
        try:
            response = self.client.models.generate_content(
                model=self.model_id,
                contents=prompt
            )
            
            # Extract text from response
            if response.text:
                response_text = response.text
                
                # Parse the response to extract badge and details
                badge: Literal['TRUSTED', 'UNTRUSTED', 'UNKNOWN'] = 'UNKNOWN'
                details = response_text
                
                # Try to extract structured response
                if 'CLASSIFICATION:' in response_text and 'DETAILS:' in response_text:
                    parts = response_text.split('DETAILS:', 1)
                    classification_part = parts[0]
                    details = parts[1].strip() if len(parts) > 1 else response_text
                    
                    if 'TRUSTED' in classification_part.upper():
                        badge = 'TRUSTED'
                    elif 'UNTRUSTED' in classification_part.upper():
                        badge = 'UNTRUSTED'
                    else:
                        badge = 'UNKNOWN'
                else:
                    # If response doesn't follow format, try to detect keywords
                    response_upper = response_text.upper()
                    if 'TRUSTED' in response_upper and 'UNTRUSTED' not in response_upper:
                        badge = 'TRUSTED'
                    elif 'UNTRUSTED' in response_upper:
                        badge = 'UNTRUSTED'
                    else:
                        badge = 'UNKNOWN'
                
                return badge, details
            else:
                return 'UNKNOWN', "No response generated from Gemini API"
                
        except Exception as e:
            raise Exception(f"Gemini API error: {str(e)}")


# Global Gemini service instance
gemini_service = GeminiService()
