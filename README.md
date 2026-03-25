## 🛠 Tech Stack
* **AI**: Whisper(STT), Hugging-Face, LangChain
* **Backend**: FastAPI / Python
* **Frontend**: React.js
* **Data**: 위급상황 음성/음향 (고도화) - 119 지능형 신고접수 음성 인식 데이터 (AI HUB)

## 🏗 Key Features & Tech Specs
1.  **AI 상황 요약 (STT & Summary)**:
    * 구급대원의 음성을 실시간으로 텍스트화(STT)하고, 핵심 증상을 LLM으로 요약하여 병원에 전송.
2.  **최적 병원 추천 알고리즘**:
    * 환자의 상태(KTAS 등급), 가용 병상 수, 실시간 교통 정보를 종합하여 최단 시간 내 수용 가능한 병원 리스트업.
3.  **실시간 대시보드**:
    * 병원 대기 현황과 이송 중인 환자 정보를 시각화하여 의료진의 선제적 대응 지원.

## 🧠 Troubleshooting
* **데이터 정합성 문제**: 여러 API(교통, 병상 정보)의 갱신 주기 차이로 인한 데이터 불일치 해결 과정.
* **음성 인식률 개선**: 구급차 내부 소음 환경에서의 STT 정확도를 높이기 위한 전처리 과정 등.

```text
├── backend/
│   ├── ai/               # Whisper, LLM 처리 로직
│   ├── models/              # 공공데이터 API 연동 모듈
├── frontend/             # 사용자 UI/UX
```

