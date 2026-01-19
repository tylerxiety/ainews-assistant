"""
Test which Gemini models are available in the GCP project.
"""
import os
from dotenv import load_dotenv
import vertexai
from vertexai.generative_models import GenerativeModel

load_dotenv()

GCP_PROJECT_ID = os.getenv("GCP_PROJECT_ID")
GCP_REGION = os.getenv("GCP_REGION")

print(f"Testing Gemini models in project: {GCP_PROJECT_ID}")
print(f"Region: {GCP_REGION}\n")

# Initialize Vertex AI
vertexai.init(project=GCP_PROJECT_ID, location=GCP_REGION)

# Try different Gemini model names
model_names = [
    "gemini-3-pro",
    "gemini-2.0-flash",
    "gemini-1.5-pro-002",
    "gemini-1.5-flash-002",
    "gemini-1.5-pro",
    "gemini-pro",
]

for model_name in model_names:
    try:
        print(f"Testing {model_name}...")
        model = GenerativeModel(model_name)
        response = model.generate_content("Say 'Hello' in one word.")
        print(f"  ✅ {model_name} works!")
        print(f"  Response: {response.text.strip()}\n")
        break
    except Exception as e:
        print(f"  ❌ {model_name} failed: {str(e)[:100]}\n")
