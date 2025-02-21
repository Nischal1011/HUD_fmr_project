# Fair Market Rent Map Visualization

A Python-based visualization tool for analyzing Fair Market Rent (FMR) data across U.S. counties. This project combines census data with FMR statistics to create interactive geographic visualizations.

## Features

- Interactive county-level map visualizations
- Fair Market Rent analysis for different bedroom types (0-4 bedrooms)
- Multiple metric visualizations including:
  - Rent-to-income ratios
  - FMR vs median rent differences
  - Affordability gaps
  - Voucher feasibility
  - Housing wage analysis
- Comprehensive statistics including mean, median, min/max, and distribution metrics
- County-specific data lookup

## Technical Requirements

- Python 3.x
- Required packages:
  - pandas
  - geopandas
  - requests
  - (Additional dependencies should be listed in requirements.txt)

## Data Sources

- U.S. Census Bureau ACS 5-year estimates (2023)
- County-level Fair Market Rent data (stored in `data/census_fmr_county.csv`)

## Setup

1. Obtain a Census API key from [api.census.gov](https://api.census.gov)
2. Install required dependencies
3. Ensure the geographic data file is present in the `data` directory

## Usage

The application provides several key functions:

```python
# Load and analyze FMR data
gdf, geo_interface = load_data()

# Get statistics for specific bedroom types
stats = get_stats("2 Bedroom")  # Returns comprehensive statistics

# Create visualizations
map_data = create_map(bedroom_type, metric_type)
```

## Data Structure

The system works with multiple metrics for each county:
- Fair Market Rent (FMR) for 0-4 bedrooms
- Rent-to-income ratios
- FMR vs median rent differences
- Affordability gaps
- Cost burden percentages
- Housing wage calculations

## API Integration

The project includes a Census API wrapper that supports:
- County-level data retrieval
- State-specific filtering
- ZIP code data access
- Automated error handling and response processing
