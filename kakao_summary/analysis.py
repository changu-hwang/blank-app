"""파싱된 대화 DataFrame 의 필터링·통계·할 일 후보 추출·개인정보 마스킹."""

import io
import re
from datetime import date

import pandas as pd

# 요청·기한·결정 성격의 표현 (규칙 기반 후보 추출용)
ACTION_PATTERNS = [
    r"까지", r"마감", r"기한", r"제출", r"회신", r"요청", r"부탁", r"검토", r"확인\s*(바랍|부탁|해\s*주)",
    r"보내\s*(주|드리)", r"송부", r"납품", r"일정", r"회의", r"미팅", r"결정", r"확정", r"\d{1,2}\s*[/.월]\s*\d{1,2}\s*일?",
]
_ACTION_RE = re.compile("|".join(ACTION_PATTERNS))

_PHONE_RE = re.compile(r"01[016789][-.\s]?\d{3,4}[-.\s]?\d{4}|0\d{1,2}[-.\s]?\d{3,4}[-.\s]?\d{4}")
_EMAIL_RE = re.compile(r"[\w.+-]+@[\w-]+\.[\w.-]+")
_RRN_RE = re.compile(r"\d{6}[-\s]?[1-4]\d{6}")
_ACCOUNT_RE = re.compile(r"\d{2,6}-\d{2,6}-\d{2,8}")

_MEDIA = {"사진", "동영상", "이모티콘", "파일", "샵검색", "삭제된 메시지입니다.", "사진 2장", "음성메시지"}


def filter_df(
    df: pd.DataFrame,
    start: date | None = None,
    end: date | None = None,
    users: list[str] | None = None,
    keyword: str = "",
) -> pd.DataFrame:
    out = df
    if start:
        out = out[out["datetime"].dt.date >= start]
    if end:
        out = out[out["datetime"].dt.date <= end]
    if users:
        out = out[out["user"].isin(users)]
    if keyword.strip():
        out = out[out["message"].str.contains(keyword.strip(), case=False, regex=False)]
    return out


def is_media(msg: str) -> bool:
    m = msg.strip()
    return m in _MEDIA or bool(re.fullmatch(r"사진 \d+장|파일: .+", m))


def user_stats(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty:
        return pd.DataFrame(columns=["user", "메시지 수", "비율(%)"])
    s = df.groupby("user").size().sort_values(ascending=False)
    return pd.DataFrame({"user": s.index, "메시지 수": s.values, "비율(%)": (s.values / s.sum() * 100).round(1)})


def daily_counts(df: pd.DataFrame) -> pd.Series:
    return df.groupby(df["datetime"].dt.date).size()


def action_candidates(df: pd.DataFrame) -> pd.DataFrame:
    mask = df["message"].apply(lambda m: not is_media(m) and bool(_ACTION_RE.search(m)))
    return df[mask]


def mask_pii(text: str) -> str:
    text = _RRN_RE.sub("[주민번호]", text)
    text = _EMAIL_RE.sub("[이메일]", text)
    text = _PHONE_RE.sub("[전화번호]", text)
    return _ACCOUNT_RE.sub("[계좌번호]", text)


def to_transcript(df: pd.DataFrame, mask: bool = True) -> str:
    lines = []
    for r in df.itertuples(index=False):
        msg = mask_pii(r.message) if mask else r.message
        lines.append(f"{r.datetime:%Y-%m-%d %H:%M} {r.user}: {msg}")
    return "\n".join(lines)


def to_excel(sheets: dict[str, pd.DataFrame]) -> bytes:
    buf = io.BytesIO()
    with pd.ExcelWriter(buf, engine="openpyxl") as xw:
        for name, frame in sheets.items():
            frame.to_excel(xw, sheet_name=name[:31], index=False)
    return buf.getvalue()
