
from flask import Flask, request, Response
from flask_cors import CORS
from faster_whisper import WhisperModel
import subprocess
import io
import wave

from agents.conversation_agent import create_conversation_agent
from agents.education_agent import create_education_agent
from agents.medical_agent import create_medical_agent
from agents.governance_agent import create_governance_agent


app = Flask(__name__)
CORS(app)

# Whisper model (fast)
model = WhisperModel("tiny")

# Agents
conversation_agent = create_conversation_agent()
education_agent = create_education_agent()
medical_agent = create_medical_agent()
governance_agent = create_governance_agent()


# ---------- Greeting route ----------
@app.route("/greet", methods=["GET"])
def greet():

    greeting = "Hey, I am your AI assistant. How can I help you today?"

    process = subprocess.Popen(
        ["piper", "--model", "models/en_US-lessac-high.onnx", "--output-raw"],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE
    )

    audio_bytes, _ = process.communicate(greeting.encode())

    wav_buffer = io.BytesIO()

    with wave.open(wav_buffer, "wb") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(22050)
        wf.writeframes(audio_bytes)

    wav_buffer.seek(0)

    return Response(wav_buffer.read(), mimetype="audio/wav")


# ---------- Voice route ----------
@app.route("/voice", methods=["POST"])
def voice():

    print("Voice request received")

    audio_file = request.files["audio"]
    audio_file.save("input.webm")

    segments, _ = model.transcribe(
        "input.webm",
        beam_size=5,
        vad_filter=True
    )

    text = " ".join([segment.text for segment in segments]).strip()

    if text == "":
        print("No speech detected")
        return Response(status=204)

    print("User said:", text)

    # ---------- Classification ----------
    prompt = f"""
Classify the user request into one category.

education
medical
governance
general

User query: {text}

Return only the category name.
"""

    topic = conversation_agent.llm.call(prompt).strip().lower()

    print("Detected topic:", topic)

    # ---------- Routing ----------
    if "education" in topic:
        response = education_agent.llm.call(text)

    elif "medical" in topic:
        response = medical_agent.llm.call(text)

    elif "governance" in topic:
        response = governance_agent.llm.call(text)

    else:
        response = conversation_agent.llm.call(text)

    print("Assistant:", response)

    # ---------- TTS ----------
    process = subprocess.Popen(
        ["piper", "--model", "models/en_US-lessac-high.onnx", "--output-raw"],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE
    )

    audio_bytes, _ = process.communicate(response.encode())

    wav_buffer = io.BytesIO()

    with wave.open(wav_buffer, "wb") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(22050)
        wf.writeframes(audio_bytes)

    wav_buffer.seek(0)

    return Response(wav_buffer.read(), mimetype="audio/wav")


if __name__ == "__main__":
    app.run(port=5000)

