import os

import streamlit as st

from kakao_summary.ai import SummaryError, summarize
from kakao_summary.analysis import (
    action_candidates,
    daily_counts,
    filter_df,
    mask_pii,
    to_excel,
    to_transcript,
    user_stats,
)
from kakao_summary.parser import parse

st.set_page_config(page_title="카카오톡 대화 정리", page_icon="💬", layout="wide")
st.title("💬 카카오톡 대화 정리")
st.caption("대화방 메뉴 → 설정 → '대화 내용 내보내기'로 받은 txt/csv 파일을 올려 주세요. 파일은 서버에 저장되지 않습니다.")


def _secret_api_key() -> str | None:
    try:
        return st.secrets.get("ANTHROPIC_API_KEY")
    except Exception:  # secrets.toml 이 없으면 예외
        return None


@st.cache_data(show_spinner="대화 파일 분석 중…")
def _load(raw: bytes):
    return parse(raw)


uploaded = st.file_uploader("내보내기 파일", type=["txt", "csv"])
if not uploaded:
    st.stop()

df = _load(uploaded.getvalue())
if df.empty:
    st.error("메시지를 찾지 못했습니다. 카카오톡 '대화 내용 내보내기' 원본 파일인지 확인해 주세요.")
    st.stop()

# ── 필터 ─────────────────────────────────────────────
with st.sidebar:
    st.header("필터")
    min_d, max_d = df["datetime"].min().date(), df["datetime"].max().date()
    period = st.date_input("기간", (min_d, max_d), min_value=min_d, max_value=max_d)
    start, end = (period if isinstance(period, tuple) and len(period) == 2 else (min_d, max_d))
    all_users = sorted(df["user"].unique())
    users = st.multiselect("참여자", all_users)
    keyword = st.text_input("키워드")
    masked = st.checkbox("개인정보 마스킹(전화·이메일·주민번호·계좌)", value=True)

view = filter_df(df, start, end, users, keyword)

c1, c2, c3, c4 = st.columns(4)
c1.metric("메시지", f"{len(view):,}")
c2.metric("참여자", view["user"].nunique())
c3.metric("기간(일)", (end - start).days + 1)
c4.metric("할 일 후보", len(action_candidates(view)))

display = view.assign(message=view["message"].map(mask_pii)) if masked else view
actions = action_candidates(display)
stats = user_stats(view)

MSG_COLUMNS = {
    "datetime": st.column_config.DatetimeColumn("일시", format="YYYY-MM-DD HH:mm"),
    "user": "발신자",
    "message": "내용",
}

tab_msg, tab_stat, tab_act, tab_ai = st.tabs(["대화", "통계", "할 일 후보", "AI 요약"])

with tab_msg:
    st.dataframe(display, width="stretch", hide_index=True, column_config=MSG_COLUMNS)

with tab_stat:
    left, right = st.columns(2)
    left.subheader("참여자별")
    left.dataframe(stats, width="stretch", hide_index=True)
    right.subheader("일자별 메시지 수")
    right.bar_chart(daily_counts(view))
    st.subheader("시간대별 메시지 수")
    st.bar_chart(view.groupby(view["datetime"].dt.hour).size().reindex(range(24), fill_value=0))

with tab_act:
    st.caption("기한·요청·제출·회신·일정 등 표현이 들어간 메시지를 규칙 기반으로 뽑은 **후보**입니다. 확정 목록이 아니므로 검토가 필요합니다.")
    st.dataframe(actions, width="stretch", hide_index=True, column_config=MSG_COLUMNS)

with tab_ai:
    api_key = _secret_api_key() or os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        api_key = st.text_input("Anthropic API 키", type="password",
                                help="Streamlit secrets 의 ANTHROPIC_API_KEY 로 설정하면 입력하지 않아도 됩니다.")
    focus = st.text_input("요약 초점(선택)", placeholder="예: 발주처 요청사항과 성과품 납품 일정")
    st.caption("현재 필터가 적용된 대화가 Claude API 로 전송됩니다. 마스킹 옵션을 확인하세요.")
    if st.button("AI 요약 생성", type="primary", disabled=not api_key or view.empty):
        with st.spinner("요약 생성 중… (대화 분량에 따라 1~2분 소요)"):
            try:
                st.session_state["summary"] = summarize(to_transcript(view, mask=masked), focus, api_key)
            except SummaryError as e:
                st.error(str(e))
    if summary := st.session_state.get("summary"):
        st.markdown(summary)
        st.download_button("요약 다운로드(.md)", summary, file_name="카카오톡_요약.md")

st.divider()
st.download_button(
    "엑셀로 내보내기",
    to_excel({"대화": display, "참여자별": stats, "할일후보": actions}),
    file_name="카카오톡_정리.xlsx",
    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
)
