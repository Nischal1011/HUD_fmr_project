# Fair Market Rent Analysis Dashboard

An interactive dashboard to visualize and analyze HUD Fair Market Rent (FMR) data across U.S. counties. This project combines data from HUD, Zillow, and geographic sources to provide insights into rental markets.

## Features

- Interactive choropleth map showing FMR distribution across U.S. counties
- Filtering by unit size (0-4 bedrooms)
- Key market statistics including:
  - Average rent
  - Median rent
  - Minimum/Maximum rents with county names
  - Standard deviation
  - Quartile values
- County-level detail on hover
- Responsive design

## Data Sources

- HUD Fair Market Rent data (FY 2025)
- Zillow rental price data
- U.S. Census Bureau geographic data (TIGER/Line shapefiles)

## Installation

1. Clone the repository:
```bash
git clone https://github.com/yourusername/fair-market-rent-analysis.git
```

2. Install required packages:
```bash
pip install -r requirements.txt
```

## Project Structure

- `fmr_map_viz.py` - Main dashboard application using Gradio
- `county_geo_id.py` - Geographic data processing utilities
- `zillow_HUD_rent_compare.py` - Data preparation and comparison logic
- `data/` - Directory containing source data files

## Usage

1. Run the dashboard:
```bash
python fmr_map_viz.py
```

2. Access the dashboard in your browser at `http://localhost:2000`

## Data Processing

The project processes data in several steps:

1. Loads and cleans HUD FMR data
2. Processes Zillow rental data for comparison
3. Matches geographic identifiers
4. Generates county-level visualizations

## Dependencies

- Gradio
- GeoPandas
- Pandas
- Plotly
- FuzzyWuzzy
- NumPy

## Contributing

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request

## License

MIT

## Acknowledgments

- U.S. Department of Housing and Urban Development
- Zillow Research
- U.S. Census Bureau