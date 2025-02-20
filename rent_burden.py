import os
import pandas as pd
from Wrapper.census import CensusAPIWrapper

if __name__ == "__main__":
    api_key = os.getenv("CENSUS_API_KEY")
    census_api = CensusAPIWrapper(api_key)

    # Define variables to fetch from ACS 5-Year Estimates with mapping
    variables = {
        "B25004_001E": "total_vacant_housing_units",       # Total vacant housing units
        "B25003_002E": "owner_occupied_housing_units",     # Owner-occupied units
        "B25003_003E": "renter_occupied_housing_units",    # Renter-occupied units
        "B19013_001E": "median_household_income",          # Median household income (past 12 months)
        "B25064_001E": "median_gross_rent",                # Median gross rent
        "B25070_001E": "total_renter_households_cost",     # Total renter households (for cost burden calc)
        "B25070_007E": "rent_30_to_34_9_percent",          # Rent 30.0-34.9% of income
        "B25070_008E": "rent_35_to_39_9_percent",          # Rent 35.0-39.9% of income
        "B25070_009E": "rent_40_to_49_9_percent",          # Rent 40.0-49.9% of income
        "B25070_010E": "rent_50_percent_or_more",          # Rent 50.0% or more of income
        "B25071_001E": "median_gross_rent_percent_income"  # Median gross rent as % of household income
    }

    # Convert variable dictionary keys to a list for the API call
    variable_list = list(variables.keys())

    # Fetch county data (all counties in the U.S.)
    county_data = census_api.get_county_data(variable_list)

    # Assuming county_data is a list of dictionaries, convert to DataFrame
    df = pd.DataFrame(county_data)

    # Create a reverse mapping for renaming columns (variable code to descriptive name)
    column_mapping = variables.copy()  # Use the existing dictionary for mapping

    # Add geographic columns that might be returned by the API (e.g., state, county FIPS)
    # Adjust these based on the actual output of get_county_data()
    geo_columns = {"state": "state_fips", "county": "county_fips"}
    column_mapping.update(geo_columns)

    # Rename DataFrame columns using the mapping
    df.rename(columns=column_mapping, inplace=True)

    # Ensure numeric columns are properly typed (convert from string if needed)
    numeric_columns = list(variables.values())  # All variables except geographic ones
    df[numeric_columns] = df[numeric_columns].apply(pd.to_numeric, errors="coerce")

    # Display sample of the DataFrame
    print("Sample of DataFrame with mapped column names:")
    print(df.head())

