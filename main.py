from flask import Flask, request, Response
from flask_cors import CORS
from faster_whisper import WhisperModel
import subprocess
import io
import wave

from rag.retriever import query_db

from agents.conversation_agent import create_conversation_agent
from agents.education_agent import create_education_agent
from agents.medical_agent import create_medical_agent
from agents.governance_agent import create_governance_agent


app = Flask(__name__)
CORS(app)

# ---------- Whisper Model ----------
model = WhisperModel("tiny")

# ---------- Agents ----------
conversation_agent = create_conversation_agent()
education_agent = create_education_agent()
medical_agent = create_medical_agent()
governance_agent = create_governance_agent()


# ---------- Helper: Generate Audio ----------
def generate_audio(text):

    process = subprocess.Popen(
        ["piper", "-m", "models/en_US-lessac-high.onnx", "--output-raw"],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE
    )

    audio_bytes, _ = process.communicate(text.encode())

    wav_buffer = io.BytesIO()

    with wave.open(wav_buffer, "wb") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(22050)
        wf.writeframes(audio_bytes)

    wav_buffer.seek(0)

    return wav_buffer.read()


# ---------- Greeting Route ----------
@app.route("/greet", methods=["GET"])
def greet():

    greeting = "Hey, I am your AI assistant. How can I help you today?"

    audio = generate_audio(greeting)

    return Response(audio, mimetype="audio/wav")


# ---------- Voice Route ----------
@app.route("/voice", methods=["POST"])
def voice():

    print("Voice request received")

    audio_file = request.files["audio"]
    audio_file.save("input.webm")

    # ---------- Speech to Text ----------
    segments, _ = model.transcribe(
        "input.webm",
        beam_size=3,
        vad_filter=True
    )

    text = " ".join([segment.text for segment in segments]).strip()

    if text == "":
        print("No speech detected")
        return Response(status=204)

    print("User said:", text)

    # ---------- RAG Retrieval ----------
    context = query_db(text)

    # ---------- Classification ----------
    classification_prompt = f"""
Classify the user request into one category.

education
medical
governance
general

User query: {text}

Return only the category name.
"""

    topic = conversation_agent.llm.call(classification_prompt).strip().lower()

    print("Detected topic:", topic)

    # ---------- Final Prompt with RAG ----------
    final_prompt = f"""
Use the following knowledge if relevant.

Context:
{context}

Question:
{text}

Answer clearly and briefly.
"""

    # ---------- Agent Routing ----------
    if "education" in topic:
        response = education_agent.llm.call(final_prompt)

    elif "medical" in topic:
        response = medical_agent.llm.call(final_prompt)

    elif "governance" in topic:
        response = governance_agent.llm.call(final_prompt)

    else:
        response = conversation_agent.llm.call(final_prompt)

    print("Assistant:", response)

    # ---------- Text to Speech ----------
    audio = generate_audio(response)

    return Response(audio, mimetype="audio/wav")


# ---------- Run Server ----------
if __name__ == "__main__":
    app.run(port=5000)