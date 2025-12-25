from google import genai
import os

print("=" * 50)
print("Testing Gemini 3 Flash Preview API Connection")
print("=" * 50)
print(f"Model: {os.environ.get('GEMINI_MODEL', 'NOT SET')}")
print()

try:
    client = genai.Client(api_key=os.environ["GEMINI_API_KEY"])
    response = client.models.generate_content(
        model=os.environ["GEMINI_MODEL"],
        contents="Say exactly: Legacy Architect is ready!"
    )
    print(f"Response: {response.text}")
    print()
    print("=" * 50)
    print("SUCCESS! Gemini 3 Flash Preview is working!")
    print("=" * 50)
except Exception as e:
    print(f"ERROR: {e}")
