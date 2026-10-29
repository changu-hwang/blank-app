"""카카오 i 오픈빌더 스킬 응답(SkillResponse v2.0) 생성 헬퍼.

참고: https://kakaobusiness.gitbook.io/main/tool/chatbot/skill_guide/answer_json_format
"""

SIMPLE_TEXT_MAX = 1000  # simpleText.text 최대 길이
QUICK_REPLY_MAX = 10    # quickReplies 최대 개수
QUICK_REPLY_LABEL_MAX = 14


def quick_reply(label: str, message: str | None = None) -> dict:
    return {
        "label": label[:QUICK_REPLY_LABEL_MAX],
        "action": "message",
        "messageText": message or label,
    }


def simple_text(text: str, quick_replies: list[str] | None = None) -> dict:
    template: dict = {"outputs": [{"simpleText": {"text": text[:SIMPLE_TEXT_MAX]}}]}
    if quick_replies:
        template["quickReplies"] = [quick_reply(q) for q in quick_replies[:QUICK_REPLY_MAX]]
    return {"version": "2.0", "template": template}


def callback_ack(wait_text: str = "답변을 준비 중입니다. 잠시만 기다려 주세요.") -> dict:
    """콜백(AI 챗봇) 블록용 1차 응답. 실제 답변은 callbackUrl 로 별도 전송."""
    return {"version": "2.0", "useCallback": True, "data": {"text": wait_text}}
