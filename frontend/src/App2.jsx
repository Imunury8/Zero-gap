import React, { useState, useRef } from 'react'; // useRef 추가
import axios from 'axios';
import { AlertCircle, Activity, PhoneCall, CheckCircle, Upload, Mic } from 'lucide-react';
import AudioRecorder from './component/AudioRecorder';

function App() {
    const [loading, setLoading] = useState(false);
    const [result, setResult] = useState(null);
    const [recordedFile, setRecordedFile] = useState(null);
    const fileInputRef = useRef(null); // 파일 인풋에 접근하기 위한 ref

    // 파일 선택 핸들러
    const handleFileChange = (e) => {
        const file = e.target.files[0];
        if (file) {
            setRecordedFile(file); // 녹음 파일과 동일한 상태에 저장
            setResult(null); // 새 파일이 들어오면 이전 결과 초기화
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
            // 백엔드 명세에 맞춰 'file' 키로 파일 전송
            formData.append('file', recordedFile, recordedFile.name || 'emergency_call.wav');
            formData.append('text', "음성 파일 기반 분석 요청");

            const response = await axios.post('http://localhost:8000/analyze', formData);
            setResult(response.data.result);
        } catch (error) {
            console.error("분석 실패:", error);
            alert("서버 통신 실패. 백엔드 상태를 확인하세요.");
        } finally {
            setLoading(false);
        }
    };

    return (
        <div className="min-h-screen bg-slate-950 text-slate-100 p-6 font-sans">
            <header className="flex justify-between items-center mb-8 border-b border-slate-800 pb-4">
                <div className="flex items-center gap-3">
                    <Activity className="text-red-500 animate-pulse" size={32} />
                    <h1 className="text-2xl font-black tracking-tighter">ZERO-GAP 119 DISPATCH</h1>
                </div>
                <div className="text-sm font-mono text-slate-400">SERVER: <span className="text-green-500 font-bold">ONLINE</span></div>
            </header>

            <main className="grid grid-cols-1 lg:grid-cols-3 gap-6">
                <div className="bg-slate-900 p-6 rounded-2xl border border-slate-800 shadow-xl flex flex-col gap-4">
                    <h2 className="flex items-center gap-2 text-lg font-bold mb-2">
                        <PhoneCall size={20} className="text-blue-400" /> 접수 및 분석
                    </h2>

                    {/* 1. 마이크 녹음 영역 */}
                    <div className="p-4 bg-slate-950/50 rounded-xl border border-slate-800">
                        <p className="text-xs text-slate-500 mb-3 font-bold uppercase tracking-widest">Method 1: 실시간 녹음</p>
                        <AudioRecorder onRecordingComplete={(file) => setRecordedFile(file)} />
                    </div>

                    <div className="relative py-2 flex items-center">
                        <div className="flex-grow border-t border-slate-800"></div>
                        <span className="flex-shrink mx-4 text-slate-600 text-xs font-bold">OR</span>
                        <div className="flex-grow border-t border-slate-800"></div>
                    </div>

                    {/* 2. 파일 업로드 영역 */}
                    <div className="p-4 bg-slate-950/50 rounded-xl border border-slate-800">
                        <p className="text-xs text-slate-500 mb-3 font-bold uppercase tracking-widest">Method 2: 파일 업로드</p>
                        <input
                            type="file"
                            ref={fileInputRef}
                            onChange={handleFileChange}
                            className="hidden"
                            accept="audio/*"
                        />
                        <button
                            onClick={() => fileInputRef.current.click()}
                            className="w-full py-3 px-4 bg-slate-800 hover:bg-slate-700 rounded-lg border border-slate-700 flex items-center justify-center gap-2 transition-all"
                        >
                            <Upload size={18} />
                            <span className="text-sm font-medium">음성 파일 선택 (.wav, .mp3)</span>
                        </button>
                        {recordedFile && !recordedFile.blob && (
                            <p className="mt-2 text-xs text-blue-400 truncate text-center">
                                📁 선택됨: {recordedFile.name}
                            </p>
                        )}
                    </div>

                    <div className="mt-auto pt-4">
                        <button
                            onClick={analyzeEmergency}
                            disabled={loading || !recordedFile}
                            className={`w-full py-4 rounded-xl font-black transition-all ${loading || !recordedFile ? 'bg-slate-800 text-slate-600' : 'bg-red-600 hover:bg-red-500 text-white shadow-[0_0_20px_rgba(220,38,38,0.2)]'
                                }`}
                        >
                            {loading ? '데이터 처리 중...' : '신고 데이터 분석 실행'}
                        </button>
                    </div>
                </div>

                {/* 결과창 (이전과 동일) */}
                <div className="lg:col-span-2">
                    {result ? (
                        /* 결과 UI 섹션 */
                        <div className={`p-8 rounded-2xl border-2 ${result.urgency === '상' ? 'border-red-500 bg-red-950/10' : 'border-slate-800 bg-slate-900'}`}>
                            {/* (기존의 결과 UI 코드 유지) */}
                            <h3 className="text-5xl font-black mb-4">PRIORITY: {result.code}</h3>
                            <div className="grid grid-cols-3 gap-4">
                                <div className="bg-slate-950 p-4 rounded-xl border border-slate-800">
                                    <p className="text-xs text-slate-500">상 확률</p>
                                    <p className="text-2xl font-mono text-red-500">{(result.probability[0] * 100).toFixed(1)}%</p>
                                </div>
                                {/* ... 중/하 확률 추가 ... */}
                            </div>
                        </div>
                    ) : (
                        <div className="h-full min-h-[400px] flex flex-col items-center justify-center bg-slate-900/50 rounded-3xl border-2 border-dashed border-slate-800 text-slate-600">
                            <CheckCircle size={48} className="mb-4 opacity-20" />
                            <p>데이터 전송 대기 중...</p>
                        </div>
                    )}
                </div>
            </main>
        </div>
    );
}

export default App;