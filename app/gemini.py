import os
from google import genai
from dotenv import load_dotenv
import time
from google.genai import errors
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

load_dotenv()

# ✅ FIX: Prioritize one API key to avoid confusion
key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
if not key:
    raise EnvironmentError("Missing GEMINI_API_KEY or GOOGLE_API_KEY in .env file")

logger.info(f"GEMINI KEY FOUND: {key[:6]}...")

client = genai.Client(api_key=key)

# Use a more conservative model for rate limits
MODEL = os.getenv("GEMINI_MODEL", "gemini-2.0-flash-lite")

# ✅ IMPROVEMENT: Track request timing to avoid rate limits
_last_request_time = 0
_min_request_interval = 2.0  # Minimum 2 seconds between requests

def generate_text(prompt: str, max_retries: int = 3) -> str:
    """
    Generate text with Gemini, with exponential backoff for rate limits.
    
    Args:
        prompt: The prompt to send to Gemini
        max_retries: Maximum number of retry attempts
        
    Returns:
        Generated text response
        
    Raises:
        RuntimeError: If rate limit retries are exhausted
        Exception: For other API errors
    """
    global _last_request_time
    
    # ✅ Rate limit prevention: Wait between requests
    time_since_last = time.time() - _last_request_time
    if time_since_last < _min_request_interval:
        wait_time = _min_request_interval - time_since_last
        logger.info(f"Rate limit prevention: waiting {wait_time:.2f}s")
        time.sleep(wait_time)
    
    delay = 3.0  # Start with 3 second delay
    last_error = None
    
    for attempt in range(max_retries):
        try:
            _last_request_time = time.time()
            
            logger.info(f"Calling Gemini (attempt {attempt + 1}/{max_retries})...")
            
            resp = client.models.generate_content(
                model=MODEL,
                contents=prompt,
            )
            
            logger.info("Gemini response received successfully")
            return resp.text
        
        except errors.ClientError as e:
            last_error = e
            error_str = str(e)
            
            # Check for rate limit errors
            if "429" in error_str or "RESOURCE_EXHAUSTED" in error_str or "quota" in error_str.lower():
                logger.warning(f"Rate limit hit (attempt {attempt + 1}/{max_retries}). Waiting {delay}s...")
                
                if attempt < max_retries - 1:
                    time.sleep(delay)
                    delay = min(delay * 2, 30)  # Exponential backoff, max 30s
                    continue
                else:
                    # Last attempt failed
                    logger.error("Rate limit retries exhausted")
                    raise RuntimeError(
                        "Gemini API rate limit exceeded. Please wait a few minutes and try again. "
                        "Consider upgrading your API key or reducing request frequency."
                    ) from e
            
            # For other errors, log and re-raise
            logger.error(f"Gemini API error: {error_str}")
            raise
        
        except Exception as e:
            logger.error(f"Unexpected error calling Gemini: {str(e)}")
            raise
    
    # Should not reach here, but just in case
    raise RuntimeError("Failed to generate text after retries") from last_error


def generate_text_with_fallback(prompt: str, fallback_response: str = None) -> str:
    """
    Generate text with a fallback response if rate limited.
    
    Args:
        prompt: The prompt to send
        fallback_response: What to return if rate limited (optional)
        
    Returns:
        Generated text or fallback response
    """
    try:
        return generate_text(prompt)
    except RuntimeError as e:
        if "rate limit" in str(e).lower():
            logger.warning("Using fallback response due to rate limit")
            if fallback_response:
                return fallback_response
            return "Rate limit reached. Please try again in a few minutes."
        raise