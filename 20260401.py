import pandas as pd, seaborn as sns, numpy as np, folium
import matplotlib.pyplot as plt
import json

temp = []
days = np.array(['월','화','수','목', '금', '토','일'])

for idx in range(1, 7):
    bike = pd.read_csv(f"./data/bike_rent_{idx}.csv", encoding='cp949', parse_dates=['대여일시'])
    temp.append(bike)

bikes = pd.concat(temp, axis=0, ignore_index=True) # ignore_index 사용하여 index 중복제거
pd.options.display.float_format='{:.2f}'.format # 포맷팅

# 시간계산에 따른 컬럼 추가
bikes['일자'] = bikes['대여일시'].dt.day
bikes['대여시간대'] = bikes['대여일시'].dt.hour
bikes['요일'] = days[bikes['대여일시'].dt.dayofweek]
bikes['주말구분'] = np.where(bikes['대여일시'].dt.dayofweek < 5, '평일','주말') # np.where 조건

# bikes와 bike_shop merge
bike_shop = pd.read_csv("./data/bike_shop.csv", encoding='cp949')
bike_temp = bike_shop[['구분','대여소번호','위도','경도']]
bikes = pd.merge(bikes,bike_temp, left_on='대여 대여소번호', right_on='대여소번호')
bikes = bikes.rename(columns={'구분': '대여구', '위도':'대여점위도', '경도' : '대여점경도'})

#데이터 시각화
plt.rc('font', family='Malgun Gothic', size=12)
count = bikes['대여시간대'].value_counts().sort_index()

# 이용량이 많은 대여소 top 10 marker 출력
holiy_top10 = bikes.pivot_table(
    index=['대여 대여소명','대여점위도','대여점경도'],
    columns='주말구분',
    values='이용시간',
    aggfunc='count'
).sort_values('주말',ascending=False)

daliy_top10 = bikes.pivot_table(
    index=['대여 대여소명','대여점위도','대여점경도'],
    columns='주말구분',
    values='이용시간',
    aggfunc='count'
).sort_values('평일',ascending=False)

holiy_top10 = holiy_top10.reset_index().head(10)
lat = holiy_top10['대여점위도'].mean()
lon = holiy_top10['대여점경도'].mean()

daliy_top10 = daliy_top10.reset_index().head(10)
lat2 = daliy_top10['대여점위도'].mean()
lon2 = daliy_top10['대여점경도'].mean()
print(lat2,lon2)

map1 = folium.Map(location=[lat2,lon2]) 
for idx, mark in daliy_top10.iterrows():
    folium.Marker(
        location=[mark['대여점위도'], mark['대여점경도']],
        popup=mark['대여 대여소명'], icon=folium.Icon(color='blue', icon='bicycle', prefix='fa')
    ).add_to(map1)

map1.save('map.html')

