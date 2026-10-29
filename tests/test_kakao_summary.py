from datetime import datetime

from kakao_summary.analysis import action_candidates, filter_df, mask_pii, to_transcript, user_stats
from kakao_summary.parser import parse

PC_TXT = """홍길동 님과 카카오톡 대화
저장한 날짜 : 2026-10-20 18:00:00

--------------- 2026년 10월 19일 월요일 ---------------
[홍길동] [오전 9:01] 안녕하세요
[김철수] [오후 12:30] 성과품 금요일까지 제출 부탁드립니다
두번째 줄
[홍길동] [오전 12:05] 자정 메시지
"""

ANDROID_TXT = """2026년 10월 19일 월요일
2026년 10월 19일 오전 9:01, 홍길동 : 안녕하세요
2026년 10월 19일 오전 9:02, 김철수님이 들어왔습니다.
2026년 10월 19일 오후 1:15, 김철수 : 내일 회의 10시
연락처 010-1234-5678
"""

IOS_TXT = """2026. 10. 19. 오후 3:40, 홍길동 : 아이폰 메시지
"""

CSV = """Date,User,Message
2026-10-19 09:01:00,"홍길동","안녕하세요"
2026-10-19 13:15:00,"김철수","검토 요청드립니다"
2026-10-19 13:20:00,"","Chat Loss"
"""


def test_pc_format():
    df = parse(PC_TXT.encode("utf-8"))
    assert len(df) == 3
    assert df.iloc[0]["datetime"] == datetime(2026, 10, 19, 0, 5)  # 오전 12시 = 0시, 시간순 정렬
    row = df[df["user"] == "김철수"].iloc[0]
    assert row["datetime"] == datetime(2026, 10, 19, 12, 30)
    assert row["message"] == "성과품 금요일까지 제출 부탁드립니다\n두번째 줄"


def test_android_format_skips_system_and_joins_lines():
    df = parse(ANDROID_TXT.encode("utf-8"))
    assert list(df["user"]) == ["홍길동", "김철수"]
    assert df.iloc[1]["datetime"] == datetime(2026, 10, 19, 13, 15)
    assert "010-1234-5678" in df.iloc[1]["message"]


def test_ios_format():
    df = parse(IOS_TXT.encode("utf-8"))
    assert df.iloc[0]["datetime"] == datetime(2026, 10, 19, 15, 40)
    assert df.iloc[0]["message"] == "아이폰 메시지"


def test_csv_format_and_cp949():
    df = parse(CSV.encode("cp949"))
    assert list(df["user"]) == ["홍길동", "김철수"]


def test_analysis():
    df = parse(ANDROID_TXT.encode("utf-8"))
    assert len(filter_df(df, users=["김철수"])) == 1
    assert len(filter_df(df, keyword="회의")) == 1
    assert user_stats(df)["메시지 수"].sum() == 2
    assert list(action_candidates(df)["user"]) == ["김철수"]
    assert "[전화번호]" in to_transcript(df, mask=True)
    assert "010-1234-5678" in to_transcript(df, mask=False)


def test_mask_pii():
    s = mask_pii("메일 a.b@test.co.kr, 주민 900101-1234567, 계좌 110-123-456789")
    assert "[이메일]" in s and "[주민번호]" in s and "[계좌번호]" in s


def test_file_message_is_media():
    from kakao_summary.analysis import is_media
    assert is_media("파일: 일정표_10월.pdf")
    assert not is_media("파일 보내주세요")
