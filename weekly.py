import streamlit as st
from streamlit_option_menu import option_menu
import streamlit.components.v1 as html
import datetime
from PIL import Image
import pandas as pd
import numpy as np
import plotly.express as px
import altair as alt
import io


st.title('스마트링크 운영차량 관리')
st.sidebar.success("메뉴를 선택하세요")

st.header('SIMS 주간 실적 분석')

sims_prev_file = st.file_uploader('#### 1. SIMS 전주 통계 엑셀파일을 업로드하세요 ####')

if sims_prev_file is not None:
    sims_prev_raw=pd.read_excel(sims_prev_file)
    filename1=sims_prev_file.name
    sims_prev_raw = sims_prev_raw.iloc[1:-1]  # 첫번째행과 마지막행 제거
    sims_prev_raw.columns = ['법인명', 'RP코드', '사업자등록번호', '전주합계', '카셰어링(베이직)','카세어링(프리미엄)','차량운행관리(기본)', '차량운행관리(1년)', '차량운행관리(3년)', '차량관제','종량제','기타','Fleet Scheduler', '주유', '하이패스']
    st.dataframe(sims_prev_raw)
else:
    st.warning('SIMS 전주통계 엑셀파일을 업로드 하세요')

sims_this_file = st.file_uploader('#### 2. SIMS 금주 통계 엑셀파일을 업로드하세요 ####')

if sims_this_file is not None:
    sims_this_raw=pd.read_excel(sims_this_file)
    filename2=sims_this_file.name
    sims_this_raw = sims_this_raw.iloc[1:-1]  # 첫번째행과 마지막행 제거
    sims_this_raw.columns = ['법인명', 'RP코드', '사업자등록번호', '금주합계', '카셰어링(베이직)','카세어링(프리미엄)','차량운행관리(기본)', '차량운행관리(1년)', '차량운행관리(3년)', '차량관제','종량제','기타','Fleet Scheduler', '주유', '하이패스']
    st.dataframe(sims_this_raw)
else:
    st.warning('SIMS 금주통계 엑셀파일을 업로드 하세요')

uploaded_file2 = st.file_uploader('#### 3. 거래처별 영업채널 엑셀파일을 업로드하세요 ####')
if uploaded_file2 is not None:
    customer=pd.read_excel(uploaded_file2)
    filename2=uploaded_file2.name

    st.write('고객사 개수: ', customer['순번'].count())
    st.dataframe(customer)

st.write("---")
st.write("표기된 값은 최소값이며 수정사항 없으면 그대로 적용됩니다.")
data_sale = st.number_input('데이터판매 대수를 입력하세요', min_value=4170, value='min')
g_smartlink = st.number_input('G-Smartlink 대수를 입력하세요', min_value=399, value='min')


if st.button("분석하기"):
    sims_compare_merge = pd.merge(sims_this_raw, sims_prev_raw, on='법인명', how='left')
    sims_compare_merge['전주합계'] = sims_compare_merge['전주합계'].fillna(0)
    columns = ['법인명', 'RP코드_x', '사업자등록번호_x', '금주합계', '전주합계']
    sims_compare = sims_compare_merge[columns]
    sims_compare.columns = ['법인명', 'RP코드', '사업자등록번호', '금주합계', '전주합계']
    
    # 데이터판매(4,170대) 및 G-smartlink 대수(399대) 추가
    add_df = pd.DataFrame({'법인명':['G-스마트링크', '데이터판매'], 'RP코드': ['RP','RP' ], '사업자등록번호': ['111-11-11111','111-11-11111' ], '금주합계': [data_sale,g_smartlink], '전주합계': [data_sale,g_smartlink]})
    
    # 기존 SIMS에 추가
    total = pd.concat([sims_compare, add_df],axis=0, ignore_index=True)

    # 장착대수 및 탈거대수 비교 계산
    total["장착대수"] = np.where(total["금주합계"] - total["전주합계"] > 0, total["금주합계"] - total["전주합계"], 0)
    total["탈거대수"] = np.where(total["금주합계"] - total["전주합계"] < 0, total["전주합계"] - total["금주합계"], 0)
    # 합계 행 추가
    total.loc['합계',:] = total.loc[0:2129, '금주합계':'전주합계'].sum(axis=0)
    total = total.fillna('-')
    total = total.astype({'금주합계': 'int', '전주합계':'int'})  # 데이터 정수로 변경

    sims_marketing_merge = pd.merge(total, customer, on='법인명', how='left')
    columns = ['법인명', 'RP코드_x', '사업자등록번호', '금주합계', '전주합계', '장착대수', '탈거대수', '순번', '영업유형(A)', '변경담당자', '인입경로']
    sims_marketing = sims_marketing_merge[columns]
    sims_marketing.columns = ['법인명', 'RP코드', '사업자등록번호', '금주합계', '전주합계', '장착대수', '탈거대수', '순번', '영업유형', '영업담당', '인입경로']
    # 영업유형 미지정 고객사는 '일반' 으로 임의지정 
    sims_marketing['영업유형'] = sims_marketing['영업유형'].fillna('일반')
    sims_marketing['순번'] = sims_marketing['순번'].fillna(0)
    sims_marketing = sims_marketing.fillna('-')
    # 최종 합계 행은 그룹통계시 제외
    sims_marketing = sims_marketing.iloc[0:-1]  

    # 전체 고객사 및 대수 합계
    st.markdown('### 전체 고객사 및 대수 ###')
    st.write('데이터판매 ',data_sale,'대', 'G-smartlink ',g_smartlink,'대 포함')
    st.dataframe(total)
    st.write("---")

    st.markdown('### 전체고객사 영업채널매칭 ###')
    st.dataframe(sims_marketing)
    st.write("---")


    # 금주 신규장착 고객사 리스트
    new_customer = sims_marketing.loc[(sims_marketing['장착대수'] > 0) & (sims_marketing['전주합계'] == 0)]
    st.markdown('### 신규장착 고객사 ###')
    st.write('고객사 개수: ', new_customer['법인명'].count())
    st.dataframe(new_customer)
    st.write("---")

    # 금주 추가장착 고객사 리스트
    add_customer = sims_marketing.loc[(sims_marketing['장착대수'] > 0) & (sims_marketing['전주합계'] > 0)]
    st.markdown('### 추가장착 고객사 ###')
    st.write('고객사 개수: ', add_customer['법인명'].count())
    st.dataframe(add_customer)
    st.write("---")    

    # 금주 대수감소(탈거) 고객사 리스트
    decrease_customer = sims_marketing.loc[((sims_marketing['탈거대수'] - sims_marketing['장착대수']) > 0) & (sims_marketing['전주합계'] > 0)]
    st.markdown('### 대수감소(탈거대수 > 장착대수) 고객사 ###')
    st.write('고객사 개수: ', decrease_customer['법인명'].count())
    st.dataframe(decrease_customer)
    st.write("---")    

    weekly_table = sims_marketing.groupby(sims_marketing['영업유형']).sum()
    weekly_table.loc['합계',:] = weekly_table.sum(axis=0)
    weekly_columns = ['금주합계', '전주합계', '장착대수', '탈거대수']
    weekly_index = weekly_table[weekly_columns]
    st.markdown('#### 영업채널별 장착 및 탈거대수 ####')
    st.dataframe(weekly_index)
    st.write("---")

st.write("---")
