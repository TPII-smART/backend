"""Gemini API service."""
from google import genai
from google.genai import types
from typing import Tuple, Literal
from app.config import settings
import httpx


class GeminiService:
    """Service for interacting with Google Gemini API."""

    def __init__(self):
        """Initialize Gemini client."""
        self.client = genai.Client(api_key=settings.GEMINI_API_KEY)
        self.model_id = "gemini-2.0-flash"

    def get_prompt(self, hash: str, expected: str) -> str:
        """Generate prompt for Gemini API based on hash and expected value."""
        return f"""
    You are an art juror.

     Given the following information:
     - Hash: {hash}
     - Expected: {expected}

     Task: Decide whether the image contains the EXPECTED content.

     STRICT OUTPUT RULES (MANDATORY):
     1) Output exactly TWO lines and nothing else. Use these exact prefixes (uppercase) with a single space after the colon:
         DETAILS: <brief analysis, <=50 words>
         CLASSIFICATION: <TRUSTED|UNTRUSTED|UNKNOWN>
     2) The second line (DETAILS) must NOT include the hash or any extra lines/annotations.
     3) DETAILS must be strictly consistent with the chosen CLASSIFICATION. To ensure this, follow these allowed/forbidden phrasing rules:
         - If CLASSIFICATION is TRUSTED: DETAILS MUST assert presence. Include one of these positive phrases: "is present", "present", "clearly shows", "visible", "depicted". DETAILS MUST NOT contain negations or absence words such as "no", "not", "absent", "instead", "cannot".
         - If CLASSIFICATION is UNTRUSTED: DETAILS MUST assert absence or mismatch. Include one of these negative phrases: "no", "not present", "absent", "instead", "a different object". DETAILS MUST NOT include positive presence phrases like "is present", "clearly shows", "visible", "depicted".
         - If CLASSIFICATION is UNKNOWN: DETAILS MUST explain uncertainty with words like "cannot determine", "unclear", "too blurred", "occluded", "cropped", "ambiguous framing", or "insufficient detail". DETAILS MUST NOT claim presence or definite absence.
     4) Word limit: DETAILS must be <=50 words.
     5) If you cannot confidently follow the required format and consistency rules, return exactly:
         CLASSIFICATION: UNKNOWN
         DETAILS: Image analysis inconclusive; insufficient confidence to mark TRUSTED or UNTRUSTED.
     6) Do NOT include JSON, code, headings, extra commentary, punctuation beyond standard sentence punctuation in DETAILS, or any other text.

     Examples (must follow exactly):
     DETAILS: Clear image of a blue ceramic mug centered and unobstructed; expected 'blue ceramic mug' is present.
     CLASSIFICATION: TRUSTED

     DETAILS: No blue ceramic mug visible; instead a metal water bottle is present.
     CLASSIFICATION: UNTRUSTED

     DETAILS: Image is heavily blurred and cropped; cannot determine whether expected object is present.
     CLASSIFICATION: UNKNOWN

     Follow these rules exactly. Any deviation is unacceptable.
     """

    async def get_image(self, hash: str) -> tuple[bytes, str]:
        url = f"https://gateway.pinata.cloud/ipfs/{hash}"
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                resp = await client.get(url)
                resp.raise_for_status()
                image_bytes: bytes = resp.content
                mime_type = resp.headers.get(
                    'content-type', 'application/octet-stream')
                return image_bytes, mime_type
        except Exception as e:
            raise Exception(f"Failed to download image from {url}: {e}")

    async def generate_response(self, hash_value: str, expected_value: str) -> Tuple[Literal['TRUSTED', 'UNTRUSTED', 'UNKNOWN'], str]:
        """
        Generate response from Gemini API with custom prompt.

        Args:
            hash_value: Hash identifier from request
            expected_value: Expected value from request

        Returns:
            Tuple of (badge, details) where badge is one of 'TRUSTED', 'UNTRUSTED', 'UNKNOWN'
            and details is the analysis text from Gemini
        """

        image, mime_type = await self.get_image(hash_value)
        prompt = self.get_prompt(hash_value, expected_value)
        image_content = types.Part.from_bytes(
            data=image,
            mime_type=mime_type,
        )

        try:
            response = self.client.models.generate_content(
                model=self.model_id,
                contents=[image_content, prompt]
            )

            # Extract text from response
            if response.text:
                response_text = response.text.strip()

                # Parse the response to extract badge and details
                badge: Literal['TRUSTED', 'UNTRUSTED', 'UNKNOWN'] = 'UNKNOWN'
                details = response_text

                # Split into non-empty lines and prefer the format:
                # DETAILS: <...>  (first line)
                # CLASSIFICATION: <TRUSTED|UNTRUSTED|UNKNOWN>  (second line)
                lines = [l.strip()
                         for l in response_text.splitlines() if l.strip()]

                parsed = False
                if len(lines) >= 2 and lines[0].upper().startswith('DETAILS:') and lines[1].upper().startswith('CLASSIFICATION:'):
                    details = lines[0].split(':', 1)[1].strip()
                    classification = lines[1].split(':', 1)[1].strip().upper()
                    if 'TRUSTED' in classification and 'UNTRUSTED' not in classification:
                        badge = 'TRUSTED'
                    elif 'UNTRUSTED' in classification:
                        badge = 'UNTRUSTED'
                    else:
                        badge = 'UNKNOWN'
                    parsed = True

                if not parsed:
                    # Try to find a DETAILS line followed by a later CLASSIFICATION line
                    details_candidate = None
                    classification_candidate = None
                    for i, line in enumerate(lines):
                        up = line.upper()
                        if up.startswith('DETAILS:') and details_candidate is None:
                            details_candidate = line.split(':', 1)[1].strip()
                            # look for CLASSIFICATION in subsequent lines
                            for j in range(i + 1, len(lines)):
                                upj = lines[j].upper()
                                if upj.startswith('CLASSIFICATION:'):
                                    classification_candidate = lines[j].split(':', 1)[
                                        1].strip().upper()
                                    break
                            if classification_candidate:
                                break

                    if details_candidate and classification_candidate:
                        details = details_candidate
                        if 'TRUSTED' in classification_candidate and 'UNTRUSTED' not in classification_candidate:
                            badge = 'TRUSTED'
                        elif 'UNTRUSTED' in classification_candidate:
                            badge = 'UNTRUSTED'
                        else:
                            badge = 'UNKNOWN'
                        parsed = True

                if not parsed:
                    # Fallback: detect keywords anywhere in the response
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
