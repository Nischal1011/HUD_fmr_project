import gradio as gr
import geopandas as gpd
import pandas as pd
import functools
import plotly.graph_objects as go

# [Keeping your existing data loading unchanged]
@functools.lru_cache(maxsize=None)
def load_data():
    """Load and validate geographic data"""
    df = pd.read_csv("data/census_fmr_county.csv", dtype={'GEOID': str})
    df = df[df['geometry'].notna() & (df['geometry'] != '0')]
    df['geometry'] = gpd.GeoSeries.from_wkt(df['geometry'])
    gdf = gpd.GeoDataFrame(df, crs="EPSG:4269")
    gdf = gdf.to_crs(epsg=4326)
    
    fmr_cols = [f'fmr_{i}' for i in range(5)]
    gdf = gdf[~(gdf[fmr_cols] == 0).all(axis=1)]
    
    numeric_cols = (
        fmr_cols +
        [f'rent_to_income_ratio_{i}' for i in range(5)] +
        [f'fmr_vs_median_rent_diff_{i}' for i in range(5)] +
        [f'fmr_vs_median_rent_percent_{i}' for i in range(5)] +
        [f'affordability_gap_{i}' for i in range(5)] +
        [f'voucher_feasibility_{i}' for i in range(5)] +
        ['pct_cost_burdened', 'pct_severe_cost_burdened'] +
        [f'housing_wage_{i}' for i in range(5)]
    )
    gdf[numeric_cols] = gdf[numeric_cols].apply(pd.to_numeric, errors='coerce')
    
    return gdf, gdf.__geo_interface__

METRIC_INFO = {
    'FMR': {'format': '${:.2f}', 'description': 'Fair Market Rent set by HUD', 'prefix': '$'},
    'Rent-to-Income Ratio': {'format': '{:.1f}%', 'description': 'Annual FMR as % of median income', 'prefix': ''},
    'FMR vs Median Rent Difference': {'format': '${:.2f}', 'description': 'Dollar difference between FMR and median rent', 'prefix': '$'},
    'FMR Deviation (%)': {'format': '{:.1f}%', 'description': 'Percentage difference FMR vs median rent', 'prefix': ''},
    'Affordability Gap': {'format': '${:.2f}', 'description': 'Excess rent over 30% income', 'prefix': '$'},
    'Voucher Feasibility': {'format': '{:.1f}%', 'description': 'FMR as % of median rent', 'prefix': ''},
    'Cost Burden': {'format': '{:.1f}%', 'description': 'Renters spending >30% on rent', 'prefix': ''},
    'Severe Cost Burden': {'format': '{:.1f}%', 'description': 'Renters spending >50% on rent', 'prefix': ''},
    'Housing Wage': {'format': '${:.2f}/hr', 'description': 'Hourly wage needed for FMR', 'prefix': '$'}
}

PERCENTAGE_METRICS = {
    'Rent-to-Income Ratio', 'FMR Deviation (%)', 'Voucher Feasibility', 
    'Cost Burden', 'Severe Cost Burden'
}

def create_map(bedroom_type, metric_type):
    """Generate interactive choropleth map"""
    gdf, geojson = load_data()
    bedroom_num = int(bedroom_type[0])
    
    metric_mapping = {
        'FMR': f'fmr_{bedroom_num}',
        'Rent-to-Income Ratio': f'rent_to_income_ratio_{bedroom_num}',
        'FMR vs Median Rent Difference': f'fmr_vs_median_rent_diff_{bedroom_num}',
        'FMR Deviation (%)': f'fmr_vs_median_rent_percent_{bedroom_num}',
        'Affordability Gap': f'affordability_gap_{bedroom_num}',
        'Voucher Feasibility': f'voucher_feasibility_{bedroom_num}',
        'Cost Burden': 'pct_cost_burdened',
        'Severe Cost Burden': 'pct_severe_cost_burdened',
        'Housing Wage': f'housing_wage_{bedroom_num}'
    }
    
    metric_col = metric_mapping[metric_type]
    format_str = METRIC_INFO[metric_type]['format']
    
    gdf['hover_text'] = gdf.apply(
        lambda x: f"<b>{x['county_name']}</b><br>"
                 f"State: {x['state_name']}<br>"
                 f"{metric_type}: {format_str.format(x[metric_col])}" if pd.notna(x[metric_col]) else "",
        axis=1
    )

    z = gdf[metric_col] * (100 if metric_type in PERCENTAGE_METRICS else 1)
    tickformat = '.1f' if metric_type in PERCENTAGE_METRICS else ',.0f'
    ticksuffix = '%' if metric_type in PERCENTAGE_METRICS else ''
    tickprefix = '$' if metric_type not in PERCENTAGE_METRICS else ''

    fig = go.Figure(go.Choropleth(
        geojson=geojson,
        locations=gdf['GEOID'],
        z=z,
        featureidkey="properties.GEOID",
        colorscale='Viridis',
        marker_line_width=0.5,
        marker_line_color='white',
        hoverinfo="text",
        hovertext=gdf['hover_text'],
        colorbar=dict(
            title=metric_type,
            thickness=15,
            tickfont=dict(size=12),
            tickprefix=tickprefix,
            ticksuffix=ticksuffix,
            tickformat=tickformat
        )
    ))

    fig.update_layout(
        height=600,
        margin=dict(r=0, t=40, l=0, b=0),
        geo=dict(
            scope='usa',
            projection=dict(type='albers usa'),
            showlakes=True,
            lakecolor='rgba(224, 242, 254, 0.8)',
            landcolor='#f5f5f5'
        ),
        font=dict(family="Arial", color="#333333"),
        paper_bgcolor='#ffffff'
    )
    return fig

def get_stats(bedroom_type, metric_type):
    """Calculate statistics with county info for min/max"""
    gdf, _ = load_data()
    bedroom_num = int(bedroom_type[0])
    
    metric_mapping = {
        'FMR': f'fmr_{bedroom_num}',
        'Rent-to-Income Ratio': f'rent_to_income_ratio_{bedroom_num}',
        'FMR vs Median Rent Difference': f'fmr_vs_median_rent_diff_{bedroom_num}',
        'FMR Deviation (%)': f'fmr_vs_median_rent_percent_{bedroom_num}',
        'Affordability Gap': f'affordability_gap_{bedroom_num}',
        'Voucher Feasibility': f'voucher_feasibility_{bedroom_num}',
        'Cost Burden': 'pct_cost_burdened',
        'Severe Cost Burden': 'pct_severe_cost_burdened',
        'Housing Wage': f'housing_wage_{bedroom_num}'
    }
    
    metric_col = metric_mapping[metric_type]
    gdf = gdf.dropna(subset=[metric_col])
    format_str = METRIC_INFO[metric_type]['format']
    
    min_row = gdf.loc[gdf[metric_col].idxmin()]
    max_row = gdf.loc[gdf[metric_col].idxmax()]
    
    return [
        format_str.format(gdf[metric_col].mean()),
        format_str.format(gdf[metric_col].median()),
        f"{format_str.format(gdf[metric_col].min())} ({min_row['county_name']}, {min_row['state_name']})",
        f"{format_str.format(gdf[metric_col].max())} ({max_row['county_name']}, {max_row['state_name']})",
        len(gdf),
        format_str.format(gdf[metric_col].std()),
        format_str.format(gdf[metric_col].quantile(0.25)),
        format_str.format(gdf[metric_col].quantile(0.75))
    ]

# Metric definition table
ALL_METRICS_DISPLAY = """
### Metric Definitions
| Metric | Description |
|--------|-------------|
""" + "\n".join(
    f"| **{metric}** | {METRIC_INFO[metric]['description']} |"
    for metric in METRIC_INFO
)

# Define a clean, professional theme
theme = gr.themes.Default(
    primary_hue="blue",
    secondary_hue="gray",
    neutral_hue="gray",
    font=("Arial", "sans-serif"),
    font_mono=("Arial", "sans-serif"),
).set(
    body_background_fill="#f5f5f5",
    block_background_fill="#ffffff",
    block_border_width="1px",
    block_border_color="#e0e0e0",
    input_background_fill="#ffffff",
    button_primary_background_fill="#2563eb",
    button_primary_text_color="#ffffff"
)

# Minimal CSS for fine-tuning
css = """
.container { 
    max-width: 1400px; 
    margin: 0 auto; 
    padding: 1rem; 
}
.stats-panel { 
    padding: 1rem; 
    border-radius: 8px; 
}
.map-container { 
    padding: 1rem; 
    border-radius: 8px; 
}
.metric-info { 
    font-size: 0.9rem; 
    color: #666666; 
    margin-top: 0.5rem;
}
.all-metrics { 
    font-size: 0.9rem; 
    margin-top: 1rem; 
}
.all-metrics table { 
    width: 100%; 
    border-collapse: collapse; 
}
.all-metrics th, .all-metrics td { 
    padding: 0.5rem; 
    text-align: left; 
    border-bottom: 1px solid #e0e0e0; 
}
"""

with gr.Blocks(theme=theme, css=css, title="U.S. Housing Market Analysis") as app:
    gr.Markdown(
        """
        # U.S. Housing Market Analysis
        Explore Fair Market Rent and housing affordability metrics across U.S. counties
        """,
        elem_classes="container"
    )
    
    with gr.Row():
        with gr.Column(scale=1):
            with gr.Group(elem_classes="stats-panel"):
                bedroom_select = gr.Dropdown(
                    choices=["0-Bedroom", "1-Bedroom", "2-Bedroom", "3-Bedroom", "4-Bedroom"],
                    value="2-Bedroom",
                    label="Bedroom Size"
                )
                metric_select = gr.Dropdown(
                    choices=list(METRIC_INFO.keys()),
                    value="FMR",
                    label="Metric"
                )
                metric_description = gr.Markdown(
                    elem_classes="metric-info"
                )
                stats_output = gr.Dataframe(
                    headers=["Statistic", "Value"],
                    label="Summary Statistics",
                    interactive=False,
                    wrap=True
                )
                gr.Markdown(
                    ALL_METRICS_DISPLAY,
                    elem_classes="all-metrics"
                )
        
        with gr.Column(scale=2):
            with gr.Group(elem_classes="map-container"):
                map_output = gr.Plot(label="Geographic Distribution")

    def update_display(bedroom_type, metric_type):
        stats = get_stats(bedroom_type, metric_type)
        stats_data = [
            ["Mean", stats[0]],
            ["Median", stats[1]],
            ["Minimum", stats[2]],
            ["Maximum", stats[3]],
            ["Counties", stats[4]],
            ["Std Dev", stats[5]],
            ["Q1 (25th)", stats[6]],
            ["Q3 (75th)", stats[7]]
        ]
        description = f"**{metric_type}**: {METRIC_INFO[metric_type]['description']}"
        return (
            create_map(bedroom_type, metric_type),
            stats_data,
            description
        )

    # Event handlers
    for input_elem in [bedroom_select, metric_select]:
        input_elem.change(
            update_display,
            inputs=[bedroom_select, metric_select],
            outputs=[map_output, stats_output, metric_description]
        )

    app.load(
        fn=lambda: update_display("2-Bedroom", "FMR"),
        outputs=[map_output, stats_output, metric_description]
    )

if __name__ == "__main__":
    app.launch()