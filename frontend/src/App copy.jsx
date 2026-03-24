import React, { useState, useRef } from 'react';
import axios from 'axios';
import { AlertCircle, Activity, PhoneCall, CheckCircle, Upload, MessageSquare, ShieldAlert } from 'lucide-react';
import AudioRecorder from './component/AudioRecorder';

function App() {
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState(null);
  const [recordedFile, setRecordedFile] = useState(null);
  const [inputText, setInputText] = useState(""); // 🎯 텍스트 상태 추가
  const fileInputRef = useRef(null);

  const handleFileChange = (e) => {
    const file = e.target.files[0];
    if (file) {
      setRecordedFile(file);
      setResult(null);
    }
  };

  const analyzeEmergency = async () => {
    if (!recordedFile) {
      alert("데이터가 없습니다. 녹음을 하거나 파일을 업로드해주세요!");
      return;
    }

    setLoading(true);
    try {
      const formData = new FormData();
      // 백엔드 명세: file(파일), text(문자열)
      formData.append('file', recordedFile, recordedFile.name || 'emergency_call.wav');
      formData.append('text', inputText || "텍스트 정보 없음"); // 🎯 입력된 텍스트 전송

      const response = await axios.post('http://localhost:8000/analyze', formData);
      setResult(response.data.result);
    } catch (error) {
      console.error("분석 실패:", error);
      alert("서버 통신 실패. 백엔드(Wav2Vec 2.0) 상태를 확인하세요.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 p-6 font-sans">
      <header className="flex justify-between items-center mb-8 border-b border-slate-800 pb-4">
        <div className="flex items-center gap-3">
          <Activity className="text-red-500 animate-pulse" size={32} />
          <h1 className="text-2xl font-black tracking-tighter italic">ZERO-GAP 119 DISPATCH</h1>
        </div>
        <div className="flex items-center gap-4">
          <div className="text-xs font-mono text-slate-400">MODEL: <span className="text-blue-400 font-bold">Wav2Vec-2.0-v2.5</span></div>
          <div className="text-xs font-mono text-slate-400">SERVER: <span className="text-green-500 font-bold">ONLINE</span></div>
        </div>
      </header>

      <main className="grid grid-cols-1 lg:grid-cols-3 gap-8">
        {/* 왼쪽: 컨트롤 섹션 */}
        <div className="bg-slate-900 p-6 rounded-2xl border border-slate-800 shadow-2xl flex flex-col gap-6">
          <h2 className="flex items-center gap-2 text-lg font-bold">
            <PhoneCall size={20} className="text-blue-400" /> 접수 데이터 입력
          </h2>

          {/* 1. 음성 입력 (녹음/업로드) */}
          <div className="space-y-4">
            <div className="p-4 bg-slate-950/50 rounded-xl border border-slate-800">
              <p className="text-[10px] text-slate-500 mb-3 font-bold uppercase tracking-widest">Method 1: Voice Recording</p>
              <AudioRecorder onRecordingComplete={(file) => setRecordedFile(file)} />
            </div>

            <div className="p-4 bg-slate-950/50 rounded-xl border border-slate-800">
              <p className="text-[10px] text-slate-500 mb-3 font-bold uppercase tracking-widest">Method 2: File Upload</p>
              <input type="file" ref={fileInputRef} onChange={handleFileChange} className="hidden" accept="audio/*" />
              <button onClick={() => fileInputRef.current.click()} className="w-full py-3 bg-slate-800 hover:bg-slate-700 rounded-lg border border-slate-700 flex items-center justify-center gap-2 transition-all">
                <Upload size={18} />
                <span className="text-sm">파일 선택 (.wav)</span>
              </button>
              {recordedFile && !recordedFile.blob && <p className="mt-2 text-xs text-blue-400 text-center">📁 {recordedFile.name}</p>}
            </div>
          </div>

          {/* 2. 텍스트 입력 (STT 보정용) 🎯 추가됨 */}
          <div className="p-4 bg-slate-950/50 rounded-xl border border-slate-800">
            <p className="text-[10px] text-slate-500 mb-3 font-bold uppercase tracking-widest">Method 3: STT / Text Info</p>
            <div className="flex items-center gap-2 bg-slate-900 p-2 rounded-lg border border-slate-700">
              <MessageSquare size={16} className="text-slate-500" />
              <input
                type="text"
                value={inputText}
                onChange={(e) => setInputText(e.target.value)}
                placeholder="신고 내용 입력 (키워드 보정용)"
                className="bg-transparent border-none outline-none text-sm w-full text-slate-200"
              />
            </div>
          </div>

          <button
            onClick={analyzeEmergency}
            disabled={loading || !recordedFile}
            className={`w-full py-4 rounded-xl font-black text-lg transition-all ${loading || !recordedFile ? 'bg-slate-800 text-slate-600' : 'bg-red-600 hover:bg-red-500 text-white shadow-[0_0_30px_rgba(220,38,38,0.3)]'
              }`}
          >
            {loading ? 'ANALYZING...' : '분석 실행'}
          </button>
        </div>

        {/* 오른쪽: 분석 결과 섹션 */}
        <div className="lg:col-span-2">
          {result ? (
            <div className={`h-full p-10 rounded-3xl border-2 transition-all duration-500 ${result.urgency === '상' ? 'border-red-600 bg-red-950/10 shadow-[0_0_50px_rgba(220,38,38,0.1)]' : 'border-slate-800 bg-slate-900'}`}>
              <div className="flex justify-between items-start mb-8">
                <div>
                  <p className="text-sm font-bold text-slate-500 uppercase tracking-widest mb-1">Emergency Level</p>
                  <h3 className={`text-7xl font-black ${result.urgency === '상' ? 'text-red-500' : result.urgency === '중' ? 'text-orange-500' : 'text-green-500'}`}>
                    {result.code}
                  </h3>
                </div>
                {result.urgency === '상' && <ShieldAlert size={64} className="text-red-500 animate-bounce" />}
              </div>

              <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
                {['상', '중', '하'].map((label, idx) => (
                  <div key={label} className="bg-slate-950/80 p-6 rounded-2xl border border-slate-800">
                    <p className="text-xs text-slate-500 font-bold mb-2">{label} 확률</p>
                    <p className={`text-3xl font-mono font-bold ${idx === 0 ? 'text-red-500' : idx === 1 ? 'text-orange-500' : 'text-green-500'}`}>
                      {(result.probability[idx] * 100).toFixed(1)}%
                    </p>
                    <div className="w-full bg-slate-800 h-1.5 mt-3 rounded-full overflow-hidden">
                      <div className={`h-full transition-all duration-1000 ${idx === 0 ? 'bg-red-500' : idx === 1 ? 'bg-orange-500' : 'bg-green-500'}`} style={{ width: `${result.probability[idx] * 100}%` }}></div>
                    </div>
                  </div>
                ))}
              </div>

              <div className="p-6 bg-slate-950 rounded-2xl border border-slate-800">
                <p className="text-xs text-slate-500 font-bold mb-3 uppercase">분석 텍스트 (STT 기반)</p>
                <p className="text-lg text-slate-300 italic">
                  "{result.analysis?.full_text || result.stt_text}"
                </p>
              </div>

              {/* 추가된 분석 결과 (요약 및 태그) */}
              {result.analysis && (
                <div className="mt-6 grid grid-cols-1 md:grid-cols-2 gap-6">
                  <div className="p-6 bg-slate-950 rounded-2xl border border-slate-800">
                    <p className="text-xs text-slate-500 font-bold mb-3 uppercase text-blue-400">📋 AI 상황 요약</p>
                    <p className="text-slate-300 font-medium leading-relaxed">
                      {result.analysis.summary || "요약 정보 없음"}
                    </p>
                  </div>
                  <div className="p-6 bg-slate-950 rounded-2xl border border-slate-800">
                    <p className="text-xs text-slate-500 font-bold mb-3 uppercase text-purple-400">🏷️ 응급 태그</p>
                    <div className="flex flex-wrap gap-2">
                      {result.analysis.tags ? (
                        result.analysis.tags.split(' ').map((tag, i) => (
                          <span key={i} className="px-3 py-1 bg-slate-800 border border-slate-700 rounded-full text-sm text-slate-300">
                            {tag}
                          </span>
                        ))
                      ) : (
                        <span className="text-slate-600 text-sm">태그 없음</span>
                      )}
                    </div>
                  </div>
                </div>
              )}
            </div>
          ) : (
            <div className="h-full min-h-[500px] flex flex-col items-center justify-center bg-slate-900/30 rounded-3xl border-2 border-dashed border-slate-800 text-slate-600">
              <Activity size={64} className="mb-4 opacity-10" />
              <p className="font-bold tracking-widest animate-pulse">AWAITING EMERGENCY DATA...</p>
            </div>
          )}
        </div>
      </main>
    </div>
  );
}

export default App;