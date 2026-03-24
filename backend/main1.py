import torch
import librosa
import numpy as np
from transformers import Wav2Vec2FeatureExtractor, Wav2Vec2ForSequenceClassification

# 1. 모델 및 추출기 로드 (서버 시작 시 한 번만 실행)
MODEL_PATH = "./models/final_engine"
device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

feature_extractor = Wav2Vec2FeatureExtractor.from_pretrained(MODEL_PATH)
model = Wav2Vec2ForSequenceClassification.from_pretrained(MODEL_PATH).to(device)
model.eval()

def predict_emergency_level(audio_path):
    """
    오디오 파일을 입력받아 상/중/하 등급을 반환합니다.
    """
    try:
        # 1. 오디오 로드 및 16kHz 리샘플링
        speech, _ = librosa.load(audio_path, sr=16000)
        
        # 2. 특징 추출 및 텐서 변환
        inputs = feature_extractor(
            speech, 
            sampling_rate=16000, 
            max_length=80000, 
            truncation=True, 
            padding="max_length", 
            return_tensors="pt"
        ).to(device)
        
        # 3. 모델 추론
        with torch.no_grad():
            logits = model(**inputs).logits
        
        # 4. 결과 해석
        probs = torch.nn.functional.softmax(logits, dim=-1)
        result_idx = torch.argmax(probs, dim=-1).item()
        
        # label2id={'상': 0, '중': 1, '하': 2} 기준
        labels = ['상', '중', '하']
        confidence = probs[0][result_idx].item()
        
        return {
            "priority": labels[result_idx],
            "confidence": round(confidence, 4),
            "probs": {labels[i]: round(probs[0][i].item(), 4) for i in range(3)}
        }
        
    except Exception as e:
        return {"error": str(e)}

@app.post("/analyze")
async def analyze_call(file: UploadFile = File(...), text: str = Form(...)):
    temp_path = f"temp_{file.filename}"
    try:
        # 임시 파일 저장
        with open(temp_path, "wb") as f:
            f.write(await file.read())

        features = preprocess_data(temp_path, text)
        probs = model.predict_proba(features)[0]
    
    # 🎯 텍스트 보정 로직 추가
        if any(word in text for word in CRITICAL_WORDS):
            probs[0] += 0.2  # '상' 확률에 20% 보너스
            probs[2] -= 0.2  # '하' 확률에서 20% 차감
        
        # 보정된 확률로 다시 판단
        if probs[0] >= h_t:
            urgency, color, code = "상", "red", "CRITICAL"
        elif probs[1] >= m_t:
            urgency, color, code = "중", "orange", "WARNING"
        else:
            urgency, color, code = "하", "green", "NORMAL"

        return {
            "status": "success",
            "result": {
                "urgency": urgency,
                "code": code,
                "color": color,
                "probability": probs.tolist(),
                "stt_text": text
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        # 🎯 파일 삭제는 여기서 안전하게 처리
        if os.path.exists(temp_path):
            os.remove(temp_path)

# 🔥 [핵심] 이 부분이 있어야 python main.py 실행 시 서버가 죽지 않고 대기합니다!
if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)