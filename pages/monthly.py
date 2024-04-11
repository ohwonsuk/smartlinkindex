import streamlit as st
from streamlit_option_menu import option_menu
import streamlit.components.v1 as html
from datetime import datetime, timedelta 
from PIL import Image
import pandas as pd
import numpy as np
import plotly.express as px
import io

st.title('스마트링크 운영차량 관리')
st.header('월간데이터 분석')

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


uploaded_file = st.file_uploader('#### 1. CMS 엑셀파일을 업로드하세요 ####')

if uploaded_file is not None:

#read xls or xlsx
    cms_raw=pd.read_excel(uploaded_file)
    filename=uploaded_file.name
    # new_header = df1.iloc[0]
    # df1 = df1[1:]
    # df1.columns = new_header
    with st.expander("전체 차량정보"):
        st.dataframe(cms_raw)

    st.write('업로드 전체 데이터수: ',cms_raw['carId'].count())
    st.write("---")


# if st.button("CMS분석하기"):
    
    #당월 장착차량
    d = st.date_input('##### 장착시작일자 입력 #####', value=None)
    st.write('장착시작일:', d)
    if d is not None:
        # date = datetime(d) # 입력받은 날짜는 date type으로 datetime64 로 변환해야 날짜 비교 가능
        pending_d = d + timedelta(days=15) # 15일 이후 등록차량 제외하기 위한 날짜계산
        start_date = np.datetime64(d)
        pending_date = np.datetime64(pending_d)

        #시간 속성 필드값 datetime으로 type 변경, 단말미매칭차량 '0' 입력, 차량번호 clean 필드생성
        cms_raw['차량생성일시'] = cms_raw['차량생성일시'].astype('datetime64[ns]')
        cms_raw['현재장착일'] = cms_raw['현재장착일'].astype('datetime64[ns]')
        cms_raw['마지막시동on'] = cms_raw['마지막시동on'].astype('datetime64[ns]')
        cms_raw['DEV_EUI'].fillna(0,inplace=True)
        cms_raw['차량번호(clean)'] = cms_raw['차량번호'].apply(carnoclean)

        # 주유/하이패스카드 정보 차량번호에 매칭하기
        fcard_list = pd.read_excel("fcard_list.xlsx", sheet_name='주유')
        hcard_list = pd.read_excel("hcard_list.xlsx", sheet_name='하이패스')
        cms_fcard_merge = pd.merge(cms_raw, fcard_list, left_on='차량번호(clean)', right_on='차량', how='left')
        cms_fcard_hcard_merge = pd.merge(cms_fcard_merge, hcard_list, left_on='차량번호(clean)', right_on='차량', how='left')
        cms_fcard_hcard_merge['id중복'] = cms_fcard_hcard_merge.duplicated(subset='carId', keep='last')
        car_card_clean = cms_fcard_hcard_merge.loc[cms_fcard_hcard_merge['id중복'] == False]
        with st.expander("보정한 차량데이터(카드매칭)"):
            st.dataframe(car_card_clean)


        # 유효한 차량 - 차량사용여부 '1', 단말기 일련번호 있는 차량과 HMG API(서비스유형 '8') 조건
        car_available = car_card_clean.loc[((car_card_clean['차량사용여부'] == 1) & (car_card_clean['DEV_EUI'] != 0)) | ((car_card_clean['차량사용여부'] == 1) & (car_card_clean['서비스유형'] == 8)) | ((car_card_clean['차량사용여부'] == 1) & (car_card_clean['주유'] == '법인(주유교통')) | ((car_card_clean['차량사용여부'] == 1) & (car_card_clean['하이패스'] == 'R하이패스(일반)')) ]
        st.write('유효한 차량대수:' , car_available['carId'].count())
        st.write('차량사용여부, 단말기 장착, HMG API 차량, 카드만 사용 차량 포함')
        st.write("---")
        car_check_list = car_card_clean.loc[(car_card_clean['차량사용여부'] == 1) & (car_card_clean['DEV_EUI'] == 0) & ~(car_card_clean['서비스유형'] == 8) & (car_card_clean['차량생성일시'] < pending_date) & (car_card_clean['주유'] != '법인(주유교통)') & (car_card_clean['하이패스'] != 'R하이패스(일반)') & (car_card_clean['하이패스'] != 'R하이패스(SIM)')]
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
        with st.expander("중복 차량데이터 확인하기"):
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
        with st.expander("차량데이터 확인"):
            st.dataframe(car_unique)
        st.write("---")
        car_unique.to_excel(f"car_unique({d}).xlsx", index=False)

        baseData = car_unique.loc[(car_unique['차량생성일시'] >= start_date) & (car_unique['현재장착일'] >= start_date) ]
        baseCarId = baseData.iloc[0,1]
        st.write('당월 carId 시작번호', baseCarId)
        # 기준 carId 이후 생성차량 리스트
        month = car_unique.loc[(car_unique['carId'] >= baseCarId) ]
        st.write('### 당월 장착리스트 ###')
        st.write(month['carId'].count())
        with st.expander("장착차량 확인"):
            st.dataframe(month)
        st.write("---")
        #월간 데이터 엑셀로 저장
        month.to_excel(f"month({d}).xlsx", index=False)
    else:
        st.warning('기준일자를 입력 하세요')  
else:
    st.warning('엑셀파일을 업로드 하세요')

st.write('#### 2. 장착월 선택하세요')
selectmonth = st.selectbox(
    "작업한 데이터로 24년도 조회월 선택",
    ("1월", '2월', '3월', '4월'),
    index=None,
    placeholder="조회월 선택하기",
)

if selectmonth is not None:
    monthlist = {'1월': '2024-01-01', '2월': '2024-02-01', '3월':'2024-03-01', '4월':'2024-04-01', '5월':'2024-05-01', '6월':'2024-06-01'}
    mon_num = monthlist.get(selectmonth)
    month = pd.read_excel(f"month({mon_num}).xlsx")
    with st.expander(f"{selectmonth} 장착차량 확인"):
        st.dataframe(month)

uploaded_file2 = st.file_uploader('#### 3. 거래처별 영업채널 엑셀파일을 업로드하세요 ####')
if uploaded_file2 is not None:
    customer=pd.read_excel(uploaded_file2)
    filename2=uploaded_file2.name

    st.write('고객사 개수: ', customer['순번'].count())
    with st.expander("고객사리스트 보기"):
        st.dataframe(customer)
    st.write("---")
    # 신규 장착 거래처별 영업채널 매칭
    marketing_type = pd.merge(month, customer, left_on='사업자번호', right_on='사업자번호', how='left')
    # 영업채널 미입력 거래처
    nochannel = marketing_type.loc[marketing_type['영업유형(A)'].isna()]
    st.write('영업채널 미입력 거래처 : ', nochannel['carId'].count())
    st.dataframe(marketing_type.loc[marketing_type['영업유형(A)'].isnull()])
    # st.dataframe(marketing_type)
    st.write("---")
    # 영업채널 미입력 거래처에 임의값 지정 - 일반
    marketing_type['영업유형(A)'] = marketing_type['영업유형(A)'].fillna('일반')
    st.write("### 고객사별 장착 차량리스트 (영업채널/마케터) ###")
    columns = ['고객사', '사업자번호', 'RP코드_x', '계약번호', 'carId','차량번호(clean)','모델', '유종', '차량생성일시', '현재장착일', 'DEV_EUI','서비스구분','data_server', '영업유형(A)', '변경담당자', '인입경로' ]
    carlist_col = marketing_type[columns]
    carlist_col.columns = ['고객사', '사업자번호', 'RP코드', '계약번호', 'carId','차량번호','차종', '유종', 'carId생성일시', '현재장착일', '단말기번호','서비스구분','데이터접속서버', '영업유형', '담당자', '인입경로' ]
    carlist_col['서비스구분'] = carlist_col['서비스구분'].fillna('-')
    carlist_col['인입경로'] = carlist_col['인입경로'].fillna('-')
    with st.expander("차량데이터 확인"):
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
