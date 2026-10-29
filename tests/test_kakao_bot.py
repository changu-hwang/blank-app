from unittest.mock import AsyncMock, MagicMock, patch

from fastapi.testclient import TestClient

from kakao_bot.app import app

client = TestClient(app)


def _payload(utterance: str, callback_url: str | None = None) -> dict:
    req = {"utterance": utterance, "user": {"id": "u1", "type": "botUserKey"}}
    if callback_url:
        req["callbackUrl"] = callback_url
    return {"intent": {"id": "i", "name": "폴백 블록"}, "userRequest": req, "action": {"params": {}}}


def test_health():
    assert client.get("/health").json() == {"status": "ok"}


def test_skill_echo():
    body = client.post("/skill", json=_payload("안녕")).json()
    assert body["version"] == "2.0"
    assert body["template"]["outputs"][0]["simpleText"]["text"] == "입력하신 내용: 안녕"
    assert body["template"]["quickReplies"][0]["messageText"] == "도움말"


def test_skill_help():
    text = client.post("/skill", json=_payload("도움말")).json()["template"]["outputs"][0]["simpleText"]["text"]
    assert "명령어" in text


def test_long_text_truncated():
    text = client.post("/skill", json=_payload("가" * 2000)).json()["template"]["outputs"][0]["simpleText"]["text"]
    assert len(text) == 1000


def test_token_required(monkeypatch):
    monkeypatch.setenv("KAKAO_SKILL_TOKEN", "secret")
    assert client.post("/skill", json=_payload("x")).status_code == 401
    assert client.post("/skill", json=_payload("x"), headers={"X-Skill-Token": "secret"}).status_code == 200


def test_callback_ack_and_delivery():
    with patch("kakao_bot.app.httpx.AsyncClient.post", new_callable=AsyncMock, return_value=MagicMock()) as post:
        body = client.post("/skill/callback", json=_payload("안녕", "https://bot-api.kakao.com/cb/123")).json()
    assert body["useCallback"] is True
    url = post.call_args.args[0]
    sent = post.call_args.kwargs["json"]
    assert url == "https://bot-api.kakao.com/cb/123"
    assert sent["template"]["outputs"][0]["simpleText"]["text"] == "입력하신 내용: 안녕"


def test_callback_without_url_falls_back_to_sync():
    body = client.post("/skill/callback", json=_payload("안녕")).json()
    assert "useCallback" not in body
    assert body["template"]["outputs"][0]["simpleText"]["text"] == "입력하신 내용: 안녕"
