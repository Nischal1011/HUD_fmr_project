import os
import numpy as np
import pandas as pd

# Step 1: Fetch and Process Census ACS Data
def get_census_data(census_file_path="data/census_county_data.csv"):
    """
    Loads and returns Census ACS data from a CSV file.
    """
    df_census = pd.read_csv(census_file_path)
    
    # Ensure GEOID is string and zero-padded
    df_census["GEOID"] = df_census["GEOID"].astype(str).str.zfill(5)

    # df_census['median_gross_rent'] = np.where(df_census['median_gross_rent']>0, np.nan, df_census   ['median_gross_rent'] )
    df_census['median_gross_rent'] = np.where(df_census['median_gross_rent']<0, np.nan, df_census['median_gross_rent'] )
    df_census['median_household_income'] = np.where(df_census['median_household_income']<0, np.nan, df_census['median_household_income'] )
    return df_census

# Step 2: Load FMR Data
def load_fmr_data(fmr_file_path="data/county_fmr.csv"):
    """
    Loads and returns FMR data from a CSV file.
    """
    df_fmr = pd.read_csv(fmr_file_path)
    
    # Ensure GEOID is string and zero-padded
    df_fmr["GEOID"] = df_fmr["GEOID"].astype(str).str.zfill(5)
    
    return df_fmr[["GEOID", "county_name", "state_name", 
                   "fmr_0", "fmr_1", "fmr_2", "fmr_3", "fmr_4", 'geometry']]

# Step 3: Integrate Data with Enhanced Metrics
def integrate_data(df_census, df_fmr):
    """
    Merges Census and FMR data and calculates affordability metrics.
    """
    # Merge Census and FMR data on GEOID
    df_integrated = pd.merge(df_census, df_fmr, on="GEOID", how="left")

    # Handling missing values
    df_integrated.fillna(0, inplace=True)

    # Rent-to-Income Ratios for all bedroom sizes
    for beds in range(5):
        df_integrated[f"rent_to_income_ratio_{beds}"] = (
            (df_integrated[f"fmr_{beds}"] * 12) / df_integrated["median_household_income"]
        ) * 100
        df_integrated['median_gross_rent'] = np.where(df_integrated[f'fmr_{beds}']==0, np.nan, df_integrated['median_gross_rent'] )
    # Percentage of Cost-Burdened Renters (>30% of income)
    cost_burdened_cols = ["rent_30_to_34_9_percent", "rent_35_to_39_9_percent", 
                          "rent_40_to_49_9_percent", "rent_50_percent_or_more"]
    df_integrated["pct_cost_burdened"] = (
        df_integrated[cost_burdened_cols].sum(axis=1) / df_integrated["total_renter_households_cost"]
    ) * 100

    # Severe Cost Burden (>50% of income)
    df_integrated["pct_severe_cost_burdened"] = (
        df_integrated["rent_50_percent_or_more"] / df_integrated["total_renter_households_cost"]
    ) * 100

    # FMR vs Median Gross Rent Differences for all bedroom sizes
    for beds in range(5):
        df_integrated[f"fmr_vs_median_rent_diff_{beds}"] = (
            df_integrated[f"fmr_{beds}"] - df_integrated["median_gross_rent"]
        )
        df_integrated[f"fmr_vs_median_rent_percent_{beds}"] = np.where(
     (df_integrated["median_gross_rent"] != 0) & (df_integrated["fmr_1"] != 0),
     ((df_integrated[f"fmr_{beds}"] - df_integrated["median_gross_rent"]) / df_integrated["median_gross_rent"]) * 100,
     np.nan  # Ensures that fmr_1 = 0 does not produce -100
 )

    

    # Affordability Gap: Excess rent over 30% threshold for all bedrooms
    for beds in range(5):
        df_integrated[f"affordability_gap_{beds}"] = (
            (df_integrated[f"fmr_{beds}"] * 12) - (df_integrated["median_household_income"] * 0.3)
        ).apply(lambda x: max(x, 0))  # Only positive gaps
        df_integrated[f'affordability_gap_{beds}'] = np.where(df_integrated[f'affordability_gap_{beds}']==0,np.nan, df_integrated[f'affordability_gap_{beds}'])
    min_wage_df = pd.read_csv("data/minimum_wage_by_state.csv")
    df_integrated = min_wage_df[['min_wage', 'state_fips']].merge(df_integrated, on = 'state_fips', how = 'right')
    # Voucher Feasibility: % of FMR above median rent for all bedrooms
    for beds in range(5):
        df_integrated[f"voucher_feasibility_{beds}"] = (
            df_integrated[f"fmr_{beds}"] / df_integrated["median_gross_rent"]
        ).replace([float('inf'), -float('inf')], 0) * 100

        
        df_integrated[f"housing_wage_{beds}"] = (df_integrated[f"fmr_{beds}"] * 12) / 2080  # Assuming 40 hours/week, 52 weeks
        df_integrated[f"housing_wage_to_min_wage_{beds}"] = df_integrated[f"housing_wage_{beds}"] / df_integrated["min_wage"] * 100

    return df_integrated

# Main Execution
if __name__ == "__main__":
    # Fetch Census data
    df_census = get_census_data()

    # Load FMR data
    df_fmr = load_fmr_data("data/county_fmr.csv")

    # Integrate datasets
    df_integrated = integrate_data(df_census, df_fmr)

    # Display sample with new metrics
    print("Integrated Data Sample:")
    sample_cols = ["GEOID", "county_name", "state_name", "median_household_income", 
                   "fmr_2", "rent_to_income_ratio_2", "pct_cost_burdened", 
                   "pct_severe_cost_burdened", "fmr_vs_median_rent_diff_2", 
                   "affordability_gap_2", "voucher_feasibility_2", "housing_wage_2"]
    print(df_integrated[sample_cols].head())

    # Save to CSV
    df_integrated.to_csv("data/census_fmr_county.csv", index=False)
    print("Integrated data saved to 'data/census_fmr_county.csv'")