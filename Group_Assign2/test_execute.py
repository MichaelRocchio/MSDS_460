# %%
import pandas as pd
import numpy as np
import pulp
from itertools import chain, combinations
import statistics as stats
import matplotlib.pyplot as plt
import seaborn as sns


counties_df = pd.read_csv('data/uscounties_geo.csv', header=0)
counties_df = counties_df[counties_df['state_id'] == 'WA'].reset_index(drop=True)
counties_df

# %%
districts_df= pd.read_csv('data/county_districts.csv', header=0)
districts_df['county']=districts_df['county'].str.lstrip(' ').str.rstrip(' ')
counties_df['county']=counties_df['county'].str.lstrip(' ').str.rstrip(' ')
counties_df=counties_df.merge(districts_df, on='county', how='left')
counties_df

# %%
## white only census
census_df = pd.read_csv('data/census_demographics.csv', header=0)
census_df['WA_MALE']=pd.to_numeric(census_df['WA_MALE'])
census_df['WA_FEMALE']=pd.to_numeric(census_df['WA_FEMALE'])
census_df['WHITE_POP']=census_df['WA_MALE']+census_df['WA_FEMALE']
census_df = census_df.groupby(['COUNTY', 'CTYNAME'])[['TOT_POP', 'WHITE_POP']].sum().reset_index()
census_df['CTYNAME']=census_df['CTYNAME'].str.lstrip(' ').str.rstrip(' ')
census_df

# %%
# the strings arent joining but I can sort and join on the index
counties_df=counties_df.sort_values(by=['county']).reset_index(drop=True)
census_df=census_df.sort_values(by=['CTYNAME']).reset_index(drop=True)
counties_df=counties_df.merge(census_df, left_index=True, right_index=True, how='left')
for i,j in zip( census_df['CTYNAME'].to_list(), counties_df['county'].to_list()):
    print(i, '  ', j)

counties_df=counties_df.reset_index()
counties_df

# %%
# Washington has 10 districts
max_district = 10
counties_df['TOT_POP'] = counties_df['TOT_POP'].astype("int")
counties_df['WHITE_POP'] = counties_df['WHITE_POP'].astype("int")
counties_df['lat'] = counties_df['lat'].astype("float")
counties_df['lng'] = counties_df['lng'].astype("float")

max_district = 10
max_population = (counties_df['population'].sum() / max_district) * 1.5
statewide_white_percentage = counties_df['WHITE_POP'].sum() / counties_df['TOT_POP'].sum()

counties_lat_Dic = dict(zip(counties_df.county, counties_df.lat))
counties_Long_Dic = dict(zip(counties_df.county, counties_df.lng))
counties_Pop_Dic = dict(zip(counties_df.county, counties_df.TOT_POP))
counties_WhitePop_Dic = dict(zip(counties_df.county, counties_df.WHITE_POP))



# %%
county_adjacency = {}
with open("data/county_adjacency.txt", 'r', encoding='ISO-8859-1') as file:
    lines = file.readlines()

for line in lines:
    parts = line.strip().split('\t')
    if len(parts) < 4:
        continue
    county_fips = parts[1]
    if county_fips.startswith('53'):
        county_name = parts[0].replace('"', '')
        adjacent_county_fips = parts[3]
        adjacent_county_name = parts[2].replace('"', '')
        if county_name not in county_adjacency:
            county_adjacency[county_name] = []
        if adjacent_county_fips.startswith('53'):
            county_adjacency[county_name].append(adjacent_county_name)

# Create the adjacency matrix
sorted_counties = sorted(county_adjacency.keys())
adjacency_matrix = pd.DataFrame(0, index=sorted_counties, columns=sorted_counties, dtype=int)
for county, neighbors in county_adjacency.items():
    for neighbor in neighbors:
        adjacency_matrix.at[county, neighbor] = 1
        adjacency_matrix.at[neighbor, county] = 1

# Adjust the indices to match county names
county_index_to_name_map = counties_df['county'].to_dict()

index_to_county_map = {index: county for index, county in enumerate(counties_df['county'])}
from concurrent.futures import ThreadPoolExecutor, as_completed


# Your existing functions
def compactness(district):
    lat_list = [counties_lat_Dic[county] for county in district]
    long_list = [counties_Long_Dic[county] for county in district]
    lat_sd = stats.stdev(lat_list)
    long_sd = stats.stdev(long_list)
    return lat_sd + long_sd

def total_pop(district):
    pop_list = [counties_Pop_Dic.get(county, 0) for county in district]
    return sum(pop_list)

def white_pop_percentage(district):
    white_pop_list = [counties_WhitePop_Dic.get(county, 0) for county in district]
    total_pop_list = [counties_Pop_Dic.get(county, 0) for county in district]
    white_pop = sum(white_pop_list)
    total_pop = sum(total_pop_list)
    return (white_pop / total_pop) if total_pop > 0 else 0

# Helper function to calculate compactness and white population percentage in parallel
def calculate_objective_for_district(district):
    compactness_value = compactness(district)
    white_pop_percent_value = white_pop_percentage(district)
    return compactness_value, white_pop_percent_value

# Initialize the optimization model
redistrict_model = pulp.LpProblem("Redistricting Model", pulp.LpMinimize)
counties = counties_df['county'].tolist()
min_len = 2
max_len = 5
possible_districts = list(chain.from_iterable(combinations(counties, i) for i in range(min_len, max_len + 1)))
x = pulp.LpVariable.dicts('district', possible_districts, cat=pulp.LpBinary)

# Calculate objective values for each district in parallel
objective_compactness = []
objective_white_pop = []
with ThreadPoolExecutor(max_workers=4) as executor:  # Adjust the number of workers as needed
    future_to_district = {executor.submit(calculate_objective_for_district, district): district for district in possible_districts}
    for future in as_completed(future_to_district):
        district = future_to_district[future]
        compactness_value, white_pop_percent_value = future.result()
        objective_compactness.append(compactness_value * x[district])
        objective_white_pop.append(abs(white_pop_percent_value - statewide_white_percentage) * x[district])


# Add the objective to the model
redistrict_model += (
    sum(objective_compactness) +
    pulp.lpSum(objective_white_pop)
), "Objective"

# Constraints
# Maximum number of districts
redistrict_model += sum([x[district] for district in possible_districts]) == max_district, "Maximum_number_of_districts"

# Adjacency constraint for each pair of counties in a district
for district in possible_districts:
    for county1 in district:
        for county2 in district:
            if county1 != county2:
                if adjacency_matrix.at[county1, county2] == 0:
                    redistrict_model += x[district] == 0

# Each county must be in exactly one district
for county in counties:
    redistrict_model += sum([x[district] for district in possible_districts if county in district]) == 1, f"Must_zone_{county}"

# Solve the model
redistrict_model.solve()

# Output the results
if redistrict_model.status == pulp.LpStatusOptimal:
    print("Optimal solution found!")
    final_output="Optimal solution found!"
else:
    print("No optimal solution found. Status:", pulp.LpStatus[redistrict_model.status])
    final_output="No optimal solution found."


input("Press Enter to Exit. {}".format(final_output))