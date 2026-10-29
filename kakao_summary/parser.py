"""카카오톡 '대화 내용 내보내기' 파일 파서.

지원 형식
- PC(Windows/Mac) txt : "--------------- 2024년 1월 1일 월요일 ---------------" + "[이름] [오전 9:01] 내용"
- Android txt        : "2024년 1월 1일 오전 9:01, 이름 : 내용"
- iOS txt            : "2024. 1. 1. 오전 9:01, 이름 : 내용"
- 모바일 csv          : "Date,User,Message" 헤더

결과는 datetime / user / message 컬럼의 DataFrame. 여러 줄 메시지는 이어 붙이고,
입장·퇴장 등 발신자가 없는 시스템 메시지는 제외한다.
"""

import csv
import io
import re
from datetime import date, datetime

import pandas as pd

COLUMNS = ["datetime", "user", "message"]

_AMPM = r"(오전|오후)\s*(\d{1,2}):(\d{2})"
_PC_DATE = re.compile(r"^-+\s*(\d{4})년\s*(\d{1,2})월\s*(\d{1,2})일.*?-+\s*$")
_PC_MSG = re.compile(rf"^\[(.+?)\]\s*\[{_AMPM}\]\s?(.*)$")
_MOBILE_MSG = re.compile(
    rf"^(\d{{4}})(?:년\s*|\.\s*)(\d{{1,2}})(?:월\s*|\.\s*)(\d{{1,2}})(?:일|\.)\s*,?\s*{_AMPM},\s*(.+?)\s:\s?(.*)$"
)
_MOBILE_SYSTEM = re.compile(rf"^(\d{{4}})(?:년\s*|\.\s*)(\d{{1,2}})(?:월\s*|\.\s*)(\d{{1,2}})(?:일|\.)\s*,?\s*{_AMPM},")
_DATE_HEADER = re.compile(r"^(\d{4})년\s*(\d{1,2})월\s*(\d{1,2})일\s*\S*요일\s*$")


def _to_24h(ampm: str, hour: str, minute: str) -> tuple[int, int]:
    h = int(hour) % 12
    if ampm == "오후":
        h += 12
    return h, int(minute)


def decode(raw: bytes) -> str:
    for enc in ("utf-8-sig", "cp949"):
        try:
            return raw.decode(enc)
        except UnicodeDecodeError:
            continue
    return raw.decode("utf-8", errors="replace")


def _parse_csv(text: str) -> pd.DataFrame:
    rows = []
    for rec in csv.DictReader(io.StringIO(text)):
        try:
            dt = datetime.fromisoformat((rec.get("Date") or "").strip())
        except ValueError:
            continue
        rows.append((dt, (rec.get("User") or "").strip(), rec.get("Message") or ""))
    return pd.DataFrame(rows, columns=COLUMNS)


def _parse_txt(text: str) -> pd.DataFrame:
    rows: list[list] = []
    current_day: date | None = None
    last_is_msg = False

    for line in text.splitlines():
        stripped = line.strip()

        m = _PC_DATE.match(stripped) or _DATE_HEADER.match(stripped)
        if m:
            current_day = date(int(m[1]), int(m[2]), int(m[3]))
            last_is_msg = False
            continue

        m = _MOBILE_MSG.match(stripped)
        if m:
            h, mi = _to_24h(m[4], m[5], m[6])
            rows.append([datetime(int(m[1]), int(m[2]), int(m[3]), h, mi), m[7].strip(), m[8]])
            last_is_msg = True
            continue

        m = _PC_MSG.match(stripped)
        if m and current_day:
            h, mi = _to_24h(m[2], m[3], m[4])
            rows.append([datetime.combine(current_day, datetime.min.time()).replace(hour=h, minute=mi), m[1].strip(), m[5]])
            last_is_msg = True
            continue

        if _MOBILE_SYSTEM.match(stripped):
            last_is_msg = False  # 입장/퇴장 등 시스템 메시지
            continue

        if last_is_msg and rows:
            rows[-1][2] += "\n" + line  # 여러 줄 메시지

    return pd.DataFrame(rows, columns=COLUMNS)


def parse(raw: bytes) -> pd.DataFrame:
    text = decode(raw)
    first = text.lstrip().splitlines()[0] if text.strip() else ""
    df = _parse_csv(text) if first.replace('"', "").startswith("Date,User,Message") else _parse_txt(text)
    if not df.empty:
        df["message"] = df["message"].str.rstrip()
        df = df.sort_values("datetime", kind="stable").reset_index(drop=True)
    return df
