import streamlit as st
import pandas as pd
import sqlite3
import os
import plotly.express as px
import plotly.graph_objects as go

# 페이지 설정
st.set_page_config(
    page_title="외국인 관광객 EDA 및 사업 전략 대시보드",
    page_icon="✈️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 커스텀 CSS (프리미엄 디자인)
st.markdown("""
    <style>
    .main {
        background-color: #f8f9fa;
    }
    .stMetric {
        background-color: #ffffff;
        padding: 20px;
        border-radius: 10px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
    }
    h1, h2, h3 {
        color: #1e3a8a;
    }
    </style>
    """, unsafe_allow_html=True)

# 데이터 경로 (상대 경로로 수정 - GitHub 배포용)
base_path = os.path.join(os.path.dirname(__file__), 'dataset')

@st.cache_data
def load_data():
    # 1. 국적 데이터
    df_nat_raw = pd.read_csv(os.path.join(base_path, '(전국기준)국적별+외국인+방문객_20260228095700.csv'), encoding='utf-8-sig')
    df_nat = df_nat_raw.iloc[1:].copy()
    df_nat.columns = ['대륙', '국가', '계', '남자', '여자']
    df_nat = df_nat[~df_nat['국가'].isin(['소계', '대륙별(2)'])]
    df_nat['계'] = pd.to_numeric(df_nat['계'], errors='coerce')
    
    # 2. 연령 데이터
    df_age_raw = pd.read_csv(os.path.join(base_path, '(전국기준)연령별+외국인+방문객_20260228095859.csv'), encoding='utf-8-sig')
    df_age = df_age_raw.iloc[2:].copy()
    df_age.columns = ['대륙1', '대륙2', '합계', '0-9세', '10-19세', '20-29세', '30-39세', '40-49세', '50-59세', '60-69세', '70-79세', '80세이상', '승무원']
    
    # 3. 교통 데이터
    df_trans_raw = pd.read_csv(os.path.join(base_path, '(전국기준)입국교통수단별+외국인+방문객_20260228095722.csv'), encoding='utf-8-sig')
    df_trans = df_trans_raw.iloc[2:].copy()
    df_trans.columns = ['대륙1', '대륙2', '합계', '공항_소계', '인천공항', '김해공항', '김포공항', '제주공항', '기타공항', '항구_소계', '부산항', '인천항', '제주항', '기타항']

    # 4. 호텔 데이터
    df_hotel_raw = pd.read_csv(os.path.join(base_path, '관광호텔+등록현황_20260228095634.csv'), encoding='utf-8-sig')
    df_hotel = df_hotel_raw.iloc[3:].copy()
    df_hotel.columns = ['지역1', '지역2', '호텔수', '객실수'] + [f'col_{i}' for i in range(len(df_hotel_raw.columns)-4)]
    df_hotel['호텔수'] = pd.to_numeric(df_hotel['호텔수'], errors='coerce')

    # 5. Airbnb 데이터
    conn = sqlite3.connect(os.path.join(base_path, 'airbnb.db'))
    df_airbnb = pd.read_sql_query("SELECT * FROM airbnb_stays", conn)
    conn.close()
    df_airbnb['price_val'] = pd.to_numeric(df_airbnb['price_value'], errors='coerce')

    # 6. 도시민박 데이터
    df_fore = pd.read_csv(os.path.join(base_path, 'foreigner.csv'), encoding='utf-8-sig')
    
    return df_nat, df_age, df_trans, df_hotel, df_airbnb, df_fore

# 데이터 로드
df_nat, df_age, df_trans, df_hotel, df_airbnb, df_fore = load_data()

# 사이드바
st.sidebar.title("🔍 분석 필터")
category = st.sidebar.selectbox("분석 영역 선택", ["전체 요약", "국적 및 연령 분석", "교통수단 분석", "숙박 공급 분석", "사업 전략 제안"])

# 1. 전체 요약
if category == "전체 요약":
    st.title("🚀 외국인 관광객 EDA 요약")
    
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("총 방문객 수 (2025)", f"{int(df_nat['계'].sum()):,}명")
    with col2:
        top_country = df_nat.sort_values('계', ascending=False).iloc[0]
        st.metric("최대 방문 국가", f"{top_country['국가']}", f"{int(top_country['계']):,}명")
    with col3:
        total_hotels = int(df_hotel[df_hotel['지역1']=='서울시']['호텔수'].sum())
        st.metric("서울시 총 호텔 수", f"{total_hotels}개")
    with col4:
        avg_airbnb = int(df_airbnb['price_val'].mean())
        st.metric("Airbnb 평균 가격", f"₩{avg_airbnb:,}")

    st.markdown("---")
    
    st.subheader("💡 핵심 인사이트")
    st.info("""
    - **핵심 타겟**: 중국, 일본 중심의 아시아권과 20-30대 젊은 층 MZ세대.
    - **입국 거점**: 인천공항이 압도적인 비중을 차지 (항공이 기본).
    - **숙박 트렌드**: 명동(호텔) vs 홍대(에어비앤비/민박)의 양강 구조. MZ세대는 마포구를 선호.
    """)

# 2. 국적 및 연령 분석
elif category == "국적 및 연령 분석":
    st.title("🌍 국적 및 연령대 심층 분석")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Top 10 방문 국가")
        top_10 = df_nat.sort_values('계', ascending=False).head(10)
        fig_nat = px.bar(top_10, x='국가', y='계', color='계', 
                         color_continuous_scale='Viridis', 
                         title='2025년 국적별 방문객 수')
        st.plotly_chart(fig_nat, use_container_width=True)

    with col2:
        st.subheader("연령대별 방문객 비중")
        df_age_total = df_age[df_age['대륙2'] == '소계'].iloc[0]
        age_data = pd.DataFrame({
            '연령대': ['0-9세', '10-19세', '20-29세', '30-39세', '40-49세', '50-59세', '60-69세', '70-79세', '80세이상'],
            '방문객': [pd.to_numeric(df_age_total[c]) for c in ['0-9세', '10-19세', '20-29세', '30-39세', '40-49세', '50-59세', '60-69세', '70-79세', '80세이상']]
        })
        fig_age = px.pie(age_data, values='방문객', names='연령대', 
                         hole=0.4, title='2025년 연령대별 비율',
                         color_discrete_sequence=px.colors.qualitative.Pastel)
        st.plotly_chart(fig_age, use_container_width=True)

    st.success("**인사이트**: 2030 세대가 전체의 45% 이상을 차지하므로 MZ세대 취향의 트렌디한 상품 구성이 필수적입니다.")

# 3. 교통수단 분석
elif category == "교통수단 분석":
    st.title("✈️ 입국 교통수단 및 공항 거점 분석")
    
    df_trans_total = df_trans[df_trans['대륙2'] == '소계'].iloc[0]
    
    col1, col2 = st.columns([1, 2])
    
    with col1:
        st.subheader("교통수단 비율")
        trans_sum = pd.DataFrame({
            '수단': ['공항', '항구'],
            '방문객': [pd.to_numeric(df_trans_total['공항_소계']), pd.to_numeric(df_trans_total['항구_소계'])]
        })
        fig_trans = px.pie(trans_sum, values='방문객', names='수단', 
                           color_discrete_sequence=['#FF6B6B', '#4ECDC4'], 
                           title='공항 vs 항구')
        st.plotly_chart(fig_trans, use_container_width=True)
        
    with col2:
        st.subheader("주요 공항별 입국객 분포")
        airport_data = pd.DataFrame({
            '공항': ['인천', '김해', '김포', '제주', '기타'],
            '방문객': [pd.to_numeric(df_trans_total[c]) for c in ['인천공항', '김해공항', '김포공항', '제주공항', '기타공항']]
        })
        fig_air = px.bar(airport_data, x='공항', y='방문객', color='방문객',
                         color_continuous_scale='Blues', title='공항별 입국객 수')
        st.plotly_chart(fig_air, use_container_width=True)

    st.warning("**전략**: 인천공항 입국객이 절대적이므로 공항 픽업/샌딩 및 공항 근처 숙박 패키지 효율이 가장 높습니다.")

# 4. 숙박 공급 분석
elif category == "숙박 공급 분석":
    st.title("🏨 숙박 공급 및 지역별 집중도 분석")
    
    tab1, tab2, tab3 = st.tabs(["서울 자치구별 호텔", "Airbnb 가격", "도시민박 집중도"])
    
    with tab1:
        st.subheader("서울시 자치구별 호텔 현황")
        df_hotel_seoul = df_hotel[(df_hotel['지역1'] == '서울시') & (df_hotel['지역2'] != '소계')].copy()
        fig_hotel = px.bar(df_hotel_seoul.sort_values('호텔수', ascending=False), 
                           x='지역2', y='호텔수', title='자치구별 관광호텔 수',
                           labels={'지역2': '자치구', '호텔수': '호텔 수(개)'})
        st.plotly_chart(fig_hotel, use_container_width=True)
    
    with tab2:
        st.subheader("Airbnb 가격 분포 (1박)")
        fig_airbnb = px.histogram(df_airbnb[df_airbnb['price_val'] < 500000], 
                                  x='price_val', nbins=50, title='Airbnb 가격 분포 (50만원 이하)',
                                  color_discrete_sequence=['#8A2BE2'])
        st.plotly_chart(fig_airbnb, use_container_width=True)
        
    with tab3:
        st.subheader("외국인 도시민박업 집중 지역 (전국 Top 15)")
        df_fore_active = df_fore[df_fore['영업상태명'] == '영업/정상'].copy()
        df_fore_active['구'] = df_fore_active['소재지전체주소'].str.split(' ', expand=True)[1]
        fore_counts = df_fore_active['구'].value_counts().head(15).reset_index()
        fore_counts.columns = ['구', '업체수']
        fig_fore = px.bar(fore_counts, x='구', y='업체수', color='업체수', 
                          color_continuous_scale='Reds', title='도시민박업 Top 15 지역')
        st.plotly_chart(fig_fore, use_container_width=True)

    st.info("**분류**: 호텔 관광객은 중구/강남 선호, 자유여행 MZ세대는 마포/성동의 도시민박을 선호하는 뚜렷한 경향을 보입니다.")

# 5. 사업 전략 제안
elif category == "사업 전략 제안":
    st.title("🎯 데이터 기반 사업 전략 제안")
    
    st.subheader("1️⃣ MZ세대 맞춤형 'K-트렌드' 패키지")
    st.markdown("""
    - **타겟**: 2030 중국/일본/미국 관광객
    - **내용**: 마포(홍대) 숙소를 거점으로 성수동 팝업스토어 투어, '인생샷' 스팟 가이딩.
    - **차별점**: 전통 유적지 대신 현재 실시간으로 유행하는 로컬 경험 제공.
    """)
    
    st.subheader("2️⃣ 인천공항 연계 프리미엄 'Zero-Wait' 픽업")
    st.markdown("""
    - **근거**: 입국객의 70% 이상이 인천공항 이용.
    - **내용**: 공항 픽업 + 숙소 체크인 보조 + 첫 서울 식사 예약 대행.
    - **수익모델**: 숙박 결합 시 할인, 단독 이용 시 프리미엄 과금.
    """)
    
    st.subheader("3️⃣ 에어비앤비-로컬 호스트 투어 연계")
    st.markdown("""
    - **근거**: 마포구의 압도적인 도시민박 공급량.
    - **내용**: 호텔 투숙객이 아닌 민박 투숙객을 위한 '동네 전문가(Local Host)' 투어.
    - **전략**: 마포구 소재 업체들과의 파트너십을 통한 독점 상품화.
    """)
    
    st.divider()
    st.markdown("### 📈 기대 효과")
    st.success("데이터 기반 타겟팅을 통하여 마케팅 비용 20% 절감 및 MZ세대 고객 만족도 30% 증가 예상")

# 푸터
st.sidebar.markdown("---")
st.sidebar.caption("Created by Antigravity Analysis Team")
