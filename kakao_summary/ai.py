"""Claude API 로 대화 요약 (선택 기능 — ANTHROPIC_API_KEY 필요)."""

import anthropic

MODEL = "claude-opus-5-5"
# 대략 1M 토큰 컨텍스트 이내로 유지하기 위한 보수적 문자 수 상한 (한글 1자 ≈ 1토큰 이상으로 가정)
MAX_CHARS = 600_000

SYSTEM_PROMPT = """당신은 업무용 카카오톡 대화를 정리하는 비서입니다.
대화록은 "YYYY-MM-DD HH:MM 이름: 내용" 형식입니다. 아래 구성으로 한국어 Markdown 보고서를 작성하세요.

## 1. 핵심 요약
3~7개 글머리표로 전체 흐름을 두괄식으로 요약.

## 2. 결정사항
| 일자 | 결정 내용 | 관련자 |

## 3. 할 일(Action Items)
| 담당자 | 할 일 | 기한 | 근거 메시지 일시 |
담당자·기한이 대화에 명시되지 않았으면 "미정"으로 적고 추측하지 마세요.

## 4. 주제별 정리
주요 주제마다 소제목과 논의 경과를 간결하게.

## 5. 미결·확인 필요 사항
결론이 나지 않았거나 상충되는 내용.

대화에 없는 사실은 만들지 말고, 해석이 들어간 문장은 "(추정)"으로 표시하세요.
[전화번호] 등 마스킹 표기는 그대로 두세요."""


class SummaryError(Exception):
    pass


def summarize(transcript: str, focus: str = "", api_key: str | None = None) -> str:
    if len(transcript) > MAX_CHARS:
        raise SummaryError(
            f"대화가 너무 깁니다({len(transcript):,}자). 기간·참여자 필터로 {MAX_CHARS:,}자 이하로 줄여 주세요."
        )

    user_content = f"<대화록>\n{transcript}\n</대화록>"
    if focus.strip():
        user_content += f"\n\n특히 다음 관점에 초점을 맞춰 정리하세요: {focus.strip()}"

    client = anthropic.Anthropic(api_key=api_key) if api_key else anthropic.Anthropic()
    try:
        with client.beta.messages.stream(
            model=MODEL,
            max_tokens=64000,
            system=SYSTEM_PROMPT,
            output_config={"effort": "medium"},
            betas=["server-side-fallback-2026-07-01"],
            fallbacks="default",
            messages=[{"role": "user", "content": user_content}],
        ) as stream:
            response = stream.get_final_message()
    except anthropic.AuthenticationError as e:
        raise SummaryError("API 키가 올바르지 않습니다.") from e
    except anthropic.RateLimitError as e:
        raise SummaryError("요청 한도를 초과했습니다. 잠시 후 다시 시도해 주세요.") from e
    except anthropic.BadRequestError as e:
        raise SummaryError(f"요청 오류: {e.message}") from e
    except anthropic.APIStatusError as e:
        raise SummaryError(f"API 오류({e.status_code}): {e.message}") from e
    except anthropic.APIConnectionError as e:
        raise SummaryError("Claude API 에 연결할 수 없습니다.") from e

    if response.stop_reason == "refusal":
        raise SummaryError("모델이 이 대화의 요약을 거절했습니다.")

    text = "".join(b.text for b in response.content if b.type == "text")
    if response.stop_reason == "max_tokens":
        text += "\n\n> ⚠️ 출력 길이 한도에 도달해 요약이 중간에 끊겼습니다. 기간을 나눠 다시 요약해 주세요."
    return text
