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

# 차량번호 cleaning 함수
def carnoclean(carno):
      
    if '(삭제)_고객사변경' in str(carno):
        return carno.replace('(삭제)_고객사변경', '')
    elif '_고객사변경' in str(carno):
        return carno.replace('_고객사변경', '')
    elif '__고객사변경' in str(carno):
        return carno.replace('__고객사변경', '')
    elif '(삭제)' in str(carno):
        return carno.replace('(삭제)', '')
    elif '(반납)' in str(carno):
        return carno.replace('(반납)', '')
    elif '(교체)' in str(carno):
        return carno.replace('(교체)', '')
    elif '(진행불가)' in str(carno):
        return carno.replace('(진행불가)', '')
    elif '(임시)' in str(carno):
        return carno.replace('(임시)', '')
    elif '(회수)' in str(carno):
        return carno.replace('(회수)', '')
    elif '(기존)' in str(carno):
        return carno.replace('(기존)', '')
    elif '(ㅅㅈ)' in str(carno):
        return carno.replace('(ㅅㅈ)', '')
    elif '__' in str(carno):
        return carno.replace('_', '')
    elif '_' in str(carno):
        return carno.replace('_', '')
    
    return carno

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

if st.button("분석하기"):
    sims_compare_merge = pd.merge(sims_this_raw, sims_prev_raw, on='법인명', how='left')
    sims_compare_merge['전주합계'] = sims_compare_merge['전주합계'].fillna(0)
    columns = ['법인명', 'RP코드_x', '사업자등록번호_x', '금주합계', '전주합계']
    sims_compare = sims_compare_merge[columns]
    sims_compare.columns = ['법인명', 'RP코드', '사업자등록번호', '금주합계', '전주합계']
    sims_compare["장착대수"] = np.where(sims_compare["금주합계"] - sims_compare["전주합계"] > 0, sims_compare["금주합계"] - sims_compare["전주합계"], 0)
    sims_compare["탈거대수"] = np.where(sims_compare["금주합계"] - sims_compare["전주합계"] < 0, sims_compare["전주합계"] - sims_compare["금주합계"], 0)
    sims_marketing_merge = pd.merge(sims_compare, customer, on='법인명', how='left')
    columns = ['법인명', 'RP코드_x', '사업자등록번호', '금주합계', '전주합계', '장착대수', '탈거대수', '순번', '영업유형(A)', '23하담당', '인입경로']
    sims_marketing = sims_marketing_merge[columns]
    sims_marketing.columns = ['법인명', 'RP코드', '사업자등록번호', '금주합계', '전주합계', '장착대수', '탈거대수', '순번', '영업유형', '영업담당', '인입경로']
    # 영업유형 미지정 고객사는 '일반' 으로 임의지정 
    sims_marketing['영업유형'] = sims_marketing['영업유형'].fillna('일반')
    sims_marketing['순번'] = sims_marketing['순번'].fillna(0)
    sims_marketing = sims_marketing.fillna('-')

    st.markdown('### 전체고객사별 리스트 ###')
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
st.header('월간데이터 분석')

uploaded_file = st.file_uploader('#### 1. CMS 엑셀파일을 업로드하세요 ####')

if uploaded_file is not None:

#read xls or xlsx
    cms_raw=pd.read_excel(uploaded_file)
    filename=uploaded_file.name
    # new_header = df1.iloc[0]
    # df1 = df1[1:]
    # df1.columns = new_header
    st.dataframe(cms_raw)

    st.write('업로드 전체 데이터수: ',cms_raw['carId'].count())
    st.write("---")
else:
    st.warning('엑셀파일을 업로드 하세요')

if st.button("CMS분석하기"):
    #시간 속성 필드값 datetime으로 type 변경
    cms_raw['차량생성일시'] = cms_raw['차량생성일시'].astype('datetime64[ns]')
    cms_raw['현재장착일'] = cms_raw['현재장착일'].astype('datetime64[ns]')
    cms_raw['마지막시동on'] = cms_raw['마지막시동on'].astype('datetime64[ns]')
    cms_raw['DEV_EUI'].fillna(0,inplace=True)
    cms_raw['차량번호(clean)'] = cms_raw['차량번호'].apply(carnoclean)

    # 유효한 차량 - 차량사용여부 '1', 단말기 일련번호 있는 차량과 HMG API(서비스유형 '8') 조건
    car_available = cms_raw.loc[((cms_raw['차량사용여부'] == 1) & (cms_raw['DEV_EUI'] != 0)) | (cms_raw['서비스유형'] == 8) ]
    st.write('유효한 차량대수:' , car_available['carId'].count())
    st.write('차량사용여부, 단말기 장착, HMG API 차량 포함')
    st.write("---")
    car_check_list = cms_raw.loc[(cms_raw['차량사용여부'] == 1) & (cms_raw['DEV_EUI'] == 0) & ~(cms_raw['서비스유형'] == 8) ]
    st.write('검증 대상 차량리스트 :', car_check_list['carId'].count())
    st.dataframe(car_check_list)
    st.write("---")
    # carId 기준 정렬
    car_available_sort = car_available.sort_values(by=['carId'])
    # carId 중복검증하기
    car_available_sort['carId중복'] = car_available_sort.duplicated(subset='carId', keep='last')
    carId_dup_count = car_available_sort['carId중복'].sum()
    carId_dup = car_available_sort.loc[car_available_sort['carId중복'] == True]
    st.write('[검증필요]carId중복 차량대수:', carId_dup_count)
    st.dataframe(carId_dup)
    # carId 중복없는 차량리스트
    carId_unique = car_available_sort.loc[car_available_sort['carId중복'] == False]
    # 차량번호 중복데이터 찾기, 최근 carid값을 남김, 중복값은 true로 표기
    carId_unique['차량번호중복'] = carId_unique.duplicated(subset='차량번호(clean)', keep=False)
    # 원본 차량번호와 cleansing한 차량번호가 동일한 carId는 중복 아닌 것으로 변경
    carId_unique.loc[(carId_unique['차량번호'] == carId_unique['차량번호(clean)']), '차량번호중복'] = False
    st.write("---")
    # 차량번호 중복 리스트 
    car_duplicate = carId_unique.loc[carId_unique['차량번호중복'] == True]
    st.write('[검증필요]차량번호 중복 리스트: ', car_duplicate['carId'].count())
    st.dataframe(car_duplicate)
    st.write("---")
    # 차량번호 중복제거 리스트
    car_unique = carId_unique.loc[carId_unique['차량번호중복'] == False]
    st.write('유효한 차량리스트 :', car_unique['carId'].count())
    st.dataframe(car_unique)
    st.write("---")
    #12월 장착차량
    d = st.date_input('#### 장착시작일자 입력 ####', value=None)
    st.write('장착시작일:', d)

    if d is not None:
      date = np.datetime64(d) # 입력받은 날짜는 date type으로 datetime64 로 변환해야 날짜 비교 가능
      baseData = car_unique.loc[(car_unique['차량생성일시'] >= date) & (car_unique['현재장착일'] >= date) ]
      baseCarId = baseData.iloc[0,1]
      st.write('12월 carId 시작번호', baseCarId)
      # 기준 carId 이후 생성차량 리스트
      month12 = car_unique.loc[(car_unique['carId'] >= baseCarId) ]
      st.write('### 당월 장착리스트 ###')
      st.write(month12['carId'].count())
      st.dataframe(month12)
      st.write("---")
    else:
      st.warning('기준일자를 입력 하세요')  


uploaded_file2 = st.file_uploader('#### 2. 거래처별 영업채널 엑셀파일을 업로드하세요 ####')
if uploaded_file2 is not None:
    customer=pd.read_excel(uploaded_file2)
    filename2=uploaded_file2.name

    st.write('고객사 개수: ', customer['순번'].count())
    st.dataframe(customer)
    st.write("---")
    # 신규 장착 거래처별 영업채널 매칭
    marketing_type = pd.merge(month12, customer, left_on='사업자번호', right_on='사업자번호', how='left')
    # 영업채널 미입력 거래처
    st.write('영업채널 미입력 거래처 : ', marketing_type['영업유형(A)'].isnull().count())
    st.dataframe(marketing_type.loc[marketing_type['영업유형(A)'].isna()])
    st.write("---")
    # 영업채널 미입력 거래처에 임의값 지정 - 일반
    marketing_type['영업유형(A)'] = marketing_type['영업유형(A)'].fillna('일반')
    st.write("### 고객사별 차량리스트 (영업채널/마케터) ###")
    columns = ['고객사', '사업자번호', 'RP코드_x', '계약번호', 'carId','차량번호(clean)','모델', '차량생성일시', '현재장착일', 'DEV_EUI','서비스구분','data_server', '영업유형(A)', '23하담당', '인입경로' ]
    carlist_col = marketing_type[columns]
    carlist_col.columns = ['고객사', '사업자번호', 'RP코드', '계약번호', 'carId','차량번호','차종', 'carId생성일시', '현재장착일', '단말기번호','서비스구분','데이터접속서버', '영업유형', '담당자', '인입경로' ]
    carlist_col['서비스구분'] = carlist_col['서비스구분'].fillna('-')
    carlist_col['인입경로'] = carlist_col['인입경로'].fillna('-')
    st.dataframe(carlist_col)
    st.write("---")
    # 영업채널별 차량대수
    st.write("### 영업채널별 차량대수 ###")
    marketing_source = carlist_col.pivot_table(values='차량번호', index=['영업유형'], aggfunc='count', margins ='True', fill_value=0)
    st.dataframe(marketing_source)
    st.write("---")
    # 고객사별 차량대수
    st.write("### 고객사별 차량대수 ####")
    customer_count = carlist_col.pivot_table(values='차량번호', index=['고객사', '영업유형'], aggfunc='count', margins ='True', fill_value=0)
    st.dataframe(customer_count)
    st.write("---")    


else:
    st.warning('엑셀파일을 업로드 하세요')

# with st.sidebar:
#     choice = option_menu("Menu", ["페이지1", "페이지2", "페이지3"],
#                          icons=['house', 'kanban', 'bi bi-robot'],
#                          menu_icon="app-indicator", default_index=0,
#                          styles={
#         "container": {"padding": "4!important", "background-color": "#fafafa"},
#         "icon": {"color": "black", "font-size": "25px"},
#         "nav-link": {"font-size": "16px", "text-align": "left", "margin":"0px", "--hover-color": "#fafafa"},
#         "nav-link-selected": {"background-color": "#08c7b4"},
#     }
#     )
