import sounddevice as sd
from scipy.io.wavfile import write
from faster_whisper import WhisperModel

model = WhisperModel("base")

def get_user_input():

    print("Speak now...")

    fs = 16000
    duration = 5

    audio = sd.rec(int(duration * fs), samplerate=fs, channels=1)
    sd.wait()

    write("input.wav", fs, audio)

    segments, _ = model.transcribe("input.wav")

    text = ""
    for segment in segments:
        text += segment.text

    print("You said:", text)

    return text