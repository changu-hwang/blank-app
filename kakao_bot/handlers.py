"""발화(utterance) → 답변 텍스트 라우팅. 업무 로직은 여기에 추가."""

from datetime import datetime
from zoneinfo import ZoneInfo

DEFAULT_QUICK_REPLIES = ["도움말", "현재시각"]

HELP_TEXT = (
    "사용 가능한 명령어\n"
    "- 도움말: 이 안내 보기\n"
    "- 현재시각: 서버 기준 한국 시각\n"
    "- 그 외 입력: 받은 문장을 그대로 돌려드립니다(에코)"
)


def handle(utterance: str, user_id: str | None = None) -> tuple[str, list[str]]:
    text = (utterance or "").strip()

    if text in ("도움말", "help", "?"):
        return HELP_TEXT, DEFAULT_QUICK_REPLIES
    if text in ("현재시각", "시간"):
        now = datetime.now(ZoneInfo("Asia/Seoul"))
        return f"현재 시각(KST): {now:%Y-%m-%d %H:%M:%S}", DEFAULT_QUICK_REPLIES
    if not text:
        return "메시지를 입력해 주세요.", DEFAULT_QUICK_REPLIES
    return f"입력하신 내용: {text}", DEFAULT_QUICK_REPLIES
