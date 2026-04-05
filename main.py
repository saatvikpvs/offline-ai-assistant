from flask import Flask, request, Response
from flask_cors import CORS
from faster_whisper import WhisperModel
import subprocess
import io
import wave
import os
import json
import re
import base64
import requests as http_requests

from rag.retriever import query_db


app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "*", "methods": ["GET", "POST", "OPTIONS"], "allow_headers": ["Content-Type"]}})

# ---------- Whisper Model (loaded once) ----------
print("[WHISPER] Loading model (small)...")
model = WhisperModel("small")
print("[WHISPER] Ready.")

# ---------- Ollama Config ----------
OLLAMA_URL = "http://localhost:11434/api/generate"
OLLAMA_MODEL = "phi3"

# ---------- Agent System Prompts ----------
SYSTEM_PROMPTS = {
    "education": """You are an expert, patient, and highly knowledgeable Education Tutor. 
Your goal is to help the user understand concepts by breaking them down into simple, easy-to-grasp analogies. 
Maintain an encouraging tone. Always keep your responses concise, natural, and conversational, as they will be spoken aloud via text-to-speech.""",

    "medical": """You are a knowledgeable and empathetic Medical Information Assistant. 
Provide clear, general health guidance and wellness information. 
CRITICAL RULE: You must NEVER diagnose illnesses or prescribe medication. Always remind the user to consult a licensed medical professional for serious health concerns. Keep your response comforting, brief, and conversational.""",

    "governance": """You are an accurate and helpful Government Services Assistant. 
Your task is to help citizens understand public policies, schemes, and administrative procedures. 
Provide factual guidance on how to prioritize access to services. Avoid political commentary. Focus purely on actionable advice and keep explanations brief and easy to understand when spoken aloud.""",

    "general": """You are a friendly, highly capable omni-purpose AI Assistant. 
You are helpful, warm, and conversational. Answer general questions directly. 
Because your responses will be spoken aloud to the user, you MUST avoid using complicated markdown, code blocks, bullet points, or weird symbols. Keep your phrasing natural and conversational like a real human speaking."""
}


# ---------- Helper: Text → Raw PCM via Piper ----------
def generate_raw_audio(text):
    process = subprocess.Popen(
        ["piper", "-m", "models/en_US-lessac-high.onnx", "--output-raw"],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE
    )
    audio_bytes, _ = process.communicate(text.encode())
    return audio_bytes


# ---------- Helper: Raw PCM → WAV ----------
def pcm_to_wav(pcm_bytes):
    wav_buffer = io.BytesIO()
    with wave.open(wav_buffer, "wb") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(22050)
        wf.writeframes(pcm_bytes)
    wav_buffer.seek(0)
    return wav_buffer.read()


# ---------- Helper: Text → WAV ----------
def generate_audio(text):
    return pcm_to_wav(generate_raw_audio(text))


# ---------- Ollama: Quick non-streaming call (for classification) ----------
def classify_query(text):
    try:
        resp = http_requests.post(OLLAMA_URL, json={
            "model": OLLAMA_MODEL,
            "prompt": f"Classify into ONE word: education, medical, governance, or general.\nQuery: {text}\nCategory:",
            "stream": False,
            "options": {"temperature": 0.1, "num_predict": 5}
        }, timeout=15)

        result = resp.json().get("response", "general").strip().lower()

        for cat in ["education", "medical", "governance"]:
            if cat in result:
                return cat
        return "general"
    except Exception as e:
        print(f"Classification error: {e}")
        return "general"


# ---------- Ollama: Streaming token generator ----------
def stream_ollama(prompt, system=""):
    payload = {
        "model": OLLAMA_MODEL,
        "prompt": prompt,
        "stream": True,
        "options": {"temperature": 0.3, "num_predict": 150}
    }
    if system:
        payload["system"] = system

    response = http_requests.post(OLLAMA_URL, json=payload, stream=True, timeout=60)

    for line in response.iter_lines():
        if line:
            data = json.loads(line)
            if "response" in data:
                yield data["response"]
            if data.get("done"):
                break


# ==========================================================
# ROUTES
# ==========================================================

# ---------- Root ----------
@app.route("/", methods=["GET"])
def index():
    return "Backend is running!"


# ---------- Greeting ----------
@app.route("/greet", methods=["GET"])
def greet():
    greeting = "Hey, I am your AI assistant. How can I help you today?"
    audio = generate_audio(greeting)
    return Response(audio, mimetype="audio/wav")


# ---------- Voice (STREAMING) ----------
@app.route("/voice", methods=["POST"])
def voice():
    print("\n--- Voice request received ---")

    audio_file = request.files["audio"]
    audio_file.save("input.wav")

    file_size = os.path.getsize("input.wav")
    print(f"Saved input.wav — {file_size} bytes")

    if file_size < 1000:
        print("File too small, skipping")
        return Response(status=204)

    # ---------- Step 1: Speech to Text ----------
    try:
        segments, _ = model.transcribe(
            "input.wav",
            beam_size=1,
            language="en",
            condition_on_previous_text=False,   # prevents repetition loops
            no_speech_threshold=0.6,
            compression_ratio_threshold=2.4
        )
        text = " ".join([s.text for s in segments]).strip()
    except Exception as e:
        print(f"Transcription error: {e}")
        return Response(status=204)

    if not text:
        print("No speech detected")
        return Response(status=204)

    # Remove repeated words/phrases (Whisper hallucination cleanup)
    words = text.split()
    cleaned = [words[0]] if words else []
    for i in range(1, len(words)):
        if words[i].lower() != words[i-1].lower():
            cleaned.append(words[i])
    text = " ".join(cleaned)

    print(f"User said: {text}")

    # ---------- Step 2: RAG Retrieval (fast — embeddings cached) ----------
    context = query_db(text)

    # ---------- Step 3: Classify topic (quick call) ----------
    topic = classify_query(text)
    print(f"Topic: {topic}")

    # ---------- Step 4+5: Stream response ----------
    return stream_response(text, context, topic)


from flask_cors import cross_origin

# ---------- Text Input Route (no Whisper needed — faster!) ----------
@app.route("/text", methods=["POST", "OPTIONS"])
@cross_origin()
def text_input():
    data = request.get_json() or {}
    text = data.get("text", "").strip()

    if not text:
        return Response(status=204)

    print(f"\n--- Text input received ---")
    print(f"User typed: {text}")

    context = query_db(text)
    topic = classify_query(text)
    print(f"Topic: {topic}")

    return stream_response(text, context, topic)


# ---------- Shared: Stream LLM → Piper → SSE ----------
def stream_response(user_text, context, topic):
    system = SYSTEM_PROMPTS.get(topic, SYSTEM_PROMPTS["general"])
    prompt = f"""Use the following knowledge if relevant.

Context:
{context}

Question:
{user_text}

Answer clearly and briefly in 1-2 sentences."""

    def generate():
        # Send user text first so frontend can display it
        yield f"data:{json.dumps({'userText': user_text})}\n\n"

        buffer = ""
        full_response = []

        for token in stream_ollama(prompt, system):
            buffer += token
            full_response.append(token)

            # Look for sentence endings followed by space or end
            sentence_match = re.search(r'[.!?](?:\s|$)', buffer)
            if sentence_match:
                sentence = buffer[:sentence_match.end()].strip()
                buffer = buffer[sentence_match.end():]

                if sentence and len(sentence) > 3:
                    print(f"  → Speaking: {sentence}")
                    wav = generate_audio(sentence)
                    b64 = base64.b64encode(wav).decode()
                    yield f"data:{json.dumps({'audio': b64, 'text': sentence})}\n\n"

        # Handle remaining text in buffer
        if buffer.strip() and len(buffer.strip()) > 3:
            print(f"  → Speaking (final): {buffer.strip()}")
            wav = generate_audio(buffer.strip())
            b64 = base64.b64encode(wav).decode()
            yield f"data:{json.dumps({'audio': b64, 'text': buffer.strip()})}\n\n"

        full_text = "".join(full_response)
        print(f"Full response: {full_text}")
        yield f"data:{json.dumps({'done': True, 'fullText': full_text})}\n\n"

    return Response(
        generate(),
        mimetype="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"}
    )


# ---------- Run Server ----------
if __name__ == "__main__":
    app.run(port=5000)