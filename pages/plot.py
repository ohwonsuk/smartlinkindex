import streamlit as st
from streamlit_option_menu import option_menu
import streamlit.components.v1 as html
from datetime import datetime, timedelta 
from dateutil.parser import parse #텍스트날짜를 날짜 형식으로 변경
from PIL import Image
import pandas as pd
import numpy as np
import plotly.express as px
import altair as alt
import io

import matplotlib.pyplot as plt
import seaborn as sns
plt.rcParams['figure.figsize'] = [12,8]
from IPython.display import set_matplotlib_formats

import os
import matplotlib.font_manager as fm  # 폰트 관련 용도 as fm

# def unique(list):
#     x = np.array(list)
#     return np.unique(x)

# @st.cache_data
# def fontRegistered():
#     font_dirs = [os.getcwd() + '/customFonts']
#     font_files = fm.findSystemFonts(fontpaths=font_dirs)

#     for font_file in font_files:
#         fm.fontManager.addfont(font_file)
#     fm._load_fontmanager(try_read_cache=False)

# fontRegistered()
# fontNames = [f.name for f in fm.fontManager.ttflist]
# fontname = st.selectbox("폰트 선택", unique(fontNames))
# st.write('애플 : AppleGothic')

# plt.rc('font', family=fontname)

# plt.rcParams["font.family"] = 'NanumGothic'
# 윈도우의 경우 'AppleGothic' 대신에 'Malgun Gothic'을 입력해주세요.

# minus 표출 오류 대응
plt.rcParams['axes.unicode_minus'] = False

st.header("스마트링크 연도별 월별 실적")

st.write('▹ 전체: 운영차량 전체')
st.write('▹ 외부: 스마트링크 가입 고객')
st.write('▹ 내부: SK렌터카 스마트케어/다이렉트/타고페이 등') 
st.write('▹ 임시: PoC, 장착 및 고객사변경 임시차량')
st.write('---')
kind = st.selectbox(
"조회 조건을 선택하세요",
("전체", "외부", "내부", '임시'),
index=None,
placeholder="선택하세요...",
)

if kind is not None:
    if kind == '전체':
        month_sum = pd.read_excel("month_sum(total).xlsx")
    elif kind == '외부':
        month_sum = pd.read_excel("month_sum(out).xlsx")
    elif kind == '내부':
        month_sum = pd.read_excel("month_sum(in).xlsx")
    else:
        month_sum = pd.read_excel("month_sum(temp).xlsx")

    month_sum_list = month_sum.iloc[:-1]
    with st.expander("월별 실적데이터"):
        st.dataframe(month_sum_list)


start_year, end_year = st.select_slider(
    '연도기간을 선택하세요',
    options=['2016', '2017', '2018', '2019', '2020', '2021', '2022', '2023', '2024'],
    value=('2016', '2024'))
st.write('선택된 기간: ', start_year, '년 -', end_year, ' 년')
st.caption('🖐🏻 시작과 끝을 동일연도로 선택시 해당 연도 데이터만 표출됩니다.')

option = st.selectbox(
    "신규장착, 탈거대수, 실장착대수 중에서 조회 데이터 선택",
    ("신규장착대수", "탈거대수", "실장착대수"),
    index=None,
    placeholder="종류 선택하기",
)

# st.write('선택된 데이터:', option)

# if option is not None:
#     if option == '기존 데이터 불러오기':
#             month_sum = pd.read_excel("month_sum.xlsx")

if option is not None:
    # month_sum = pd.read_excel("month_sum.xlsx")
    # month_sum_list = month_sum.iloc[:-1]
    # with st.expander("월별 실적데이터"):
    #     st.dataframe(month_sum_list)
    
    s_year = int(start_year)
    e_year = int(end_year)
    gap_year = e_year - s_year
    if gap_year == 0:
        if s_year == 2016:
            month_sum_plot = month_sum_list.iloc[0:2]
            st.dataframe(month_sum_plot)
        # elif s_year == 2024:
        #     count = (s_year  - 2016 - 1) * 12 + 2
        #     month_sum_plot = month_sum_list.iloc[count:]
        else:
            count = s_year - 2016 - 1
            start = 2 + count*12
            end = start + 12
            month_sum_plot = month_sum_list.iloc[start:end]
            st.dataframe(month_sum_plot)

        st.write('월별 신규 장착대수')
        st.bar_chart(month_sum_plot, x='기준월' , y= option)
        st.write('월별 누적 차량대수')
        st.line_chart(month_sum_plot, x='기준월' , y='누적차량대수', color='#F9051C', )

        fig, ax = plt.subplots(figsize=(10,6))
        ax.plot(month_sum_plot['장착대수'], label=option)
        ax.plot(month_sum_plot['누적차량대수'], label='누적차량대수')
        ax.set_xlabel('기준월')
        ax.set_ylabel('차량대수')
        ax.legend()
        st.pyplot(fig)
    else:
        if s_year == 2016:
            count = 2+ gap_year * 12
            month_sum_plot = month_sum_list.iloc[0:count]
        else:
            count = s_year - 2016 -1
            start = 2 + (count)*12
            end = start + (gap_year+1)*12
            month_sum_plot = month_sum_list.iloc[start:end]

        st.write('월별 '+ option)
        st.bar_chart(month_sum_plot, x='기준월' , y=option)
        st.write('월별 누적 차량대수')
        st.line_chart(month_sum_plot, x='기준월' , y='누적차량대수', color='#F9051C', )

        # fig, ax = plt.subplots(figsize=(10,6))
        # ax.plot(month_sum_plot[option], label=option)
        # ax.plot(month_sum_plot['누적차량대수'], label='누적차량대수')
        # ax.set_xlabel('기준월')
        # ax.set_ylabel('차량대수')
        # ax.legend()
        # st.pyplot(fig)

st.write('---')

st.subheader(':blue[계약종료 고객사 리스트]')

if st.button('데이터불러오기', key=1):
    nouse_list = pd.read_excel("nouse_customer.xlsx", dtype={ '종료연월': str})
    with st.expander("계약해지 고객사"):
        st.dataframe(nouse_list)
else:
    st.write('버튼을 선택하세요')


    # fig1, ax = plt.subplots()
    # ax.hist(month_sum, bins=100)
    # plt.ylabel('누적차량대수')
    # plt.xlabel('기준월')
    
    # st.pyplot(fig1)

    # total_length = len(month_sum_plot.index)
    # ax = month_sum_plot.plot(kind="bar", x="기준월", y="장착대수", color="Green", fontsize=10)

    # ax2 = month_sum_plot.plot(kind="line", x="기준월", y="누적차량대수", secondary_y=True, color="Red", ax=ax)

    # plt.title("월별 신규 장착 및 누적 차량대수")
    # ax.set_ylabel("신규장착")
    # ax2.set_ylabel("누적")
    # # x축 눈금설정 간격조정
    # ax.set_xticks(np.arange(1, total_length+1, 12))
    # st.show()