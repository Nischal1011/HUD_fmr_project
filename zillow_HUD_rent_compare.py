import pandas as pd 

import geopandas as gpd
import pandas as pd
import gradio as gr
import matplotlib.pyplot as plt
import seaborn as sns
if __name__ == "__main__":
    zillow_df = pd.read_csv("data/County_zori_uc_sfrcondomfr_sm_month.csv")
    # Calculate 3-month moving average for the last 3 months
    last_3_months = ['2024-10-31', '2024-11-30', '2024-12-31']
    zillow_df['last_3_month_ma'] = zillow_df[last_3_months].mean(axis=1)
    zillow_df_v1 = zillow_df[['StateName', 'Metro', 'RegionName', 'last_3_month_ma']]

    zillow_df_v1



    hud_fmr_df = pd.read_csv("data/FY25_FMRs.csv")
    hud_fmr_df_v1 = hud_fmr_df[['state', 'countyname', 'fmr_0', 'fmr_1', 'fmr_2', 'fmr_3', 'fmr_4']]

    hud_fmr_df_v1.rename(columns = {'countyname':'county_name'}, inplace = True)
    county_geo_id_df = pd.read_csv("data/county_geoid.csv")
    county_geo_id_df.rename(columns = {'STATEFP':'state'}, inplace = True)
    county_geo_id_df['state'] = county_geo_id_df['state'].astype('str')
    county_geo_id_df['state'] = county_geo_id_df['state'].str.zfill(2)
    county_geo_id_df['GEOID'] = county_geo_id_df['GEOID'].astype('str')
    hud_fmr_df_v1['state'] = hud_fmr_df_v1['state'].astype('str')
    hud_fmr_df_v1['state'] = hud_fmr_df_v1['state'].str.zfill(2)
    county_geo_id_df['GEOID'] = county_geo_id_df['GEOID'].str.zfill(5)
    hud_fmr_df_v1['county_name'] = hud_fmr_df_v1['county_name'].str.upper()
    
    from fuzzywuzzy import process

    # Subset Alaska counties from both DataFrames
    alaska_fmr = hud_fmr_df_v1[hud_fmr_df_v1['state'] == '02']
    alaska_geo = county_geo_id_df[county_geo_id_df['state'] == '02']

    # Create a mapping of original to best-matched county names
    matched_counties = {}
    for county in alaska_geo['county_name']:
        # Get the best match and score
        best_match, score = process.extractOne(county, alaska_fmr['county_name'].tolist())
        # Optionally apply a score threshold (e.g., 80)
        if score >= 80:
            matched_counties[county] = best_match
        else:
            # Keep original name if score is too low
            matched_counties[county] = county  # or handle manually

    # Update county names in the geo DataFrame
    county_geo_id_df.loc[county_geo_id_df['state'] == '02', 'county_name'] = (
        county_geo_id_df['county_name'].map(matched_counties))


    hud_fmr_df_v2 = county_geo_id_df.merge(hud_fmr_df_v1, on = ['state', 'county_name'], how = 'inner')
    # Load shapefiles using Geopandas
    county_shapefile = gpd.read_file("data/cb_2018_us_county_20m/cb_2018_us_county_20m.shp")
    county_shapefile_v1 = county_shapefile[['GEOID', 'geometry']]


    hud_fmr_df_v3 = hud_fmr_df_v2.merge(county_shapefile_v1, on = 'GEOID')
    state_fips_map = {
    "01": "Alabama", "02": "Alaska", "04": "Arizona", "05": "Arkansas", "06": "California",
    "08": "Colorado", "09": "Connecticut", "10": "Delaware", "11": "District of Columbia",
    "12": "Florida", "13": "Georgia", "15": "Hawaii", "16": "Idaho", "17": "Illinois",
    "18": "Indiana", "19": "Iowa", "20": "Kansas", "21": "Kentucky", "22": "Louisiana",
    "23": "Maine", "24": "Maryland", "25": "Massachusetts", "26": "Michigan", "27": "Minnesota",
    "28": "Mississippi", "29": "Missouri", "30": "Montana", "31": "Nebraska", "32": "Nevada",
    "33": "New Hampshire", "34": "New Jersey", "35": "New Mexico", "36": "New York",
    "37": "North Carolina", "38": "North Dakota", "39": "Ohio", "40": "Oklahoma", "41": "Oregon",
    "42": "Pennsylvania", "44": "Rhode Island", "45": "South Carolina", "46": "South Dakota",
    "47": "Tennessee", "48": "Texas", "49": "Utah", "50": "Vermont", "51": "Virginia",
    "53": "Washington", "54": "West Virginia", "55": "Wisconsin", "56": "Wyoming"
}
    hud_fmr_df_v3['state_name'] = hud_fmr_df_v3['state'].astype(str).str.zfill(2).map(state_fips_map)

    hud_fmr_df_v3.to_csv("data/county_fmr.csv", index = False)
    

    print("Data saved to data/county_fmr.csv")
   