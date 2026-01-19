"""
Test Gemini 3 Pro Preview with global region.
"""
import os
from dotenv import load_dotenv
import vertexai
from vertexai.generative_models import GenerativeModel

load_dotenv()

GCP_PROJECT_ID = os.getenv("GCP_PROJECT_ID")

print(f"Testing Gemini 3 Pro Preview in global region")
print(f"Project: {GCP_PROJECT_ID}\n")

try:
    # Initialize Vertex AI with global region
    vertexai.init(project=GCP_PROJECT_ID, location="global")

    # Try Gemini 3 Pro Preview
    model = GenerativeModel("gemini-3-pro-preview")

    response = model.generate_content("Say 'Hello from Gemini 3 Pro' in one sentence.")

    print(f"✅ Gemini 3 Pro Preview works!")
    print(f"✅ Response: {response.text.strip()}")

except Exception as e:
    print(f"❌ Error: {str(e)}")
    import traceback
    traceback.print_exc()
