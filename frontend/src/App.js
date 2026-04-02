
import { useState } from "react";
import AvatarViewer from "./components/AvatarViewer";

function App() {

  const [greeted, setGreeted] = useState(false);
  const [audioElement, setAudioElement] = useState(null);
  const [recording, setRecording] = useState(false);

  // ---- VRM Avatar List ----
  const avatars = [
    "/3841841720510957418.vrm",
    "/8329890252317737768.vrm"
  ];

  const [avatarIndex, setAvatarIndex] = useState(0);

  const nextAvatar = () => {
    setAvatarIndex((avatarIndex + 1) % avatars.length);
  };

  const prevAvatar = () => {
    setAvatarIndex((avatarIndex - 1 + avatars.length) % avatars.length);
  };

  async function speak() {

    try {

      if (!greeted) {

        const greet = await fetch("http://localhost:5000/greet");
        const greetBlob = await greet.blob();

        const greetAudio = new Audio(URL.createObjectURL(greetBlob));
        await greetAudio.play();

        setGreeted(true);
      }

      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });

      const recorder = new MediaRecorder(stream);
      let chunks = [];

      setRecording(true);

      recorder.ondataavailable = (e) => {
        chunks.push(e.data);
      };

      recorder.onstop = async () => {

        setRecording(false);

        const blob = new Blob(chunks, { type: "audio/webm" });

        const formData = new FormData();
        formData.append("audio", blob);

        const response = await fetch("http://localhost:5000/voice", {
          method: "POST",
          body: formData
        });

        if (response.status === 204) {
          console.log("No speech detected");
          return;
        }

        const audioBlob = await response.blob();
        const audio = new Audio(URL.createObjectURL(audioBlob));

        setAudioElement(audio);

        audio.play();
      };

      recorder.start();

      setTimeout(() => {
        if (recorder.state !== "inactive") recorder.stop();
      }, 8000);

    } catch (error) {

      console.error("Microphone error:", error);
      alert("Microphone permission required");

    }
  }

  return (
    <div style={{textAlign:"center"}}>

      <h2>AI Avatar Assistant</h2>

      {/* Avatar Selector */}
      <div style={{marginBottom:"10px"}}>
        <button onClick={prevAvatar}>◀</button>
        <span style={{margin:"0 10px"}}>Avatar {avatarIndex + 1}</span>
        <button onClick={nextAvatar}>▶</button>
      </div>

      <button onClick={speak} disabled={recording}>
        {recording ? "🎙 Listening..." : "🎤 Speak"}
      </button>

      <AvatarViewer
        avatar={avatars[avatarIndex]}
        audio={audioElement}
      />

    </div>
  );
}

export default App;

