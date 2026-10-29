"""카카오톡 채널 챗봇 스킬 서버 (카카오 i 오픈빌더).

실행: uvicorn kakao_bot.app:app --host 0.0.0.0 --port 8000

엔드포인트
- POST /skill           : 일반 스킬 (5초 이내 동기 응답)
- POST /skill/callback  : 콜백 스킬 (즉시 대기 응답 후 callbackUrl 로 최종 답변, 1분 이내)
- GET  /health          : 헬스체크

환경변수
- KAKAO_SKILL_TOKEN : 설정 시 요청 헤더 X-Skill-Token 값과 일치해야 처리
"""

import hmac
import logging
import os

import httpx
from fastapi import BackgroundTasks, FastAPI, Header, HTTPException, Request

from kakao_bot.handlers import handle
from kakao_bot.responses import callback_ack, simple_text

logger = logging.getLogger("kakao_bot")

app = FastAPI(title="Kakao Skill Server")


def _check_token(token: str | None) -> None:
    expected = os.environ.get("KAKAO_SKILL_TOKEN")
    if expected and not hmac.compare_digest(token or "", expected):
        raise HTTPException(status_code=401, detail="invalid skill token")


def _parse(payload: dict) -> tuple[str, str | None, str | None]:
    req = payload.get("userRequest") or {}
    user_id = (req.get("user") or {}).get("id")
    return req.get("utterance", ""), user_id, req.get("callbackUrl")


@app.get("/health")
def health() -> dict:
    return {"status": "ok"}


@app.post("/skill")
async def skill(request: Request, x_skill_token: str | None = Header(default=None)) -> dict:
    _check_token(x_skill_token)
    utterance, user_id, _ = _parse(await request.json())
    text, replies = handle(utterance, user_id)
    return simple_text(text, replies)


async def _send_callback(callback_url: str, utterance: str, user_id: str | None) -> None:
    try:
        text, replies = handle(utterance, user_id)
        body = simple_text(text, replies)
    except Exception:
        logger.exception("handler failed")
        body = simple_text("처리 중 오류가 발생했습니다. 잠시 후 다시 시도해 주세요.")
    try:
        async with httpx.AsyncClient(timeout=10) as client:
            resp = await client.post(callback_url, json=body)
            resp.raise_for_status()
    except httpx.HTTPError:
        logger.exception("callback delivery failed")


@app.post("/skill/callback")
async def skill_callback(
    request: Request,
    background: BackgroundTasks,
    x_skill_token: str | None = Header(default=None),
) -> dict:
    _check_token(x_skill_token)
    utterance, user_id, callback_url = _parse(await request.json())
    if not callback_url:
        # 콜백이 비활성화된 블록에서 호출된 경우 동기 응답으로 대체
        text, replies = handle(utterance, user_id)
        return simple_text(text, replies)
    background.add_task(_send_callback, callback_url, utterance, user_id)
    return callback_ack()
