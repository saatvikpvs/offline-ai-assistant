import subprocess
import os


MODEL_PATH = "models/en_US-lessac-high.onnx"
OUTPUT_FILE = "output.wav"


def speak(text):

    print("\nAssistant:", text)

    # Generate speech using Piper
    process = subprocess.Popen(
        ["piper", "--model", MODEL_PATH, "--output_file", OUTPUT_FILE],
        stdin=subprocess.PIPE
    )

    process.communicate(text.encode())

    # Play audio (Windows)
    os.system(f"start {OUTPUT_FILE}")