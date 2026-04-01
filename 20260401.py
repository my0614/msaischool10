import pandas as pd, seaborn as sns, numpy as np, folium
import matplotlib.pyplot as plt

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
plt.rc('font', family='Malgun Gothic', size=15)
plt.figure(figsize=(15,4))
plt.title('시간대별 따릉이 이용건수')

count = bikes['대여시간대'].value_counts().sort_index()
#plt.bar(count.index, count.values) # matplot 
# count.plot(kind='bar') # pandas에서 제공하는 plot
#sns.countplot(data=bikes, x='대여시간대', color='pink', hue='주말구분')

df = bikes.groupby(['주말구분', '일자', '대여시간대'])['자전거번호'].count().reset_index()

hourly_dayofweek_ride = df.pivot_table(
    index='대여시간대',
    columns='주말구분',
    values='자전거번호',
    aggfunc='mean'
)


hourly_dayofweek_ride = hourly_dayofweek_ride[['주말', '평일']]
plt.figure(figsize=(10,6))
sns.heatmap(
    hourly_dayofweek_ride,
    annot=True,
    fmt='.1f',
    annot_kws={'size':8},
    cmap='Blues',
)

plt.title('주말 vs 평일 시간대별 평균 이용량')
plt.show()