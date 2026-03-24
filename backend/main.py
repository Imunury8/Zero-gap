import os
import uvicorn
import numpy as np
import librosa
import joblib
import shutil
from fastapi import FastAPI, File, UploadFile, Form, HTTPException
from fastapi.middleware.cors import CORSMiddleware

# 🎯 XGBoost와 Sklearn 필수 임포트
from xgboost import XGBClassifier
from sklearn.preprocessing import StandardScaler
from sklearn.feature_extraction.text import TfidfVectorizer

# 🎯 별도 모듈: 응급 상황 텍스트 분석 (요약/태그 생성용)
try:
    from emergency_analysis import analyze_emergency_text
except ImportError:
    # 모듈이 없을 경우를 대비한 더미 함수 (에러 방지용)
    def analyze_emergency_text(text, audio_path=None):
        return {"summary": "분석 모듈 로드 실패", "tags": "N/A"}

app = FastAPI()

# CORS 설정
origins = [
    "http://localhost:5173",
    "http://localhost:3000",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ==========================================
# 1. 모델 패키지 로드 (서버 시작 시 1회)
# ==========================================
# 노트북에서 저장한 파일명: zero_gap_engine_final.pkl
MODEL_PATH = "./models/zero_gap_engine_final.pkl"

# 전역 변수 초기화
model_pack = None
model = None
scaler = None
tfidf = None
THRESHOLDS = {'high_t': 0.5, 'mid_t': 0.3} # 기본값
AUDIO_WEIGHT = 1.0

try:
    if os.path.exists(MODEL_PATH):
        print(f"📦 모델 패키지 로딩 중... ({MODEL_PATH})")
        model_pack = joblib.load(MODEL_PATH)
        
        # 딕셔너리 언패킹 (Notebook Cell 8 참조)
        model = model_pack['model']
        scaler = model_pack['scaler']
        tfidf = model_pack['tfidf']
        THRESHOLDS = model_pack['thresholds']
        AUDIO_WEIGHT = model_pack.get('audio_weight', 5.0) # 노트북 저장값인 5.0 사용
        
        print(f"✅ 로드 완료!")
        print(f"   - 임계값: 상({THRESHOLDS['high_t']}), 중({THRESHOLDS['mid_t']})")
        print(f"   - 오디오 가중치: {AUDIO_WEIGHT}")
        print(f"   - 텍스트 벡터: {len(tfidf.get_feature_names_out())} 차원")
        
    else:
        print(f"🚨 모델 파일을 찾을 수 없습니다: {MODEL_PATH}")

except Exception as e:
    print(f"🚨 모델 로드 중 치명적 에러: {e}")

# ==========================================
# 2. 특징 추출 함수 (노트북 로직 재현)
# ==========================================
def extract_audio_features(file_path):
    """
    노트북의 오디오 전처리 로직을 재현합니다.
    - 기본 41개 특징 추출 (MFCC 40 + RMS 1 가정)
    - Jitter/Shimmer 자리를 위한 0 padding (2개) 추가 -> 총 43개
    """
    try:
        # 16kHz 로드
        y, sr = librosa.load(file_path, sr=16000)

        # 1. MFCC (40개)
        mfcc = librosa.feature.mfcc(y=y, sr=sr, n_mfcc=40)
        mfcc_mean = np.mean(mfcc.T, axis=0)
        
        # 2. RMS (1개) - 에너지/음량 관련
        rms = np.mean(librosa.feature.rms(y=y))
        
        # 기본 41개 특징 결합
        base_features = np.hstack([mfcc_mean, rms])
        
        # 3. Padding (Jitter/Shimmer 자리 2개 0으로 채움 - Notebook Cell 4 참조)
        # notebook: np.hstack([X_train_audio, np.zeros((..., 2))])
        padding = np.zeros(2)
        
        # 최종 43개 특징 (1, 43) 형태로 반환
        final_audio_feats = np.hstack([base_features, padding]).reshape(1, -1)
        
        return final_audio_feats

    except Exception as e:
        print(f"오디오 특징 추출 실패: {e}")
        return None

# ==========================================
# 3. 통합 분석 API
# ==========================================
@app.post("/analyze")
async def analyze_call(file: UploadFile = File(...), text: str = Form(...)):
    if model is None:
        raise HTTPException(status_code=500, detail="서버에 모델이 로드되지 않았습니다.")

    temp_path = f"temp_{file.filename}"
    try:
        # 1. 파일 임시 저장
        with open(temp_path, "wb") as f:
            shutil.copyfileobj(file.file, f)

        # ---------------------------------------------------------
        # [Step 1] 오디오 처리 (Notebook Cell 4 로직)
        # ---------------------------------------------------------
        raw_audio = extract_audio_features(temp_path) # (1, 43)
        if raw_audio is None:
            raise HTTPException(status_code=400, detail="오디오 처리 실패")
            
        # 스케일링 적용
        scaled_audio = scaler.transform(raw_audio)
        
        # 가중치 증폭 (Notebook: * 2.0 또는 * 5.0)
        weighted_audio = scaled_audio * AUDIO_WEIGHT

        # ---------------------------------------------------------
        # [Step 2] 텍스트 처리 (TF-IDF)
        # ---------------------------------------------------------
        # 텍스트가 비어있으면 기본값 처리
        input_text = text if text.strip() else "내용 없음"
        
        # TF-IDF 변환 (1, 1000)
        text_vector = tfidf.transform([input_text]).toarray()

        # ---------------------------------------------------------
        # [Step 3] 특징 결합 (오디오 + 텍스트)
        # ---------------------------------------------------------
        # (1, 43) + (1, 1000) -> (1, 1043)
        final_features = np.hstack([weighted_audio, text_vector])

        # ---------------------------------------------------------
        # [Step 4] 모델 예측 및 커스텀 임계값 적용 (Notebook Cell 7 참조)
        # ---------------------------------------------------------
        probs = model.predict_proba(final_features)[0] # [prob_상, prob_중, prob_하] 아님! (모델 클래스 순서 확인 필요)
        # XGBoost의 classes_ 확인 (보통 [0, 1, 2] -> 상, 중, 하)
        
        # 확률 추출
        prob_sang = probs[0] # Class 0
        prob_jung = probs[1] # Class 1
        prob_ha   = probs[2] # Class 2

        # 최적화된 임계값 적용 로직
        if prob_sang >= THRESHOLDS['high_t']:
            urgency_idx = 0
            urgency_label = "상"
            code = "CRITICAL"
            color = "red"
        elif prob_jung >= THRESHOLDS['mid_t']:
            urgency_idx = 1
            urgency_label = "중"
            code = "WARNING"
            color = "orange"
        else:
            urgency_idx = 2
            urgency_label = "하"
            code = "NORMAL"
            color = "green"

        # ---------------------------------------------------------
        # [Step 5] 추가 분석 정보 생성 (LLM/Rule-based)
        # ---------------------------------------------------------
        # 요청하신 emergency_analysis.py 활용 (오디오 경로 전달)
        analysis_result = analyze_emergency_text(input_text, audio_path=temp_path)

        # 결과 반환
        return {
            "status": "success",
            "result": {
                "urgency": urgency_label,
                "code": code,
                "color": color,
                "probability": [float(prob_sang), float(prob_jung), float(prob_ha)],
                "stt_text": analysis_result.get("full_text", input_text), # 📝 STT 결과 우선 사용
                "analysis": {
                    "summary": analysis_result.get("summary", "요약 없음"),
                    "tags": analysis_result.get("tags", ""),
                    "full_text": analysis_result.get("full_text", input_text)
                }
            }
        }

    except Exception as e:
        print(f"에러 발생: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))
        
    finally:
        # 임시 파일 삭제
        if os.path.exists(temp_path):
            os.remove(temp_path)

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)