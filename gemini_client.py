import os
from google import genai
from google.genai import types
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# We retrieve the API key from environment
api_key = os.getenv("GEMINI_API_KEY")

def get_gemini_client():
    """Retrieve genai.Client instance using GEMINI_API_KEY from environment."""
    if not api_key:
        raise ValueError(
            "GEMINI_API_KEY is not set in the environment or .env file. "
            "Please create a .env file containing GEMINI_API_KEY=your_key."
        )
    return genai.Client(api_key=api_key)

def ask_gemini_with_google(prompt: str, model: str = "gemini-2.5-flash") -> dict:
    """
    Generate response from Gemini model with Google Search grounding enabled.
    Returns dictionary with final answer, token usage metadata, and raw response.
    """
    try:
        client = get_gemini_client()
        
        # Configure the request to use Google Search Grounding
        config = types.GenerateContentConfig(
            tools=[types.Tool(google_search=types.GoogleSearch())]
        )
        
        # Generate content
        response = client.models.generate_content(
            model=model,
            contents=prompt,
            config=config
        )
        
        # Extract token usage details
        prompt_tokens = 0
        completion_tokens = 0
        total_tokens = 0
        
        if response.usage_metadata:
            prompt_tokens = response.usage_metadata.prompt_token_count or 0
            completion_tokens = response.usage_metadata.candidates_token_count or 0
            total_tokens = response.usage_metadata.total_token_count or 0
            
        return {
            "answer": response.text or "",
            "tokens": {
                "prompt_tokens": prompt_tokens,
                "completion_tokens": completion_tokens,
                "total_tokens": total_tokens
            },
            "raw": response
        }
        
    except Exception as e:
        raise RuntimeError(f"Error calling Gemini API: {str(e)}") from e
