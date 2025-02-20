import requests
import pandas as pd
import os
class CensusAPIWrapper:
    BASE_URL = "https://api.census.gov/data/2023/acs/acs5"

    def __init__(self, api_key):
        self.api_key = api_key

    def get_state_data(self, variables):
        """Fetch data at state level"""
        params = {
            "get": ",".join(variables + ["NAME"]),
            "for": "state:*",
            "key": self.api_key
        }
        return self._make_request(params)

    def get_zip_data(self, variables):
        """Fetch data at ZIP code level (ZCTA)"""
        params = {
            "get": ",".join(variables + ["NAME"]),
            "for": "zip code tabulation area:*",
            "key": self.api_key
        }
        return self._make_request(params)

    def get_county_data(self, variables, state_fips=None):
        """Fetch data at county level, optionally for a specific state"""
        params = {
            "get": ",".join(variables + ["NAME"]),
            "for": "county:*",
            "key": self.api_key
        }
        if state_fips:
            params["in"] = f"state:{state_fips}"
        return self._make_request(params)

    def _make_request(self, params):
        """Shared request handling logic"""
        response = requests.get(self.BASE_URL, params=params)
        
        if response.status_code != 200:
            raise Exception(f"API Request Failed: {response.status_code} - {response.text}")

        data = response.json()
        df = pd.DataFrame(data[1:], columns=data[0])
        
        # Clean column names
        df = df.rename(columns={
            "zip code tabulation area": "zip_code",
            "state": "state_fips",
            "county": "county_fips"  # Add county FIPS renaming
        })
        
        return df

if __name__ == "__main__":
    api_key = os.getenv("CENSUS_API_KEY")
    census_api = CensusAPIWrapper(api_key)

    # Define variables to fetch
    variables = {
        "B25004_001E": "total_vacant_housing_units",
        "B25003_002E": "owner_occupied_housing_units",
        "B25003_003E": "renter_occupied_housing_units",
        "B25064_001E": "median_gross_rent",
        "B19013_001E": "median_household_income"
    }
    variable_list = list(variables.keys())

    # Fetch state data
    state_data = census_api.get_state_data(variable_list)
    print("State Data:")
    print(state_data.head())

    # Fetch county data (all counties in the U.S.)
    county_data = census_api.get_county_data(variable_list)
    print("\nCounty Data (All Counties):")
    print(county_data.head())

