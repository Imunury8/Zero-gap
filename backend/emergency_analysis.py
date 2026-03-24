import torch
import re
import whisper
import imageio_ffmpeg
import os
from transformers import PreTrainedTokenizerFast, BartForConditionalGeneration
from fuzzywuzzy import process

# ⚠️ FFmpeg 경로 주입 (Windows 환경 필수)
os.environ["PATH"] += os.pathsep + os.path.dirname(imageio_ffmpeg.get_ffmpeg_exe())
print(f"DEBUG: ffmpeg path injected. Current PATH includes: {os.path.dirname(imageio_ffmpeg.get_ffmpeg_exe())}")

# ==========================================
# 1. 설정 및 모델 로드 (서버 시작 시 1회 실행)
# ==========================================

# ⚠️ 로컬에 모델이 없다면 HuggingFace Hub의 기본 모델을 사용하거나 경로를 수정하세요.
# 예: ./models/kobart_summary 폴더에 모델이 있어야 합니다.
# 없으면 "gogamza/kobart-summarization" 등을 사용할 수 있습니다.
KOBART_PATH = "./models/final_emergency_model_v2" 
WHISPER_MODEL_SIZE = "small"

print("📦 [Emergency Analysis] 로딩 중... (KoBART + Whisper)")

model = None
tokenizer = None
stt_model = None
device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

try:
    # 1. KoBART 요약 모델 로드
    tokenizer = PreTrainedTokenizerFast.from_pretrained(KOBART_PATH)
    model = BartForConditionalGeneration.from_pretrained(KOBART_PATH)
    model.to(device)
    print(f"✅ KoBART 모델 로드 완료")
    
    # 2. Whisper STT 모델 로드
    stt_model = whisper.load_model(WHISPER_MODEL_SIZE)
    print(f"✅ Whisper({WHISPER_MODEL_SIZE}) 모델 로드 완료")
    
except Exception as e:
    print(f"⚠️ 모델 로드 실패: {e}")
    print("👉 'models/final_emergency_model_v2' 경로 확인 및 'openai-whisper' 설치 확인 필요.")

# 광주 행정동 리스트 (주소 보정용)
GWANGJU_DONGS = [
    "충장동", "동명동", "계림동", "산수동", "소태동", "용산동", "서석동", "학동", "학운동", "지산동",
    "양동", "농성동", "광천동", "유촌동", "치평동", "쌍촌동", "화정동", "세하동", "서창동", "금호동",
    "풍암동", "동천동", "양림동", "방림동", "봉선동", "서동", "사직동", "월산동", "백운동", "주월동",
    "진월동", "행암동", "효덕동", "송하동", "지석동", "대촌동", "중흥동", "유동", "중앙동", "임동",
    "신안동", "용봉동", "운암동", "동림동", "우산동", "풍향동", "문화동", "각화동", "문흥동", "두암동",
    "삼각동", "일곡동", "매곡동", "오치동", "석곡동", "망월동", "건국동", "본촌동", "양산동", "신용동",
    "송정동", "도산동", "신흥동", "신촌동", "어룡동", "선암동", "우산동", "월곡동", "비아동", "신가동",
    "운남동", "신창동", "수완동", "하남동", "임곡동", "동곡동", "하산동", "평동", "옥동", "도덕동",
    "삼도동", "본량동", "남산동"
]

def transcribe_audio(audio_path):
    """
    Whisper 모델을 사용하여 오디오 파일을 텍스트로 변환합니다.
    """
    if stt_model is None:
        return ""
    
    try:
        result = stt_model.transcribe(audio_path, language="ko")
        return result["text"]
    except Exception as e:
        print(f"STT 변환 실패: {e}")
        return ""

# ==========================================
# 2. 내부 로직 함수 (주소 보정 및 태깅)
# ==========================================
def process_post_logic(summary_text, dialogue_text):
    # 1. 주소 보정 로직
    final_summary = summary_text
    addr_match = re.search(r'\[(.*?)\]', summary_text)
    
    if addr_match:
        full_addr = addr_match.group(1)
        target_part = full_addr.split()[-1]
        # fuzzywuzzy로 가장 유사한 행정동 찾기
        best_match, score = process.extractOne(target_part, GWANGJU_DONGS)
        if score >= 60:
            final_summary = summary_text.replace(target_part, best_match)

    # 2. 태그 추출 로직
    tags = []
    
    # 인구통계학적 태그
    if any(x in dialogue_text for x in ["할머니", "어르신", "노인", "할아버지"]): tags.append("#고령자")
    if any(x in dialogue_text for x in ["아이", "애기", "아기", "영유아", "신생아", "어린이집", "유치원"]): tags.append("#소아")
    if any(x in dialogue_text for x in ["장애인", "휠체어", "지체", "시각장애", "청각장애", "수어"]): tags.append("#장애인")
    if any(x in dialogue_text for x in ["임산부", "임신", "만삭", "진통", "양수", "산모"]): tags.append("#임산부")
    if any(x in dialogue_text for x in ["기저질환", "환자", "지병", "암환자", "투석", "당뇨", "고혈압"]): tags.append("#환자")
    if any(x in dialogue_text for x in ["외국인", "말이 안 통함", "영어", "외국어"]): tags.append("#외국인")

    # 증상별 태그 매핑
    symptom_map = {
        "#거동불가": ["못 일어나", "거동", "불편", "고관절"],
        "#호흡곤란": ["숨", "호흡", "코고는", "헉헉"],
        "#의식불명": ["정신", "의식", "기절", "실신", "안 깨어나"],
        "#심정지": ["심장", "맥박", "가슴통증", "압박", "CPR"],
        "#출혈": ["피", "출혈", "찢어짐", "과다출혈"],
        "#경련": ["경련", "발작", "떨림", "거품"],
        "#추락_골절": ["떨어짐", "추락", "골절", "부러짐"],
        "#뇌졸중": ["마비", "언어장애", "말이 안 나와", "반신마비"],
        "#화상": ["불", "화상", "뜨거움", "연기"]
    }
    
    for tag, keywords in symptom_map.items():
        if any(kw in dialogue_text for kw in keywords):
            tags.append(tag)

    return final_summary, " ".join(tags)

# ==========================================
# 3. 외부 호출용 메인 함수
# ==========================================
def analyze_emergency_text(text, audio_path=None):
    """
    main.py에서 호출하는 함수입니다.
    입력된 텍스트를 요약하고 태그를 생성하여 반환합니다.
    만약 텍스트가 부족하고 오디오 경로가 있다면 STT를 수행합니다.
    """
    # 0. 텍스트가 부족하면 STT 시도
    if (not text or len(text) < 5 or text == "텍스트 정보 없음") and audio_path:
        print(f"🎤 텍스트 정보 부족. STT 변환 시도: {audio_path}")
        stt_text = transcribe_audio(audio_path)
        if stt_text:
            text = stt_text
            print(f"📝 STT 변환 결과: {text}")

    # 텍스트가 없거나 너무 짧으면 분석 스킵
    if not text or len(text) < 5 or text == "텍스트 정보 없음":
        return {
            "summary": "분석할 텍스트 정보가 부족합니다.",
            "tags": "#정보없음"
        }

    # 모델이 로드되지 않았으면 원본 반환
    if model is None or tokenizer is None:
        final_summary, ner_tags = process_post_logic(text, text)
        return {
            "summary": text, # 요약 대신 원본 사용
            "tags": ner_tags
        }

    try:
        # 1. KoBART 요약 생성
        input_ids = tokenizer.encode(text, return_tensors="pt")
        input_ids = input_ids.to(device)

        summary_ids = model.generate(
            input_ids,
            max_new_tokens=50,      # 요약 길이 제한
            num_beams=5,            # Beam Search
            length_penalty=1.2,
            repetition_penalty=2.5, # 반복 방지
            early_stopping=True
        )
        
        summary_out = tokenizer.decode(summary_ids[0], skip_special_tokens=True)

        # 2. 후처리 (주소 보정 및 태그 생성)
        # 태그 생성 시에는 원문(text)을 참조하여 키워드를 찾습니다.
        final_summary, ner_tags = process_post_logic(summary_out, text)

        return {
            "summary": final_summary,
            "tags": ner_tags,
            "full_text": text  # 📝 변환된 STT 텍스트 반환
        }

    except Exception as e:
        print(f"텍스트 분석 중 에러 발생: {e}")
        return {
            "summary": text, 
            "tags": "#에러",
            "full_text": text
        }