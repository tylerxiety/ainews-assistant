"""
Test GCP services: TTS, Storage, and Vertex AI (Gemini).
"""
import os
from dotenv import load_dotenv
from google.cloud import texttospeech
from google.cloud import storage
import vertexai
from vertexai.generative_models import GenerativeModel

# Load environment variables
load_dotenv()

GCP_PROJECT_ID = os.getenv("GCP_PROJECT_ID")
GCP_REGION = os.getenv("GCP_REGION")
GCS_BUCKET_NAME = os.getenv("GCS_BUCKET_NAME")

print(f"Testing GCP services for project: {GCP_PROJECT_ID}")
print(f"Region: {GCP_REGION}")
print(f"Bucket: {GCS_BUCKET_NAME}\n")

# Test 1: Text-to-Speech
print("1. Testing Text-to-Speech API...")
try:
    tts_client = texttospeech.TextToSpeechClient()
    # List voices to verify access
    voices = tts_client.list_voices()
    print(f"   ✅ TTS API accessible ({len(voices.voices)} voices available)")
except Exception as e:
    print(f"   ❌ TTS API error: {str(e)}")

# Test 2: Cloud Storage
print("\n2. Testing Cloud Storage...")
try:
    storage_client = storage.Client()
    bucket = storage_client.bucket(GCS_BUCKET_NAME)
    if bucket.exists():
        print(f"   ✅ Bucket '{GCS_BUCKET_NAME}' exists and is accessible")
    else:
        print(f"   ❌ Bucket '{GCS_BUCKET_NAME}' not found")
except Exception as e:
    print(f"   ❌ Storage error: {str(e)}")

# Test 3: Vertex AI (Gemini)
print("\n3. Testing Vertex AI (Gemini)...")
try:
    vertexai.init(project=GCP_PROJECT_ID, location=GCP_REGION)
    # Try different model names
    model_names = ["gemini-1.5-pro-002", "gemini-1.5-flash-002", "gemini-1.5-pro"]

    for model_name in model_names:
        try:
            model = GenerativeModel(model_name)
            response = model.generate_content("Say 'Hello' in one word.")
            print(f"   ✅ Vertex AI initialized with {model_name}")
            print(f"   ✅ Gemini test response: {response.text.strip()}")
            break
        except Exception as model_error:
            if model_name == model_names[-1]:  # Last attempt
                raise model_error
            continue
except Exception as e:
    print(f"   ❌ Vertex AI error: {str(e)}")

print("\n✅ GCP connection test complete!")
