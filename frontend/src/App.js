import React, { useState, useRef, Suspense, useEffect, useCallback } from "react";
import { Canvas } from "@react-three/fiber";
import { OrbitControls, Stars, Grid } from "@react-three/drei";
import Robot from "./Robot";
import "./App.css";

// ---------- Helper: Build WAV blob from raw PCM samples ----------
function encodeWAV(samples, sampleRate) {
  const buffer = new ArrayBuffer(44 + samples.length * 2);
  const view = new DataView(buffer);

  function writeString(offset, str) {
    for (let i = 0; i < str.length; i++) view.setUint8(offset + i, str.charCodeAt(i));
  }

  writeString(0, "RIFF");
  view.setUint32(4, 36 + samples.length * 2, true);
  writeString(8, "WAVE");
  writeString(12, "fmt ");
  view.setUint32(16, 16, true);
  view.setUint16(20, 1, true);
  view.setUint16(22, 1, true);
  view.setUint32(24, sampleRate, true);
  view.setUint32(28, sampleRate * 2, true);
  view.setUint16(32, 2, true);
  view.setUint16(34, 16, true);
  writeString(36, "data");
  view.setUint32(40, samples.length * 2, true);

  for (let i = 0; i < samples.length; i++) {
    const s = Math.max(-1, Math.min(1, samples[i]));
    view.setInt16(44 + i * 2, s < 0 ? s * 0x8000 : s * 0x7FFF, true);
  }

  return new Blob([view], { type: "audio/wav" });
}

function App() {
  const [modelPath, setModelPath] = useState("/models/bot.vrm");
  const [action, setAction] = useState("idle");
  const [isRecording, setIsRecording] = useState(false);
  const [messages, setMessages] = useState([]);       // chat history
  const [textInput, setTextInput] = useState("");      // text input field
  const [isSending, setIsSending] = useState(false);   // disable input while processing

  // Recording refs
  const streamRef = useRef(null);
  const audioCtxRef = useRef(null);
  const processorRef = useRef(null);
  const recordedChunks = useRef([]);
  const chatEndRef = useRef(null);

  // Auto-scroll chat to bottom
  useEffect(() => {
    if (chatEndRef.current) {
      chatEndRef.current.scrollIntoView({ behavior: "smooth" });
    }
  }, [messages]);

  // ---------- Auto-greet on load ----------
  useEffect(() => {
    const fetchGreeting = async () => {
      try {
        const res = await fetch("http://localhost:5000/greet");
        if (res.ok) {
          const audioBlob = await res.blob();
          const sound = new Blob([audioBlob], { type: "audio/wav" });
          const audioUrl = URL.createObjectURL(sound);
          const audio = new Audio(audioUrl);
          audio.play().catch(() => { });
          setAction("wave");
          audio.onended = () => setAction("idle");
          setMessages([{ role: "ai", text: "Hey, I am your AI assistant. How can I help you today?" }]);
        }
      } catch (err) {
        console.error("Greet error", err);
        setMessages([{ role: "ai", text: "Backend unreachable. Please make sure the server is running." }]);
      }
    };
    fetchGreeting();
  }, []);

  // ---------- Shared SSE stream handler ----------
  // skipUserText: true when called from sendText (user msg already added)
  const handleSSEStream = useCallback(async (res, skipUserText = false) => {
    const reader = res.body.getReader();
    const decoder = new TextDecoder();
    let sseBuffer = "";
    const audioQueue = [];
    let isPlaying = false;
    let aiTextParts = [];
    let aiMsgAdded = false;

    const playNext = () => {
      if (audioQueue.length === 0) {
        isPlaying = false;
        setAction("idle");
        return;
      }
      isPlaying = true;
      const b64 = audioQueue.shift();
      const audio = new Audio("data:audio/wav;base64," + b64);
      audio.onended = playNext;
      audio.onerror = () => playNext();
      audio.play().catch(() => playNext());
    };

    while (true) {
      const { done, value } = await reader.read();
      if (done) break;

      sseBuffer += decoder.decode(value, { stream: true });

      while (sseBuffer.includes("\n\n")) {
        const idx = sseBuffer.indexOf("\n\n");
        const eventBlock = sseBuffer.substring(0, idx);
        sseBuffer = sseBuffer.substring(idx + 2);

        if (eventBlock.startsWith("data:")) {
          try {
            const data = JSON.parse(eventBlock.substring(5));

            // User text from voice transcription
            if (data.userText && !skipUserText) {
              setMessages(prev => [...prev, { role: "user", text: data.userText }]);
              continue;
            }
            if (data.userText && skipUserText) continue;

            // Done signal
            if (data.done) {
              continue;
            }

            // Audio + text chunk
            if (data.audio) {
              audioQueue.push(data.audio);
              setAction("talk");
              if (!isPlaying) playNext();
            }
            // Build AI text response live in chat
            if (data.text) {
              aiTextParts.push(data.text);
              const currentText = aiTextParts.join(" ");
              if (!aiMsgAdded) {
                aiMsgAdded = true;
                setMessages(prev => [...prev, { role: "ai", text: currentText }]);
              } else {
                // Update the last AI message with accumulated text
                setMessages(prev => {
                  const updated = [...prev];
                  updated[updated.length - 1] = { role: "ai", text: currentText };
                  return updated;
                });
              }
            }
          } catch (e) {
            console.error("SSE parse error:", e);
          }
        }
      }
    }
  }, []);

  // ---------- Send recorded WAV to backend ----------
  const sendAudio = useCallback(async (wavBlob) => {
    try {
      setIsSending(true);
      const formData = new FormData();
      formData.append("audio", wavBlob, "recording.wav");

      const res = await fetch("http://localhost:5000/voice", {
        method: "POST",
        body: formData
      });

      if (res.status === 204) {
        setMessages(prev => [...prev, { role: "ai", text: "No speech detected. Please try again." }]);
        return;
      }
      if (!res.ok) return;

      await handleSSEStream(res);
    } catch (err) {
      console.error("Error sending audio:", err);
    } finally {
      setIsSending(false);
    }
  }, [handleSSEStream]);

  // ---------- Send text input to backend ----------
  const sendText = useCallback(async () => {
    const text = textInput.trim();
    if (!text) return;

    setTextInput("");
    setIsSending(true);
    setMessages(prev => [...prev, { role: "user", text }]);

    try {
      const res = await fetch("http://localhost:5000/text", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ text })
      });

      if (res.status === 204) return;
      if (!res.ok) return;

      await handleSSEStream(res, true);  // skip userText, already added above
    } catch (err) {
      console.error("Error sending text:", err);
      setMessages(prev => [...prev, { role: "ai", text: "Error: Could not reach server." }]);
    } finally {
      setIsSending(false);
    }
  }, [textInput, handleSSEStream]);

  // ---------- Handle Enter key ----------
  const handleKeyDown = (e) => {
    if (e.key === "Enter" && !isSending) {
      sendText();
    }
  };

  // ---------- Start recording ----------
  const startRecording = async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      streamRef.current = stream;
      const audioCtx = new (window.AudioContext || window.webkitAudioContext)({ sampleRate: 16000 });
      audioCtxRef.current = audioCtx;
      const source = audioCtx.createMediaStreamSource(stream);
      const processor = audioCtx.createScriptProcessor(4096, 1, 1);
      processorRef.current = processor;
      recordedChunks.current = [];

      processor.onaudioprocess = (e) => {
        recordedChunks.current.push(new Float32Array(e.inputBuffer.getChannelData(0)));
      };

      source.connect(processor);
      processor.connect(audioCtx.destination);
      setIsRecording(true);
    } catch (err) {
      console.error("Microphone error:", err);
    }
  };

  // ---------- Stop recording & send ----------
  const stopRecording = async () => {
    if (!isRecording) return;
    setIsRecording(false);

    if (processorRef.current) { processorRef.current.disconnect(); processorRef.current = null; }
    if (audioCtxRef.current) { await audioCtxRef.current.close(); audioCtxRef.current = null; }
    if (streamRef.current) { streamRef.current.getTracks().forEach(t => t.stop()); streamRef.current = null; }

    const totalLength = recordedChunks.current.reduce((acc, c) => acc + c.length, 0);
    if (totalLength < 8000) return;

    const merged = new Float32Array(totalLength);
    let offset = 0;
    for (const chunk of recordedChunks.current) {
      merged.set(chunk, offset);
      offset += chunk.length;
    }

    await sendAudio(encodeWAV(merged, 16000));
  };

  const toggleRecording = () => {
    if (isRecording) stopRecording();
    else startRecording();
  };

  return (
    <div className="App">
      <button
        className="swap-button"
        onClick={() => setModelPath(prev => prev === "/models/bot1.vrm" ? "/models/bot.vrm" : "/models/bot1.vrm")}
      >
        🔄 Change Avatar
      </button>
      {/* ---------- 3D Robot Scene ---------- */}
      <Canvas camera={{ position: [0, 1.2, 3], fov: 45 }}>
        <color attach="background" args={["#0a0a0f"]} />
        <Suspense fallback={null}>
          <Robot action={action} modelPath={modelPath} />
          <Stars />
          <Grid infiniteGrid cellSize={0.5} sectionSize={1} />
        </Suspense>
        <ambientLight intensity={0.6} />
        <pointLight position={[5, 5, 5]} intensity={2} />
        <OrbitControls target={[0, 1, 0]} />
      </Canvas>

      {/* ---------- Chat Panel ---------- */}
      <div className="chat-panel">
        <div className="chat-header">💬 CONVERSATION</div>

        <div className="chat-messages">
          {messages.map((msg, i) => (
            <div key={i} className={`chat-msg ${msg.role}`}>
              <span className="chat-role">{msg.role === "user" ? "You" : "AI"}</span>
              <span className="chat-text">{msg.text}</span>
            </div>
          ))}
          <div ref={chatEndRef} />
        </div>

        {/* ---------- Text Input ---------- */}
        <div className="chat-input-row">
          <input
            className="chat-input"
            type="text"
            placeholder={isSending ? "Thinking..." : "Type your question..."}
            value={textInput}
            onChange={(e) => setTextInput(e.target.value)}
            onKeyDown={handleKeyDown}
            disabled={isSending}
          />
          <button
            className="chat-send"
            onClick={sendText}
            disabled={isSending || !textInput.trim()}
          >
            ➤
          </button>
        </div>

        {/* ---------- Voice Button ---------- */}
        <button
          className={`speak ${isRecording ? "recording" : ""}`}
          onClick={toggleRecording}
          disabled={isSending && !isRecording}
        >
          {isRecording ? "🎤 CLICK TO STOP" : "🎙️ CLICK TO SPEAK"}
        </button>
      </div>

    </div>
  );
}

export default App;