import numpy as np
import pandas as pd

months = {"january": 1,"february": 2,"march": 3,"april": 4, "may": 5,"june": 6,"july": 7, "august": 8,"september": 9,"october": 10,"november": 11,"december": 12}
phases = {'New Moon': 0, 'First Quarter': 0.5, 'Third Quarter': 0.5, 'Full Moon': 1}

# 데이터셋 불러오기
meteor_showers = pd.read_csv("./data/meteorshowers.csv")
moon_phases_2026 = pd.read_csv("./data/moon_phases_2026.csv")
constellations = pd.read_csv("./data/constellations.csv")
cities = pd.read_csv("./data/cities.csv")

#항아 데이터 추가
change_meteor_shower = {'name' : "Chang\'e", 'radiant' : 'Draco', 'bestmonth' : 'october', 'startmonth': 'october', 'startday' : 1,
                        'endmonth' : 'october', 'endday' : 31, 'hemisphere' : 'northern', 'preferredhemisphere' : 'northern' }
change_meteor_shower_df = pd.DataFrame(change_meteor_shower,index = [0])
meteor_showers = pd.concat([meteor_showers,change_meteor_shower_df],axis=0)

draco_constellation = {'constellation' : 'Draco', 'bestmonth' : 'july', 'latitudestart' : 90, 'latitudeend' : -15, 'besttime' :2100, 'hemisphere' : 'northern'}
draco_constellation_df = pd.DataFrame(draco_constellation, index = [0])
constellations = pd.concat([constellations,draco_constellation_df],axis=0)

# text -> int 월로 변경
def change_month(month):
    return months[month]

# 별자리 관측
def predict_best_meteor_shower_viewing(city):
    if not city in cities.values:
        return f'{city} 지역에 관한 별자리 관측 서비스 지원이 불가능합니다.'
    
    latitude = cities[cities['city'] == city]['latitude'].iloc[0]
    constellations_list = constellations[(constellations['latitudestart'] >= latitude) & (constellations['latitudeend'] <= latitude)]['constellation'].to_list()
    
    if not constellations_list:
        meteor_shower_string = f'{city} 지역에서는 관측할 수 있는 별자리가 없습니다.'

    meteor_shower_string = f'{city} 지역에 관한 별자리 관측 서비스 지원이 가능합니다.'

    for constell in constellations_list:
        name = meteor_showers[meteor_showers['radiant']  == constell]['name'].iloc[0]
        radiant =  meteor_showers[meteor_showers['radiant']  == constell]['radiant'].iloc[0]
        meteor_showers_startdate = pd.to_datetime(meteor_showers[meteor_showers['radiant']  == constell]['startdate']).iloc[0]
        meteor_showers_enddate = pd.to_datetime(meteor_showers[meteor_showers['radiant']  == constell]['enddate']).iloc[0]
        moon_phases_2026['date'] = pd.to_datetime(moon_phases_2026['date'])
        moon_phase_list = moon_phases_2026.loc[(moon_phases_2026['date'] >= meteor_showers_startdate) & (moon_phases_2026['date'] <= meteor_showers_enddate)]
        best_moon_date = moon_phase_list.loc[moon_phase_list['percentage'].idxmin()]['date'].strftime('%Y-%m-%d')
        meteor_shower_string = f"{name}를 잘 보려면 {radiant}자리 위치를 향하여 {best_moon_date}날짜에 보시면 관측이 잘됩니다."
        print(meteor_shower_string)
    return  meteor_shower_string, name, meteor_showers_startdate, meteor_showers_enddate,best_moon_date

# 컬럼 dtype 변경
meteor_showers['bestmonth'] = meteor_showers['bestmonth'].map(months)
meteor_showers['startmonth'] = meteor_showers['startmonth'].map(months)
meteor_showers['endmonth'] = meteor_showers['endmonth'].map(months)
constellations['bestmonth'] = constellations['bestmonth'].apply(change_month) #apply 사용

# Datetime 변환
meteor_showers['startdate'] = pd.to_datetime('2026'+ meteor_showers['startmonth'].astype(str).str.zfill(2) + meteor_showers['startday'].astype(str).str.zfill(2), format='%Y%m%d')
meteor_showers['enddate'] = pd.to_datetime('2026'+ meteor_showers['endmonth'].astype(str).str.zfill(2) + meteor_showers['endday'].astype(str).str.zfill(2), format='%Y%m%d')
moon_phases_2026['percentage'] = moon_phases_2026['moonphase'].map(phases)

# 불필요한 프레임 삭제하기
meteor_showers = meteor_showers.drop(['preferredhemisphere', 'startmonth','startday','endmonth','endday'],axis=1)
constellations =  constellations.drop(['besttime'],axis=1)
moon_phases_2026['percentage'] = moon_phases_2026['percentage'].ffill().fillna(0)

#유성우 관측 기간 조회
predict_best_meteor_shower_viewing('Seoul')
