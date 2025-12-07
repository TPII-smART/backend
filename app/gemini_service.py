"""Gemini API service."""
from google import genai
from google.genai import types
from typing import Any, Tuple, Literal
from app.config import settings
import httpx


class GeminiService:
    """Service for interacting with Google Gemini API."""

    def __init__(self):
        """Initialize Gemini client."""
        self.client = genai.Client(api_key=settings.GEMINI_API_KEY)
        self.model_id = "gemini-2.5-flash"

    def get_prompt(self, expected: str) -> str:
        """Generate prompt for Gemini API based on hash and expected value."""
        return f"""
    You are an art juror.

     Given the following information:
     - The uploaded resources 
     - Expected: {expected}

     Task: Decide whether the resources contains the EXPECTED content between all of them.

     STRICT OUTPUT RULES (MANDATORY):
     1) Output exactly TWO lines and nothing else. Use these exact prefixes (uppercase) with a single space after the colon:
         DETAILS: <brief analysis, <=50 words>
         CLASSIFICATION: <MATCHS WITH DESCRIPTION|NEEDS REVISION|UNKNOWN>
     2) The second line (DETAILS) must NOT include the hash or any extra lines/annotations.
     3) DETAILS must be strictly consistent with the chosen CLASSIFICATION. To ensure this, follow these allowed/forbidden phrasing rules:
         - If CLASSIFICATION is MATCHS WITH DESCRIPTION: DETAILS MUST assert presence. Include one of these positive phrases: "is present", "present", "clearly shows", "visible", "depicted". DETAILS MUST NOT contain negations or absence words such as "no", "not", "absent", "instead", "cannot".
         - If CLASSIFICATION is NEEDS REVISION: DETAILS MUST assert absence or mismatch. Include one of these negative phrases: "no", "not present", "absent", "instead", "a different object". DETAILS MUST NOT include positive presence phrases like "is present", "clearly shows", "visible", "depicted".
         - If CLASSIFICATION is UNKNOWN: DETAILS MUST explain uncertainty with words like "cannot determine", "unclear", "too blurred", "occluded", "cropped", "ambiguous framing", or "insufficient detail". DETAILS MUST NOT claim presence or definite absence.
     4) Word limit: DETAILS must be <=50 words.
     5) If you cannot confidently follow the required format and consistency rules, return exactly:
         CLASSIFICATION: UNKNOWN
         DETAILS: Image analysis inconclusive; insufficient confidence to mark MATCHS WITH DESCRIPTION or NEEDS REVISION.
     6) Do NOT include JSON, code, headings, extra commentary, punctuation beyond standard sentence punctuation in DETAILS, or any other text.

     Examples (must follow exactly):
     DETAILS: Clear image of a blue ceramic mug centered and unobstructed; expected 'blue ceramic mug' is present.
     CLASSIFICATION: MATCHS WITH DESCRIPTION

     DETAILS: No blue ceramic mug visible; instead a metal water bottle is present.
     CLASSIFICATION: NEEDS REVISION

     DETAILS: Image is heavily blurred and cropped; cannot determine whether expected object is present.
     CLASSIFICATION: UNKNOWN

     Follow these rules exactly. Any deviation is unacceptable.
     """

    async def get_image(self, hash: str) -> tuple[bytes, str]:
        # Prefer Cloudflare IPFS gateway which is generally script-friendly/CORS-friendly.
        # Accept hashes with or without "ipfs://" or "/ipfs/" prefixes.
        ipfs_hash = hash
        if ipfs_hash.startswith("ipfs://"):
            ipfs_hash = ipfs_hash[len("ipfs://"):]
        if ipfs_hash.startswith("/ipfs/"):
            ipfs_hash = ipfs_hash[len("/ipfs/"):]
        # Try multiple public IPFS gateways as fallback (Cloudflare may not resolve)
        gateways = [
            "https://cloudflare-ipfs.com/ipfs/{}",
            "https://ipfs.io/ipfs/{}",
            "https://dweb.link/ipfs/{}",
            "https://gateway.pinata.cloud/ipfs/{}",
        ]
        last_exc = None
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                for gw in gateways:
                    url = gw.format(ipfs_hash)
                    try:
                        resp = await client.get(url)
                        resp.raise_for_status()
                        image_bytes: bytes = resp.content
                        mime_type = resp.headers.get(
                            'content-type', 'application/octet-stream')
                        return image_bytes, mime_type
                    except Exception as e:
                        last_exc = e
                        # try next gateway
            # If we reach here no gateway succeeded
            tried = ", ".join(gateways)
            raise Exception(
                f"Failed to download image for hash {ipfs_hash} from gateways: {tried}; last error: {last_exc}")
        except Exception as e:
            raise Exception(
                f"Failed to download image from IPFS gateways for {ipfs_hash}: {e}")

    async def download_image(self, hash: str) -> types.Part:
        """Download image from IPFS and return as Gemini Part."""
        image_bytes, mime_type = await self.get_image(hash)
        return types.Part.from_bytes(
            data=image_bytes,
            mime_type=mime_type,
        )

    async def generate_response(self, hashes: list[str], expected_value: str) -> Tuple[Literal['MATCHS WITH DESCRIPTION', 'NEEDS REVISION', 'UNKNOWN'], str]:
        """
        Generate response from Gemini API with custom prompt.

        Args:
            hash_value: Hash identifier from request
            expected_value: Expected value from request

        Returns:
            Tuple of (badge, details) where badge is one of 'MATCHS WITH DESCRIPTION', 'NEEDS REVISION', 'UNKNOWN'
            and details is the analysis text from Gemini
        """

        contents: types.ContentListUnion = [await self.download_image(h) for h in hashes]
        prompt = self.get_prompt(expected_value)
        contents.append(prompt)

        try:
            response = self.client.models.generate_content(
                model=self.model_id,
                contents=contents
            )

            # Extract text from response
            if response.text:
                response_text = response.text.strip()

                # Parse the response to extract badge and details
                badge: Literal['MATCHS WITH DESCRIPTION',
                               'NEEDS REVISION', 'UNKNOWN'] = 'UNKNOWN'
                details = response_text

                # Split into non-empty lines and prefer the format:
                # DETAILS: <...>  (first line)
                # CLASSIFICATION: <MATCHS WITH DESCRIPTION|NEEDS REVISION|UNKNOWN>  (second line)
                lines = [l.strip()
                         for l in response_text.splitlines() if l.strip()]

                parsed = False
                if len(lines) >= 2 and lines[0].upper().startswith('DETAILS:') and lines[1].upper().startswith('CLASSIFICATION:'):
                    details = lines[0].split(':', 1)[1].strip()
                    classification = lines[1].split(':', 1)[1].strip().upper()
                    if 'MATCHS WITH DESCRIPTION' in classification and 'NEEDS REVISION' not in classification:
                        badge = 'MATCHS WITH DESCRIPTION'
                    elif 'NEEDS REVISION' in classification:
                        badge = 'NEEDS REVISION'
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
                        if 'MATCHS WITH DESCRIPTION' in classification_candidate and 'NEEDS REVISION' not in classification_candidate:
                            badge = 'MATCHS WITH DESCRIPTION'
                        elif 'NEEDS REVISION' in classification_candidate:
                            badge = 'NEEDS REVISION'
                        else:
                            badge = 'UNKNOWN'
                        parsed = True

                if not parsed:
                    # Fallback: detect keywords anywhere in the response
                    response_upper = response_text.upper()
                    if 'MATCHS WITH DESCRIPTION' in response_upper and 'NEEDS REVISION' not in response_upper:
                        badge = 'MATCHS WITH DESCRIPTION'
                    elif 'NEEDS REVISION' in response_upper:
                        badge = 'NEEDS REVISION'
                    else:
                        badge = 'UNKNOWN'

                return badge, details
            else:
                return 'UNKNOWN', "No response generated from Gemini API"

        except Exception as e:
            raise Exception(f"Gemini API error: {str(e)}")


# Global Gemini service instance
gemini_service = GeminiService()
