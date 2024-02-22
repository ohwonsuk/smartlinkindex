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

# import matplotlib.font_manager as fm
# fm.get_fontconfig_fonts()

plt.rcParams["font.family"] = 'AppleGothic'
# 윈도우의 경우 'AppleGothic' 대신에 'Malgun Gothic'을 입력해주세요.

#retina  화면 선명도 개선
set_matplotlib_formats('retina')

# minus 표출 오류 대응
plt.rcParams['axes.unicode_minus'] = False


st.title('스마트링크 운영차량 관리')
st.header('연간 월별 실적')

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

def dateformat(date):
    if len(date) >= 7:
        return parse(date)
    
    return date

# 내부/외부/임시 구분
def companykind(company):
    if '스마트케어' in str(company):
        return '내부'
    elif '다이렉트' in str(company):
        return '내부'
    elif '타고페이' in str(company):
        return '내부'
    elif '준장기' in str(company):
        return '내부'
    elif '제주지점' in str(company):
        return '내부'
    elif '직영' in str(company):
        return '내부'
    elif 'PoC' in str(company):
        return '임시'
    elif '스마트링크' in str(company):
        return '임시'
    elif '내부' in str(company):
        return '임시'
    elif '계원' in str(company):
        return '임시'
    elif 'SKCarRental' in str(company):
        return '임시'
    elif company == '-':
        return '임시'
    elif company == 'SKM&S':
        return '임시'
    
    return '외부'


uploaded_file = st.file_uploader('#### CMS 엑셀파일을 업로드하세요 ####')

if uploaded_file is not None:

#read xls or xlsx
    cms_raw=pd.read_excel(uploaded_file, dtype={ 18: str,19: str})
    filename=uploaded_file.name
    # new_header = df1.iloc[0]
    # df1 = df1[1:]
    # df1.columns = new_header
    with st.expander("전체 차량정보"):
        st.dataframe(cms_raw)

    st.write('업로드 전체 데이터수: ',cms_raw['carId'].count())
    st.write("---")

    
    #당월 장착차량
    d = st.date_input('##### 데이터 기준일자 입력 #####', value=None)
    st.write('데이터 추출일자:', d)
    if d is not None:
        # date = datetime(d) # 입력받은 날짜는 date type으로 datetime64 로 변환해야 날짜 비교 가능
        guide_date = np.datetime64(d)

        #시간 속성 필드값 datetime으로 type 변경, 단말미매칭차량 '0' 입력, 차량번호 clean 필드생성
        cms_raw['계약시작일자'] = cms_raw['계약시작일자'].astype('str')
        cms_raw['계약종료일자'] = cms_raw['계약종료일자'].astype('str')
        cms_raw['계약시작일자(clean)'] = cms_raw['계약시작일자'].apply(dateformat)
        cms_raw['계약종료일자(clean)'] = cms_raw['계약종료일자'].apply(dateformat)
        cms_raw['계약시작일자(clean)'] = cms_raw['계약시작일자(clean)'].apply(pd.to_datetime)
        cms_raw['계약종료일자(clean)'] = cms_raw['계약종료일자(clean)'].apply(pd.to_datetime)
        cms_raw['서비스유형'] = cms_raw['서비스유형'].fillna(0)
        cms_raw['서비스유형'] = cms_raw['서비스유형'].astype('int')
        cms_raw['차량생성일시'] = cms_raw['차량생성일시'].astype('datetime64[ns]')
        cms_raw['현재장착일'] = cms_raw['현재장착일'].astype('datetime64[ns]')
        cms_raw['마지막시동on'] = cms_raw['마지막시동on'].astype('datetime64[ns]')
        cms_sort = cms_raw.sort_values(by=['carId'])
        cms_sort['DEV_EUI'].fillna(0,inplace=True)

        # 미입력 고객사 및 고객사명 '-' 로 된 차량은 'Smartlink PoC' 로 대체
        cms_sort.loc[cms_sort['고객사'].isnull(), '고객사'] = 'Smartlink PoC'
        cms_sort.loc[cms_sort['고객사'] == '-', '고객사'] = 'Smartlink PoC'
        cms_sort.loc[cms_sort['고객사'].isnull()]
        cms_sort['차량번호(clean)'] = cms_sort['차량번호'].apply(carnoclean)

        # 시작연월 추출하기, 차량생성일자 23년12월31일 이후 단말시리얼 없고, 서비스유형 8(HMG API) 아닌 차량을 미장착으로 구분
        min_date = pd.to_datetime('2016-12-31')
        compare_date = pd.to_datetime('2023-12-31')
        cms_sort['시작연월'] = cms_sort['차량생성일시'].dt.strftime("%Y%m")
        cms_sort.loc[(cms_sort['차량생성일시'] > cms_sort['현재장착일']) & (cms_sort['현재장착일'] > min_date ) , '시작연월'] = cms_sort['현재장착일'].dt.strftime("%Y%m")

        cms_sort.loc[(cms_sort['DEV_EUI'] == 0) & (cms_sort['서비스유형']!= 8) & (cms_sort['차량생성일시'] > compare_date), '시작연월'] = '미장착'
        
        # 차량사용 여부에 따른 차량 구분
        cms_on = cms_sort.loc[cms_sort['차량사용여부'] == 1]
        cms_off = cms_sort.loc[cms_sort['차량사용여부'] == 0]

        # 미사용 차량 종료연월 입력
        cms_off['종료일자'] = cms_off['차량갱신일시']
        cms_off.loc[cms_off['마지막시동on'] < cms_off['계약종료일자'], '종료일자'] = cms_off['마지막시동on']
        cms_off.loc[cms_off['계약종료일자(clean)'] < cms_off['차량갱신일시'], '종료일자'] = cms_off['계약종료일자(clean)']
        cms_off.loc[cms_off['탈거완료작업일자'] > cms_off['마지막시동on'], '종료일자'] = cms_off['탈거완료작업일자']
        cms_off['종료연월'] = cms_off['종료일자'].dt.strftime("%Y%m")

        # 미사용 차량 리스트 추출
        columns = ['carId','종료일자', '종료연월']
        cms_off_list = cms_off[columns]
        # 전체 차량중 미사용차량에 종료연월 필드 추가하기
        cms_onoff_merge = pd.merge(cms_sort, cms_off_list, left_on='carId', right_on='carId', how='left')

        # 작업 기준일자 필드 추가
        cms_onoff_merge['기준일자'] = pd.to_datetime(guide_date)

        # 고객사 타입 구분 - 외부/내부(SKR)/임시(운영센터 및 개발검증)
        cms_onoff_merge['구분'] = cms_onoff_merge['고객사'].apply(companykind)
        columns = ['고객사','사업자번호','구분','carId','차량번호(clean)','차량사용여부','DEV_EUI','시작연월', '종료연월', '차량생성일시','차량갱신일시','현재장착일','사용시작작업일자','탈거완료작업일자','마지막시동on','계약시작일자(clean)', '계약종료일자(clean)', '차량번호', '기준일자']
        cms_onoff_list = cms_onoff_merge[columns]

        # 당월 미장착 차량 제외한 차량리스트 기준 차량사용여부에 따른 차량 구분
        cms_avail_list = cms_onoff_list.loc[cms_onoff_list['시작연월'] != '미장착']
        cms_use = cms_avail_list.loc[cms_avail_list['차량사용여부'] == 1]
        cms_nouse = cms_avail_list.loc[cms_avail_list['차량사용여부'] == 0]
        cms_nouse_month = cms_nouse[['고객사','구분', '종료연월']]
        cms_nouse_month_sorting = cms_nouse_month.sort_values(['고객사','종료연월'], ascending = [True, True])

        # 서비스 종료 고객사 리스트 - 마지막 탈거 종료연월 추출하기
        nouse_month = cms_nouse_month_sorting.drop_duplicates(subset='고객사',keep='last')

        # 차량사용여부에 따른 고객사별 사용/미사용 차량대수
        cms_nouse_customer = cms_nouse.pivot_table(values='차량번호', index=['고객사'], aggfunc='count', margins ='True', fill_value=0)
        cms_use_customer = cms_use.pivot_table(values='차량번호', index=['고객사'], aggfunc='count', margins ='True', fill_value=0)

        cms_onoff_merge = pd.merge(cms_nouse_customer, cms_use_customer, left_on='고객사', right_on='고객사', how='left')
        cms_onoff_merge['차량번호_y'] = cms_onoff_merge['차량번호_y'].fillna(0)
        cms_onoff_merge['차량번호_y'] = cms_onoff_merge['차량번호_y'].astype('int')
        cms_off_customer_month = pd.merge(cms_onoff_merge, nouse_month, left_on='고객사', right_on='고객사', how='left')

        # 계약 해지 고객사 리스트 및 차량대수 
        nouse_customer_list = cms_off_customer_month.loc[(cms_off_customer_month['차량번호_y'] == 0) & (cms_off_customer_month['구분'] =='외부')]
        nouse_customer_sort = nouse_customer_list.sort_values(['종료연월','고객사'], ascending = [True, True])
        col = ['고객사', '차량번호_x', '구분', '종료연월']
        nouse_customer = nouse_customer_sort[col]
        nouse_customer.rename(columns={'차량번호_x': '차량대수'}, inplace=True)
        nouse_list = nouse_customer.reset_index(drop=True)
        nouse_list.to_excel("nouse_customer.xlsx", index=False)
        st.write('고객사 서비스 종료시기 및 대수')
        st.dataframe(nouse_list)
        st.write("---")

        # 계약 종료 고객사 수
        nouse_customer_table = nouse_customer.pivot_table(values='고객사', index=['종료연월'], aggfunc='count', margins ='True', fill_value=0)
        
        with st.expander("월별 계약종료 고객사수"):
            st.dataframe(nouse_customer_table)
        st.write("---")

        st.write('전체: 운영차량 전체, 외부: 스마트링크 가입 고객사, 내부: SK렌터카 상품, 임시: PoC, 장착 및 고객사변경 임시차량')
        kind = st.selectbox(
        "고객사 구분을 선택하세요",
        ("전체", "외부", "내부", '임시'),
        index=None,
        placeholder="선택하세요...",
        )

        st.write('선택된 값:', kind)


        if kind is not None:
        # 고객사 구분에 따른 분석 데이터 전환 - 전체, 외부, 내부, 임시
        # kind = '외부'
            if kind == '전체':
                target = cms_avail_list.copy(deep=True)
            else:
                target = cms_avail_list.loc[cms_avail_list['구분'] == kind]

            # 월별 신규 장착대수 합계
            month_new_sum = target.pivot_table(values='차량사용여부', index='시작연월', aggfunc='count', margins ='True', fill_value=0)

            # 월별 탈거대수 합계
            month_off_sum = target.pivot_table(values='차량사용여부', index='종료연월', aggfunc='count', margins ='True', fill_value=0)

            month_new_sum.reset_index(inplace=True)
            month_off_sum.reset_index(inplace=True)

            # 신규/탈거 대수 합치기
            month_history = pd.merge(month_new_sum, month_off_sum, left_on='시작연월', right_on='종료연월', how='left')

            month_history.columns = ['기준월', '신규장착대수', '탈거월', '탈거대수']
            columns = [ '기준월', '신규장착대수', '탈거대수']
            month_sum = month_history[columns]
            month_sum['탈거대수'] = month_sum['탈거대수'].fillna(0)
            month_sum = month_sum.astype({'탈거대수': 'int'})
            month_sum['실장착대수'] = month_sum['신규장착대수'] - month_sum['탈거대수']
            #누적 차량대수 구하기
            month_sum['누적차량대수'] = month_sum['실장착대수'].cumsum()
            month_sum.to_excel(f"month_sum({kind}).xlsx", index=False)
            st.write('월별 누적 차량대수')
            st.dataframe(month_sum)
            st.write("---")

else:
    st.write('파일 선택은 필수 입니다.')

# option = st.selectbox(
#     "도표 사용 데이터 선택하기",
#     ("기존 데이터 불러오기", "신규 데이터"),
#     index=None,
#     placeholder="데이터선택하기",
# )

# st.write('선택된 데이터:', option)

# if option is not None:
#     if option == '기존 데이터 불러오기':
#             month_sum = pd.read_excel("month_sum.xlsx")

#     month_sum_plot = month_sum.iloc[:-1]
#     st.line_chart(month_sum_plot, x='기준월' , y='누적차량대수')

        # total_length = len(month_sum_plot.index)
        # ax = month_sum_plot.plot(kind="bar", x="기준월", y="장착대수", color="Green", fontsize=10)

        # ax2 = month_sum_plot.plot(kind="line", x="기준월", y="누적차량대수", secondary_y=True, color="Red", ax=ax)

        # plt.title("월별 신규 장착 및 누적 차량대수")
        # ax.set_ylabel("신규장착")
        # ax2.set_ylabel("누적")
        # # x축 눈금설정 간격조정
        # ax.set_xticks(np.arange(1, total_length+1, 12))
        # plt.tight_layout()
        # plt.show()

