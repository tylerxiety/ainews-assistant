## Project Name
**AI News Assistant (Aina)**

## Elevator pitch
**Listen to your newsletters, chat with them.**
Turn standard RSS feeds into an interactive, bilingual audio experience—listen hands-free, ask questions mid-stream, and control playback with your voice.

## Inspiration
I subscribe to dozens of newsletters, but reading them all is a struggle. Passive text-to-speech tools exist, but they feel robotic and isolating—I can't ask "Wait, what does that acronym mean?" or "Skip to the section about React."

I wanted to transform the solitary act of reading into a dynamic conversation. I imagined a "news buddy" that not only reads to me with premium human-like voices but also allows me to interrupt, ask for clarification, or translate content on the fly—making my commute or workout not just productive, but interactive.

## What it does
Aina is a Progressive Web App (PWA) that converts any newsletter RSS feed into an intelligent audio session. It leverages the latest **Gemini 3** models to create a "Wow" hands-free experience:

*   **Smart Cleaning & Translation with Gemini 3 Flash**: We use the new Gemini 3 Flash model to process chaotic HTML from newsletters. Its advanced reasoning capability distinguishes between content, headers, and ads with high precision, and it provides nuanced English-to-Chinese translations that capture the original "newsletter tone"—all at lightning speed.
*   **Real-Time Voice Control with Gemini Live**: Users can control playback ("pause", "rewind 10s", "bookmark this") purely by voice. We use Gemini Live's function calling in a real-time WebSocket session to detect commands without a rigid "wake word."
*   **Conversational Q&A**: If you seek clarification (e.g., *"What did that last segment say about the new API?"*), Gemini Live answers instantly with audio, maintaining context of the entire newsletter.
*   **Premium Audio**: The app generates per-segment audio using Google Cloud's **Chirp 3 HD Aoede** voices for a lifelike listening experience.
*   **Bilingual Mode**: Seamlessly toggle between English and Chinese audio tracks, perfect for language learners or bilingual users.

## How we built it
The project is a full-stack integration of modern web technologies and Google's AI suite:
*   **Frontend**: React 19 PWA with TypeScript, utilizing **AudioContext** and AudioWorklets for raw PCM audio capture and streaming.
*   **Backend**: Python FastAPI service running on Cloud Run, acting as a secure WebSocket proxy between the client and Gemini/Vertex AI.
*   **AI Core**: 
    *   **Gemini 3 Flash (Preview)** for text processing (cleaning/translation).
    *   **Gemini Live (2.5 Flash)** for the real-time voice interface.
*   **Infrastructure**: Supabase (Postgres) for state/content storage, Cloud Storage for audio files, and Cloud Scheduler for automated RSS fetching.

Key to our speed was an **agentic workflow**: I "pair-programmed" with multiple AI agents (Antigravity, Claude Code, Codex) to prototype the architecture, review code, and debug complex concurrency issues in the voice pipeline.

## Challenges we ran into
*   **iOS Safari WebSocket Support**: Browsers like Safari have strict limitations on WebSocket upgrades and audio contexts. We solved this by building a custom Python WebSocket proxy that standardizes the connection to Gemini Live, ensuring it works seamlessly on mobile devices.
*   **The "Turn-Taking" Latency**: In a conversational UI, a 2-second delay feels like an eternity. We implemented a hybrid approach: **client-side VAD (Voice Activity Detection)** using `silero-vad` interrupts playback locally in milliseconds, while Gemini Live processes the audio stream in the cloud to determine if it was a command or a question.
*   **Syncing Bilingual Audio**: Mapping English segments to Chinese translations one-to-one while maintaining natural sentence boundaries for TTS required a carefully designed data schema and strict output validation from Gemini 3.

## Accomplishments that we're proud of
*   **Sub-Second Interruption**: The feeling of saying "Wait, stop" and having the audio pause *instantly* makes the AI feel truly present.
*   **"Magic" Voice Control**: Converting natural speech commands into app actions (tool calls) without traditional intent-classification training data.
*   **Gemini 3's Precision**: Seeing Gemini 3 Flash correctly identify obscure newsletter formatting quirks and translate technical jargon accurately was a huge win.
*   **Agentic Development**: Building a complex, production-ready system with queue management, extensive error handling, and cloud infrastructure interactions in a very short timeframe using AI agents.

## What's next for Aina
*   **Personalized Daily Brief**: Using Gemini to synthesize a custom 5-minute intro summarizing *all* unread newsletters based on user interests.
*   **Voice-Based "Deep Dives"**: Allowing users to ask the AI to "go find more info on this topic" by searching the web via Gemini, seamlessly adding the new info to the audio queue.
*   **Offline Vector Search**: Implementing local embeddings to allow Q&A against downloaded newsletters even when offline.

## Testing Instructions
No login required. Works on any modern browser (desktop or mobile).

1. Open the app and tap any newsletter issue
2. Tap **Play** on the audio bar — listen to the newsletter
3. To try **Voice Mode**: tap the mic icon in the center of the audio bar, accept the browser microphone permission
4. While listening, try these voice commands:
   * "Pause" / "Play"
   * "Next" (skips to next segment) / "Previous"
   * "Rewind" or "Forward" (5 seconds by default)
   * "Bookmark" (saves to ClickUp if configured)
5. Ask a question mid-stream, e.g. *"What did that last part say about transformers?"* — Gemini Live will answer with audio, then resume the newsletter

Best experienced on a phone with headphones for the full hands-free experience.

## Built With
*   **gemini-3-flash-preview** (Reasoning & Translation)
*   **gemini-live-2.5-flash** (Voice Interface)
*   **google-cloud-tts** (Chirp 3 HD Voices)
*   **vertex-ai**
*   **fastapi** / **python**
*   **react** / **typescript**
*   **supabase**
*   **google-cloud-run**
