# 💬 카카오톡 대화 정리 (Streamlit)

카카오톡 '대화 내용 내보내기' 파일(txt/csv)을 업로드하면 대화를 정리합니다.

- 지원 형식: PC(Windows/Mac) txt, Android txt, iOS txt, 모바일 csv (UTF-8/CP949)
- 기능: 기간·참여자·키워드 필터, 참여자별/일자별/시간대별 통계, 할 일 후보(규칙 기반) 추출, 개인정보 마스킹, 엑셀 내보내기
- AI 요약(선택): Claude API로 핵심 요약·결정사항·할 일·미결사항 보고서 생성. `.streamlit/secrets.toml`에 `ANTHROPIC_API_KEY = "..."`를 설정하거나 화면에서 키 입력
  - 필터가 적용된 대화가 외부 API로 전송되므로, 마스킹 옵션과 소속 기관 보안 지침을 확인하세요.

[![Open in Streamlit](https://static.streamlit.io/badges/streamlit_badge_black_white.svg)](https://blank-app-template.streamlit.app/)

### How to run it on your own machine

1. Install the requirements

   ```
   $ pip install -r requirements.txt
   ```

2. Run the app

   ```
   $ streamlit run streamlit_app.py
   ```

## 카카오톡 채널 챗봇 스킬 서버 (`kakao_bot/`)

카카오 i 오픈빌더의 **스킬(Skill) 서버**입니다. Streamlit 앱과는 별도의 FastAPI 프로세스로 실행합니다.

```
pip install -r requirements-bot.txt
uvicorn kakao_bot.app:app --host 0.0.0.0 --port 8000
```

| 엔드포인트 | 용도 |
|---|---|
| `POST /skill` | 일반 스킬 — 5초 이내 동기 응답 |
| `POST /skill/callback` | 콜백 스킬 — 즉시 대기 메시지 후 `callbackUrl`로 최종 답변(1분 이내) |
| `GET /health` | 헬스체크 |

오픈빌더 설정 순서
1. 카카오톡 채널 개설 → 카카오 i 오픈빌더에서 챗봇 생성·채널 연결
2. **스킬** 메뉴에서 URL 등록 (`https://<서버주소>/skill`, HTTPS 필수)
3. 폴백 블록(또는 원하는 블록)의 응답을 "스킬데이터 사용"으로 지정 후 배포
4. (선택) 스킬 헤더에 `X-Skill-Token` 추가 + 서버 환경변수 `KAKAO_SKILL_TOKEN`에 같은 값 설정
5. (선택) 응답이 5초를 넘을 수 있으면 블록의 콜백 기능을 켜고 `/skill/callback` 사용 (AI 챗봇 전환 신청 필요)

업무 로직은 `kakao_bot/handlers.py`의 `handle()`에 추가합니다. 테스트: `pytest tests`
