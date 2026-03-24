import React, { useState, useRef } from 'react';

const AudioRecorder = ({ onRecordingComplete }) => {
  const [isRecording, setIsRecording] = useState(false);
  const [audioUrl, setAudioUrl] = useState(null);
  const mediaRecorder = useRef(null);
  const audioChunks = useRef([]);

  // 1. 녹음 시작
  const startRecording = async () => {
    const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
    mediaRecorder.current = new MediaRecorder(stream);
    audioChunks.current = [];

    mediaRecorder.current.ondataavailable = (event) => {
      audioChunks.current.push(event.data);
    };

    mediaRecorder.current.onstop = () => {
      const audioBlob = new Blob(audioChunks.current, { type: 'audio/wav' });
      const url = URL.createObjectURL(audioBlob);
      setAudioUrl(url);
      onRecordingComplete(audioBlob); // 부모 컴포넌트(App.jsx)로 파일 전달
    };

    mediaRecorder.current.start();
    setIsRecording(true);
  };

  // 2. 녹음 중지
  const stopRecording = () => {
    mediaRecorder.current.stop();
    setIsRecording(false);
  };

  return (
    <div className="flex flex-col items-center p-6 bg-slate-900 rounded-xl border border-slate-700 shadow-lg">
      <div className="mb-4">
        {isRecording ? (
          <button onClick={stopRecording} className="bg-red-600 hover:bg-red-700 text-white font-bold py-3 px-6 rounded-full animate-pulse">
            🔴 녹음 중지
          </button>
        ) : (
          <button onClick={startRecording} className="bg-blue-600 hover:bg-blue-700 text-white font-bold py-3 px-6 rounded-full">
            🎙️ 마이크 시작
          </button>
        )}
      </div>

      {audioUrl && (
        <div className="mt-4 w-full">
          <p className="text-sm text-slate-400 mb-2">미리듣기:</p>
          <audio src={audioUrl} controls className="w-full" />
        </div>
      )}
    </div>
  );
};

export default AudioRecorder;