import pandas as pd
import matplotlib.pyplot as plt

# 데이터 읽기
df = pd.read_csv("./data/rocksamples.csv")

# 단위 변환 (g → kg)
df['Weight (kg)'] = df['Weight (g)'] / 1000

# -------------------------------
# 1. Mission별 샘플 총량 계산
# -------------------------------
Mission = (
    df.groupby('Mission')['Weight (kg)']
    .sum()
    .reset_index()
    .rename(columns={'Weight (kg)': 'Sample weight (kg)'})
)

# -------------------------------
# 2. 달 모듈 (LM)
# -------------------------------
Mission['Lunar module (LM)'] = [
    'Eagle (LM-5)', 'Intrepid (LM-6)', 'Antares (LM-8)',
    'Falcon (LM-10)', 'Orion (LM-11)', 'Challenger (LM-12)'
]

Mission['LM mass (kg)'] = [15103, 15235, 15264, 16430, 16445, 16456]

# -------------------------------
# 3. 명령 모듈 (CM)
# -------------------------------
Mission['Command Module (CM)'] = [
    'Columbia (CSM-107)', 'Yankee Clipper (CM-100)',
    'Kitty Hawk (CM-110)', 'Endeavor (CM-112)',
    'Casper (CM-113)', 'America (CM-114)'
]

Mission['CM Mass (kg)'] = [5560, 5609, 5758, 5875, 5840, 5960]

# -------------------------------
# 4. 총 무게 계산
# -------------------------------
Mission['Total weight (kg)'] = Mission['LM mass (kg)'] + Mission['CM Mass (kg)']

# -------------------------------
# 5. 비율 계산
# -------------------------------
saturnVPayload = 43500

Mission['Sample : Payload'] = Mission['Sample weight (kg)'] / saturnVPayload
Mission['Crewed area : Payload'] = Mission['Total weight (kg)'] / saturnVPayload
Mission['Sample : Crewed area'] = Mission['Sample weight (kg)'] / Mission['Total weight (kg)']

# -------------------------------
# 6. 아르테미스 데이터
# -------------------------------
artemis_crewedArea = 26520

artemis_dict = {
    'Mission': ['artemis1', 'artemis1b', 'artemis2'],
    'Total weight (kg)': [artemis_crewedArea]*3,
    'Payload (kg)': [26988, 37965, 42955]
}

artemis_mission = pd.DataFrame(artemis_dict)

# -------------------------------
# 7. 샘플 무게 추정
# -------------------------------
artemis_mission['Sample weight from total (kg)'] = (
    artemis_mission['Total weight (kg)'] * Mission['Sample : Crewed area'].mean()
)

artemis_mission['Sample weight from payload (kg)'] = (
    artemis_mission['Payload (kg)'] * Mission['Sample : Payload'].mean()
)

artemis_mission['Estimated sample weight (kg)'] = (
    artemis_mission['Sample weight from total (kg)'] +
    artemis_mission['Sample weight from payload (kg)']
) / 2

# -------------------------------
# 결과 출력
# -------------------------------
print("=== Apollo Mission ===")
print(Mission)

print("\n=== Artemis Estimate (mean) ===")
print(artemis_mission['Estimated sample weight (kg)'].mean())

# -------------------------------
# 8. 샘플 필터링 및 분석
# -------------------------------
df['Remaining (kg)'] = df['Weight (kg)'] * df['Pristine (%)'] * 0.01

# 조건 필터
low_samples = df[(df['Weight (kg)'] >= 0.16) & (df['Pristine (%)'] <= 50)]

needed_samples = low_samples[low_samples['Type'].isin(['Basalt','Breccia'])]
Crustal = df[df['Type'] == 'Crustal']

needed_samples = pd.concat([needed_samples, Crustal])

# -------------------------------
# Type별 집계 (최종 결과)
# -------------------------------
result = needed_samples.groupby('Type')['Weight (kg)'].agg(['sum', 'mean']).reset_index()
result.columns = ['Type','Total weight (kg)', 'Average weight (kg)']
count_df = df['Type'].value_counts()

results = pd.merge(result, count_df, on='Type')
needed_samples_overview = results.rename(columns={'count' : 'Number of samples'})

needed_samples_overview['Percentage of rocks'] = needed_samples_overview['Number of samples'] / needed_samples_overview['Number of samples'].sum()
needed_samples_overview['Weight to collect'] = needed_samples_overview['Percentage of rocks'] * artemis_mission['Estimated sample weight (kg)'].mean()
needed_samples_overview['Rocks to collect'] = needed_samples_overview['Weight to collect'] /needed_samples_overview['Average weight (kg)']
print(needed_samples_overview)

print("=" * 30)
print("암석별 필요한 개수")
print("=" * 30)
for t in range(len(needed_samples_overview)):
    print(f"{needed_samples_overview['Type'][t]}은 최소 {round(needed_samples_overview['Rocks to collect'][t],2)}개가 필요하고개당,  {round(needed_samples_overview['Weight to collect'][t],2)} kg이상이여야합니다")
# -------------------------------
# 9. 시각화 (옵션)
# -------------------------------
# plt.figure()
# plt.bar(result['Type'], result['Total weight (kg)'])
# plt.title('Total Weight by Type')
# plt.show()