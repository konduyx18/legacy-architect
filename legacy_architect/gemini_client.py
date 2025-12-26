"""Gemini API client for Legacy Architect agent."""

import os
import json
import re
from typing import Optional, Dict, Any
from google import genai


# Default model
DEFAULT_MODEL = "gemini-3-flash-preview"


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
    
    # Handle response - check for text attribute
    if response is None:
        raise ValueError("API returned None response")
    
    # Try to get text from response
    if hasattr(response, 'text') and response.text:
        return response.text
    
    # Try candidates structure
    if hasattr(response, 'candidates') and response.candidates:
        candidate = response.candidates[0]
        if hasattr(candidate, 'content') and candidate.content:
            if hasattr(candidate.content, 'parts') and candidate.content.parts:
                return candidate.content.parts[0].text
    
    raise ValueError(f"Could not extract text from response: {response}")


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
