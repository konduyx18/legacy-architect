"""Gemini API client for Legacy Architect agent."""

import os
import json
import re
from typing import Optional, Dict, Any
from google import genai


# Default model
DEFAULT_MODEL = "gemini-3-flash-preview"


def _extract_text(response: Any) -> str:
    """
    Extract text from Gemini API response, handling multiple response formats.
    
    Supports:
    - Standard Gemini response (response.text)
    - Candidates-based response (response.candidates[0].content.parts[0].text)
    - Gemini 3 thinking models (different structure with thoughts)
    - Fallback regex extraction from string representation
    
    Args:
        response: The Gemini API response object
    
    Returns:
        Extracted text from the response
    
    Raises:
        ValueError: If text cannot be extracted from response
    """
    if response is None:
        raise ValueError("API returned None response")
    
    # Method 1: Try standard response.text attribute
    if hasattr(response, 'text') and response.text:
        return response.text
    
    # Method 2: Try candidates structure (standard format)
    if hasattr(response, 'candidates') and response.candidates:
        try:
            candidate = response.candidates[0]
            if hasattr(candidate, 'content') and candidate.content:
                if hasattr(candidate.content, 'parts') and candidate.content.parts:
                    part = candidate.content.parts[0]
                    if hasattr(part, 'text') and part.text:
                        return part.text
        except (IndexError, AttributeError) as e:
            # Continue to next method if this fails
            pass
    
    # Method 3: Try Gemini 3 thinking model format
    # Gemini 3 models may have thoughts_token_count but empty content
    # Check if there's a thought or alternative text field
    if hasattr(response, 'candidates') and response.candidates:
        try:
            candidate = response.candidates[0]
            
            # Check for thought field
            if hasattr(candidate, 'thought') and candidate.thought:
                return candidate.thought
            
            # Check for alternative content structures
            if hasattr(candidate, 'content'):
                content = candidate.content
                
                # Try to get any text from parts even if it looks empty
                if hasattr(content, 'parts') and content.parts:
                    for part in content.parts:
                        # Check for text attribute
                        if hasattr(part, 'text'):
                            text = part.text
                            if text:  # Only return if not empty
                                return text
                        
                        # Check for thought attribute in part
                        if hasattr(part, 'thought') and part.thought:
                            return part.thought
                
                # Try to get text directly from content
                if hasattr(content, 'text') and content.text:
                    return content.text
        except (IndexError, AttributeError) as e:
            # Continue to fallback method
            pass
    
    # Method 4: Fallback - try to extract text from string representation
    # This handles cases where the response structure is non-standard
    response_str = str(response)
    
    # Try to find text in common patterns
    text_patterns = [
        r"text:\s*['\"](.+?)['\"]",
        r"text=(['\"])(.+?)\1",
        r"'text':\s*['\"](.+?)['\"]",
        r'"text":\s*"(.+?)"',
    ]
    
    for pattern in text_patterns:
        match = re.search(pattern, response_str, re.DOTALL)
        if match:
            # Get the last group (the actual text content)
            text = match.group(match.lastindex)
            if text and text.strip():
                return text.strip()
    
    # If all methods fail, provide detailed error message
    error_details = []
    error_details.append(f"Response type: {type(response)}")
    
    if hasattr(response, 'candidates'):
        error_details.append(f"Has candidates: {len(response.candidates) if response.candidates else 0}")
    
    if hasattr(response, 'thoughts_token_count'):
        error_details.append(f"Thoughts token count: {response.thoughts_token_count}")
    
    if hasattr(response, '__dict__'):
        error_details.append(f"Response attributes: {list(response.__dict__.keys())}")
    
    error_msg = "Could not extract text from response. " + " | ".join(error_details)
    raise ValueError(error_msg)


def _strip_markdown_code_blocks(text: str) -> str:
    """
    Remove markdown code block markers from text.
    
    Handles formats like:
    ```python
    code
    ```
    
    or just:
    ```
    code
    ```
    """
    # Remove opening code block markers (```python, ```py, ```)
    text = re.sub(r'^```(?:python|py)?\s*\n', '', text, flags=re.MULTILINE)
    
    # Remove closing code block markers
    text = re.sub(r'\n```\s*$', '', text, flags=re.MULTILINE)
    
    # Also handle case where ``` is at the very start or end
    text = text.strip()
    if text.startswith('```python'):
        text = text[9:].lstrip('\n')
    elif text.startswith('```py'):
        text = text[5:].lstrip('\n')
    elif text.startswith('```'):
        text = text[3:].lstrip('\n')
    
    if text.endswith('```'):
        text = text[:-3].rstrip('\n')
    
    return text.strip()


def get_client() -> genai.Client:
    """
    Get an authenticated Gemini client.
    
    Returns:
        Configured Gemini client
    
    Raises:
        ValueError: If GEMINI_API_KEY is not set
    """
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        raise ValueError("GEMINI_API_KEY environment variable is not set")
    
    return genai.Client(api_key=api_key)


def get_model_name() -> str:
    """Get the model name from environment or use default."""
    return os.environ.get("GEMINI_MODEL", DEFAULT_MODEL)


def generate_text(
    prompt: str,
    system_instruction: Optional[str] = None,
    temperature: float = 0.7,
    max_tokens: int = 16384
) -> str:
    """
    Generate text using Gemini.
    
    Args:
        prompt: The user prompt
        system_instruction: Optional system instruction
        temperature: Sampling temperature (0.0-1.0)
        max_tokens: Maximum tokens to generate
    
    Returns:
        Generated text response
    """
    client = get_client()
    model = get_model_name()
    
    # Build config
    config = genai.types.GenerateContentConfig(
        temperature=temperature,
        max_output_tokens=max_tokens,
    )
    
    if system_instruction:
        config.system_instruction = system_instruction
    
    # Generate response
    response = client.models.generate_content(
        model=model,
        contents=prompt,
        config=config
    )
    
    # Use the enhanced _extract_text() helper to handle all response formats
    return _extract_text(response)


def generate_json(
    prompt: str,
    system_instruction: Optional[str] = None,
    temperature: float = 0.3
) -> Dict[str, Any]:
    """
    Generate JSON using Gemini.
    
    Args:
        prompt: The user prompt
        system_instruction: Optional system instruction
        temperature: Sampling temperature (lower = more deterministic)
    
    Returns:
        Parsed JSON response as dict
    """
    # Add JSON instruction to system prompt
    json_system = (system_instruction or "") + """

IMPORTANT: Respond with ONLY valid JSON. No markdown, no code blocks, no explanation.
Just the raw JSON object."""
    
    response = generate_text(
        prompt=prompt,
        system_instruction=json_system.strip(),
        temperature=temperature
    )
    
    # Clean up response - remove markdown code blocks if present
    cleaned = response.strip()
    if cleaned.startswith("```json"):
        cleaned = cleaned[7:]
    elif cleaned.startswith("```"):
        cleaned = cleaned[3:]
    if cleaned.endswith("```"):
        cleaned = cleaned[:-3]
    cleaned = cleaned.strip()
    
    return json.loads(cleaned)


def generate_code(
    prompt: str,
    system_instruction: Optional[str] = None,
    temperature: float = 0.2
) -> str:
    """
    Generate code using Gemini.
    
    Args:
        prompt: The user prompt
        system_instruction: Optional system instruction
        temperature: Sampling temperature (lower = more deterministic)
    
    Returns:
        Generated code (cleaned of markdown)
    """
    response = generate_text(
        prompt=prompt,
        system_instruction=system_instruction,
        temperature=temperature
    )
    
    # Strip any markdown code blocks
    code = _strip_markdown_code_blocks(response)
    
    return code


def generate_diff(
    prompt: str,
    system_instruction: Optional[str] = None,
    temperature: float = 0.2
) -> str:
    """
    Generate a unified diff using Gemini.
    
    Args:
        prompt: The user prompt
        system_instruction: Optional system instruction
        temperature: Sampling temperature (lower = more deterministic)
    
    Returns:
        Generated unified diff (cleaned of markdown)
    """
    response = generate_text(
        prompt=prompt,
        system_instruction=system_instruction,
        temperature=temperature
    )
    
    # Clean up response - remove markdown code blocks if present
    cleaned = response.strip()
    if cleaned.startswith("```diff"):
        cleaned = cleaned[7:]
    elif cleaned.startswith("```"):
        cleaned = cleaned[3:]
    if cleaned.endswith("```"):
        cleaned = cleaned[:-3]
    
    return cleaned.strip()


def test_connection() -> bool:
    """
    Test the Gemini API connection.
    
    Returns:
        True if connection successful, False otherwise
    """
    try:
        response = generate_text(
            prompt="Hello",
            temperature=0.0,
            max_tokens=100
        )
        print(f"Response: {response}")
        return response is not None and len(response) > 0
    except Exception as e:
        print(f"Connection test failed: {e}")
        return False


if __name__ == "__main__":
    print("Testing Gemini client...")
    print(f"Model: {get_model_name()}")
    
    if test_connection():
        print("✅ Connection successful!")
        
        # Test JSON generation
        print("\nTesting JSON generation...")
        result = generate_json(
            prompt="Return a JSON object with keys 'status' (value: 'ok') and 'count' (value: 42)"
        )
        print(f"Result: {result}")
        
    else:
        print("❌ Connection failed!")
