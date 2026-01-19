"""
Test TTS voice availability, especially Chirp 3 HD.
"""
from google.cloud import texttospeech

client = texttospeech.TextToSpeechClient()

# List all voices
voices = client.list_voices()

# Filter for Chirp voices
chirp_voices = [v for v in voices.voices if "Chirp" in v.name]

print(f"Found {len(chirp_voices)} Chirp voices:\n")

for voice in chirp_voices[:20]:  # Show first 20
    print(f"  {voice.name}")
    print(f"    Language: {voice.language_codes}")
    print(f"    Gender: {voice.ssml_gender.name}")
    print()

# Check if our specific voice exists
target_voice = "en-US-Chirp3-HD-Aoede"
if any(v.name == target_voice for v in voices.voices):
    print(f"✅ Voice '{target_voice}' is available!")
else:
    print(f"❌ Voice '{target_voice}' NOT found")
    print("\nSearching for similar voices:")
    similar = [v for v in voices.voices if "Aoede" in v.name or ("Chirp" in v.name and "HD" in v.name)]
    for v in similar[:5]:
        print(f"  - {v.name}")
