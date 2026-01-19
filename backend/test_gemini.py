"""
Test Google GenAI (Gemini) with the new SDK.
"""
import os
from dotenv import load_dotenv
from google import genai
from google.genai import types

# Load environment variables
load_dotenv()

GCP_PROJECT_ID = os.getenv("GCP_PROJECT_ID")
GCP_REGION = os.getenv("GCP_REGION")

print(f"Testing Gemini with new Google GenAI SDK")
print(f"Project: {GCP_PROJECT_ID}, Region: {GCP_REGION}\n")

try:
    # Initialize client
    client = genai.Client(
        vertexai=True,
        project=GCP_PROJECT_ID,
        location=GCP_REGION
    )

    # Test with a simple prompt
    response = client.models.generate_content(
        model='gemini-2.0-flash-exp',
        contents='Say "Hello" in one word.'
    )

    print(f"✅ Gemini API working!")
    print(f"✅ Test response: {response.text.strip()}")

except Exception as e:
    print(f"❌ Gemini error: {str(e)}")

print("\n✅ Gemini test complete!")
