import requests
import pandas as pd
import re

# Fetch FIPS data
url = "https://transition.fcc.gov/oet/info/maps/census/fips/fips.txt"
response = requests.get(url)
text = response.text  # Directly use the text content

# Process text lines
counties_data = []
current_state_fips = None




for line in text.split("\n"):
    line = line.strip()
    if not line:
        continue
    
    # Match state lines (e.g., "01        ALABAMA")
    state_match = re.match(r"^\s*(\d{2})\s+([A-Z\s]+)$", line)
    if state_match:
        current_state_fips = state_match.group(1)
        continue
    
    # Match county lines (e.g., "01001        Autauga County")
    county_match = re.match(r"^\s*(\d{5})\s+(.+)$", line)
    if county_match and current_state_fips:
        fips_code = county_match.group(1)
        county_name = county_match.group(2).strip()
        
        # Skip state-level entries (e.g., "01000        Alabama")
        if fips_code.endswith("000"):
            continue
        
        # Clean county name (remove "County", "Parish", etc.)
        cleaned_name = re.sub(
            r"\s+County$|\s+Parish$|\s+Borough$|\s+Census Area$|\s+Municipio$",
            "", 
            county_name, 
            flags=re.IGNORECASE
        ).strip()
        
        counties_data.append({
            "STATEFP": current_state_fips,
            "GEOID": fips_code,
            "county_name": cleaned_name.upper()  # Standardize to uppercase
        })

# Create DataFrame
fips_df = pd.DataFrame(counties_data)
fips_df['county_name'] = fips_df['county_name'] + ' COUNTY'
fips_df['STATEFP'] = fips_df['GEOID'].astype(str).str[:2]

fips_df.to_csv("data/county_geoid.csv", index=False)