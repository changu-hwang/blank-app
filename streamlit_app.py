import streamlit as st
from datetime import datetime
import json

st.set_page_config(
    page_title="건설현장 긴급 안전관리",
    page_icon="🚨",
    layout="wide",
    initial_sidebar_state="expanded"
)

# CSS 스타일
st.markdown("""
<style>
.sos-button {
    background-color: #FF0000;
    color: white;
    font-size: 2rem;
    font-weight: bold;
    padding: 20px 40px;
    border-radius: 10px;
    text-align: center;
    animation: blink 1s step-start infinite;
}
@keyframes blink {
    50% { opacity: 0.5; }
}
.emergency-box {
    background-color: #FFF3CD;
    border: 2px solid #FF6B00;
    border-radius: 10px;
    padding: 20px;
    margin: 10px 0;
}
.action-box {
    background-color: #D4EDDA;
    border: 2px solid #28A745;
    border-radius: 10px;
    padding: 15px;
    margin: 5px 0;
}
.danger-box {
    background-color: #F8D7DA;
    border: 2px solid #DC3545;
    border-radius: 10px;
    padding: 15px;
    margin: 5px 0;
}
.info-box {
    background-color: #D1ECF1;
    border: 2px solid #17A2B8;
    border-radius: 10px;
    padding: 15px;
    margin: 5px 0;
}
</style>
""", unsafe_allow_html=True)

# 사고 유형별 긴급 대처 데이터
ACCIDENT_PROTOCOLS = {
    "추락 사고": {
        "icon": "🔴",
        "severity": "매우 위험",
        "immediate": [
            "피해자를 함부로 움직이지 마세요 (척추 손상 위험)",
            "의식 및 호흡 확인",
            "출혈이 있으면 깨끗한 천으로 압박 지혈",
            "골절 부위 고정 (부목 사용)",
            "보온 유지 (담요 등으로 덮기)",
        ],
        "caution": [
            "목/척추 부상 의심 시 절대 이동 금지",
            "의식 없을 경우 기도 확보 후 CPR 준비",
            "2차 추락 방지를 위해 현장 통제",
        ],
        "cpr": True,
    },
    "감전 사고": {
        "icon": "⚡",
        "severity": "매우 위험",
        "immediate": [
            "즉시 전원 차단 (메인 차단기)",
            "절연체로 피해자를 전원에서 분리",
            "직접 접촉 절대 금지",
            "의식 및 호흡 확인",
            "화상 부위 냉각 (흐르는 물 15분)",
        ],
        "caution": [
            "전원 차단 전 피해자 직접 접촉 금지",
            "심정지 가능성 높음 - CPR 즉시 준비",
            "2차 감전 방지를 위해 현장 통제",
        ],
        "cpr": True,
    },
    "화재 발생": {
        "icon": "🔥",
        "severity": "매우 위험",
        "immediate": [
            "즉시 비상벨 작동 및 대피 방송",
            "초기 소화 가능 시 소화기 사용 (등 뒤에 출구 확보)",
            "전직원 즉시 대피 지시",
            "가스 밸브 및 전원 차단",
            "부상자 확인 및 119 신고",
        ],
        "caution": [
            "연기 있을 경우 낮은 자세로 이동",
            "엘리베이터 절대 사용 금지",
            "화염이 크면 초기 진화 시도 금지",
        ],
        "cpr": False,
    },
    "협착/끼임 사고": {
        "icon": "⚙️",
        "severity": "위험",
        "immediate": [
            "즉시 기계 전원 차단",
            "역방향 운전으로 이탈 시도 (가능 시)",
            "함부로 잡아당기지 마세요",
            "피해자 의식 확인 및 안정",
            "출혈 시 압박 지혈",
        ],
        "caution": [
            "기계 재가동 절대 금지",
            "무리한 이탈 시도 금지 (절단 위험)",
            "119 구조대 전문 장비 대기",
        ],
        "cpr": False,
    },
    "붕괴/매몰 사고": {
        "icon": "🏗️",
        "severity": "매우 위험",
        "immediate": [
            "즉시 전 직원 대피",
            "2차 붕괴 위험 구역 통제",
            "매몰자 위치 파악 (소리, 목격자 확인)",
            "119 및 구조대 신고",
            "중장비 가동 중단",
        ],
        "caution": [
            "2차 붕괴 위험 - 구조는 전문가에게",
            "가스 누출 가능성 확인",
            "주변 지반 상태 지속 감시",
        ],
        "cpr": False,
    },
    "화학물질 누출": {
        "icon": "☣️",
        "severity": "위험",
        "immediate": [
            "즉시 누출 구역 대피",
            "바람이 부는 방향의 반대쪽으로 대피",
            "방호복/마스크 착용 후 밸브 차단",
            "누출 물질 MSDS 확인",
            "피부 접촉 시 흐르는 물로 15분 이상 세척",
        ],
        "caution": [
            "흡입 시 즉시 신선한 공기 위치로 이동",
            "화기 및 전기 사용 금지 (폭발 위험)",
            "하수구 유입 방지",
        ],
        "cpr": False,
    },
    "기타 부상": {
        "icon": "🩹",
        "severity": "일반",
        "immediate": [
            "피해자를 안전한 장소로 이동",
            "부상 부위 확인",
            "출혈 시 압박 지혈",
            "골절 의심 시 고정",
            "피해자 안정 및 보온",
        ],
        "caution": [
            "상태 악화 시 즉시 119 신고",
            "의식 저하 시 기도 확보",
            "음식/음료 제공 금지 (수술 가능성)",
        ],
        "cpr": False,
    },
}

# 세션 상태 초기화
if "site_info" not in st.session_state:
    st.session_state.site_info = {
        "name": "",
        "address": "",
        "manager": "",
        "manager_phone": "",
        "worker_count": 0,
    }
if "accident_log" not in st.session_state:
    st.session_state.accident_log = []
if "emergency_mode" not in st.session_state:
    st.session_state.emergency_mode = False
if "selected_accident" not in st.session_state:
    st.session_state.selected_accident = None

# 사이드바 - 현장 정보 설정
with st.sidebar:
    st.header("📋 현장 정보")
    st.session_state.site_info["name"] = st.text_input(
        "현장명", value=st.session_state.site_info["name"], placeholder="○○ 건설현장"
    )
    st.session_state.site_info["address"] = st.text_input(
        "현장 주소", value=st.session_state.site_info["address"], placeholder="시/군/구 동/읍/면 번지"
    )
    st.session_state.site_info["manager"] = st.text_input(
        "안전관리자명", value=st.session_state.site_info["manager"]
    )
    st.session_state.site_info["manager_phone"] = st.text_input(
        "관리자 연락처", value=st.session_state.site_info["manager_phone"], placeholder="010-0000-0000"
    )
    st.session_state.site_info["worker_count"] = st.number_input(
        "현장 근로자 수", min_value=0, value=st.session_state.site_info["worker_count"]
    )

    st.divider()
    st.subheader("📞 비상 연락망")
    st.markdown("**119** - 소방/구급")
    st.markdown("**112** - 경찰")
    st.markdown("**1588-0066** - 고용노동부")
    st.markdown("**1544-1949** - 안전보건공단")

    st.divider()
    if st.button("📄 사고 기록 보기", use_container_width=True):
        st.session_state.show_log = True

# 메인 화면
st.title("🚨 건설현장 긴급 안전관리 시스템")

site_name = st.session_state.site_info["name"] or "현장명 미입력"
site_address = st.session_state.site_info["address"] or "주소 미입력"
st.markdown(f"**현장:** {site_name} | **위치:** {site_address} | **현재시각:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

st.divider()

# 긴급 SOS 섹션
col1, col2, col3 = st.columns([1, 2, 1])
with col2:
    st.markdown("""
    <div class="sos-button">
        🚨 긴급 사고 발생 시 아래에서 사고 유형을 선택하세요 🚨
    </div>
    """, unsafe_allow_html=True)

st.markdown("---")

# 사고 유형 선택
st.subheader("⚠️ 사고 유형 선택")
cols = st.columns(4)
accident_types = list(ACCIDENT_PROTOCOLS.keys())

for i, accident_type in enumerate(accident_types):
    protocol = ACCIDENT_PROTOCOLS[accident_type]
    with cols[i % 4]:
        if st.button(
            f"{protocol['icon']} {accident_type}",
            key=f"btn_{accident_type}",
            use_container_width=True,
            type="primary" if protocol["severity"] == "매우 위험" else "secondary",
        ):
            st.session_state.selected_accident = accident_type
            st.session_state.emergency_mode = True

# 긴급 대처 매뉴얼 표시
if st.session_state.emergency_mode and st.session_state.selected_accident:
    accident = st.session_state.selected_accident
    protocol = ACCIDENT_PROTOCOLS[accident]
    accident_time = datetime.now()

    st.markdown("---")
    st.markdown(f"""
    <div class="danger-box">
        <h2>{protocol['icon']} {accident} 발생! - {accident_time.strftime('%H:%M:%S')}</h2>
        <h3>위험도: {protocol['severity']}</h3>
    </div>
    """, unsafe_allow_html=True)

    # 119 긴급 연결 버튼
    col_call1, col_call2, col_call3 = st.columns([1, 2, 1])
    with col_call2:
        st.markdown("""
        <a href="tel:119" style="
            display: block;
            background-color: #FF0000;
            color: white;
            text-align: center;
            padding: 20px;
            font-size: 1.8rem;
            font-weight: bold;
            border-radius: 10px;
            text-decoration: none;
            margin: 10px 0;
        ">📞 119 긴급 신고 (터치/클릭)</a>
        """, unsafe_allow_html=True)

    # 119 신고 시 전달할 정보
    st.markdown(f"""
    <div class="emergency-box">
        <h3>📢 119 신고 시 이렇게 말하세요:</h3>
        <p style="font-size: 1.1rem;">
        "건설현장에서 <strong>{accident}</strong>이 발생했습니다.<br>
        현장 주소는 <strong>{site_address}</strong>입니다.<br>
        현장명은 <strong>{site_name}</strong>이고,<br>
        부상자가 있습니다. 빨리 와 주세요."
        </p>
    </div>
    """, unsafe_allow_html=True)

    col_action, col_caution = st.columns(2)

    with col_action:
        st.markdown("### ✅ 즉각 조치 사항")
        for i, action in enumerate(protocol["immediate"], 1):
            st.markdown(f"""
            <div class="action-box">
                <strong>{i}단계:</strong> {action}
            </div>
            """, unsafe_allow_html=True)

    with col_caution:
        st.markdown("### ⛔ 주의사항")
        for caution in protocol["caution"]:
            st.markdown(f"""
            <div class="danger-box">
                ⚠️ {caution}
            </div>
            """, unsafe_allow_html=True)

        if protocol["cpr"]:
            st.markdown("""
            <div class="danger-box">
                <h4>💗 CPR 필요 시</h4>
                <ol>
                    <li>119 신고 후 안내에 따라 실시</li>
                    <li>가슴 압박: 분당 100~120회</li>
                    <li>깊이: 약 5cm (성인 기준)</li>
                    <li>압박:인공호흡 = 30:2</li>
                </ol>
            </div>
            """, unsafe_allow_html=True)

    # 사고 보고서 작성
    st.markdown("---")
    st.subheader("📝 사고 보고서 작성")
    with st.form("accident_report"):
        col_r1, col_r2 = st.columns(2)
        with col_r1:
            victim_name = st.text_input("부상자 성명")
            victim_age = st.number_input("나이", min_value=0, max_value=100, value=0)
            victim_company = st.text_input("소속 업체")
        with col_r2:
            accident_location = st.text_input("사고 발생 위치 (현장 내 구체적 위치)")
            victim_condition = st.selectbox("부상자 상태", ["의식 있음", "의식 불명", "경상", "중상", "사망"])
            workers_present = st.number_input("현장 근로자 수", min_value=0, value=st.session_state.site_info["worker_count"])

        accident_description = st.text_area("사고 경위 (간략히)", height=100)
        witness = st.text_input("목격자 성명/연락처")

        submitted = st.form_submit_button("📋 사고 보고서 저장", use_container_width=True, type="primary")

        if submitted:
            report = {
                "시각": accident_time.strftime("%Y-%m-%d %H:%M:%S"),
                "현장명": site_name,
                "현장주소": site_address,
                "안전관리자": st.session_state.site_info["manager"],
                "사고유형": accident,
                "부상자": victim_name,
                "나이": victim_age,
                "소속": victim_company,
                "사고위치": accident_location,
                "부상자상태": victim_condition,
                "사고경위": accident_description,
                "목격자": witness,
                "근로자수": workers_present,
            }
            st.session_state.accident_log.append(report)
            st.success("✅ 사고 보고서가 저장되었습니다.")

    # 초기화 버튼
    st.markdown("---")
    col_reset1, col_reset2, col_reset3 = st.columns([1, 1, 1])
    with col_reset2:
        if st.button("🔄 긴급 모드 종료 (상황 종료 후 클릭)", use_container_width=True):
            st.session_state.emergency_mode = False
            st.session_state.selected_accident = None
            st.rerun()

# 사고 기록 표시
if st.session_state.accident_log:
    st.markdown("---")
    st.subheader(f"📊 사고 기록 ({len(st.session_state.accident_log)}건)")
    for i, log in enumerate(reversed(st.session_state.accident_log), 1):
        with st.expander(f"사고 #{len(st.session_state.accident_log) - i + 1} | {log['시각']} | {log['사고유형']}"):
            st.json(log)

# 하단 안내
st.markdown("---")
st.markdown("""
<div class="info-box">
    <strong>📌 안전 관련 법령 안내</strong><br>
    • 중대재해 발생 시 <strong>즉시 작업 중지</strong> 및 고용노동부 신고 의무 (산업안전보건법 제54조)<br>
    • 사망사고 등 중대재해 발생 시 <strong>24시간 내</strong> 고용노동부 지방관서 신고<br>
    • 신고: <strong>1588-0066</strong> (고용노동부) | <strong>1544-1949</strong> (안전보건공단)
</div>
""", unsafe_allow_html=True)
