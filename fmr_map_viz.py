import gradio as gr
import geopandas as gpd
import pandas as pd
import functools
import plotly.graph_objects as go

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
    'FMR': {
        'format': '${:.2f}',
        'description': 'Fair Market Rent set by HUD (Neutral - context dependent)',
        'prefix': '$'
    },
    'Rent-to-Income Ratio': {
        'format': '{:.1f}%',
        'description': 'Annual FMR as % of median income (Lower is better - less burden)',
        'prefix': ''
    },
    'FMR vs Median Rent Difference': {
        'format': '${:.2f}',
        'description': 'Dollar difference between FMR and median rent (Higher is better - FMR exceeds market rent)',
        'prefix': '$'
    },
    'FMR Deviation (%)': {
        'format': '{:.1f}%',
        'description': 'Percentage difference FMR vs median rent (Higher is better - FMR exceeds market rent)',
        'prefix': ''
    },
    'Affordability Gap': {
        'format': '${:.2f}',
        'description': 'Excess rent over 30% income (Lower is better - less unaffordable)',
        'prefix': '$'
    },
    'Voucher Feasibility': {
        'format': '{:.1f}%',
        'description': 'FMR as % of median rent (Higher is better - better coverage)',
        'prefix': ''
    },
    'Cost Burden': {
        'format': '{:.1f}%',
        'description': 'Renters spending >30% on rent (Lower is better - fewer burdened households)',
        'prefix': ''
    },
    'Severe Cost Burden': {
        'format': '{:.1f}%',
        'description': 'Renters spending >50% on rent (Lower is better - fewer severely burdened households)',
        'prefix': ''
    },
    'Housing Wage': {
        'format': '${:.2f}/hr',
        'description': 'Hourly wage needed for FMR (Lower is better - more affordable)',
        'prefix': '$'
    }
}

METRIC_DIRECTION = {
    'FMR': 'neutral',
    'Rent-to-Income Ratio': 'lower',
    'Affordability Gap': 'lower',
    'Cost Burden': 'lower',
    'Severe Cost Burden': 'lower',
    'Housing Wage': 'lower',
    'FMR vs Median Rent Difference': 'higher',
    'FMR Deviation (%)': 'higher',
    'Voucher Feasibility': 'higher'
}

PERCENTAGE_METRICS = {
    'Rent-to-Income Ratio',
    'FMR Deviation (%)',
    'Voucher Feasibility',
    'Cost Burden',
    'Severe Cost Burden'
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
    prefix = METRIC_INFO[metric_type]['prefix']
    
    gdf['hover_text'] = gdf.apply(
        lambda x: f"<b>{x['county_name']}</b><br>"
                 f"State: {x['state_name']}<br>"
                 f"{metric_type}: {format_str.format(x[metric_col])}" if pd.notna(x[metric_col]) else "",
        axis=1
    )

    if metric_type in PERCENTAGE_METRICS:
        z = gdf[metric_col] * 100
        tickprefix = ''
        ticksuffix = '%'
        tickformat = '.1f'
    else:
        z = gdf[metric_col]
        tickprefix = '$'
        ticksuffix = ''
        tickformat = ',.0f'

    # Use 'Viridis' for a lighter, more legible heatmap (uniform and clear color transition)
    colorscale = 'Viridis'

    # Conditionally set the colorbar title: show only metric_type for FMR, include description for others
    colorbar_title_text = f"{metric_type}"
    if metric_type != 'FMR':
        colorbar_title_text += f"<br><br>{METRIC_INFO[metric_type]['description']}"

    fig = go.Figure(go.Choropleth(
        geojson=geojson,
        locations=gdf['GEOID'],
        z=z,
        featureidkey="properties.GEOID",
        colorscale=colorscale,
        marker_line_width=0.5,
        marker_line_color='white',
        hoverinfo="text",
        hovertext=gdf['hover_text'],
        colorbar=dict(
            title=dict(
                text=colorbar_title_text,  # Use the conditionally built title
                font=dict(size=14),
                side='right'
            ),
            thickness=15,
            len=0.75,
            tickfont=dict(size=12),
            tickprefix=tickprefix,
            ticksuffix=ticksuffix,
            tickformat=tickformat
        )
    ))

    fig.update_layout(
        height=600,
        margin=dict(r=0, t=30, l=0, b=0),
        geo=dict(
            scope='usa',
            projection=dict(type='albers usa'),
            showlakes=True,
            lakecolor='#e0f2fe',  # Lighter lake color for better contrast
            landcolor='#f0f4f8',  # Lighter land color for better legibility
            bgcolor='rgba(240, 244, 248, 0.9)'  # Lighter background for the map
        ),
        font=dict(
            family="Inter",
            color="#333333"  # Darker text for contrast on lighter background
        ),
        paper_bgcolor='rgba(240, 244, 248, 0.9)',  # Lighter background for the entire plot
        plot_bgcolor='rgba(240, 244, 248, 0.9)'  # Lighter plot background
    )

    return fig

def get_stats(bedroom_type, metric_type):
    """Calculate statistics for selected metric"""
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
    
    return [
        format_str.format(val) if isinstance(val, float) else val
        for val in [
            gdf[metric_col].mean(),
            gdf[metric_col].median(),
            gdf[metric_col].min(),
            gdf[metric_col].max(),
            len(gdf),
            gdf[metric_col].std(),
            gdf[metric_col].quantile(0.25),
            gdf[metric_col].quantile(0.75)
        ]
    ]

# Static table includes all metrics with their descriptions
ALL_METRICS_DISPLAY = """
### All Metrics

| Metric                      | Description                                                      |
|-----------------------------|------------------------------------------------------------------|
""" + "\n".join(
    f"| **{metric}** | {METRIC_INFO[metric]['description']} |"
    for metric in METRIC_INFO
)

theme = gr.themes.Soft(
    primary_hue="blue",
    secondary_hue="slate",
    neutral_hue="slate",
    font=("Inter", "sans-serif")
)

css = """
.gradio-container {
    background-color: #1a1a1a !important;
}
.container {
    margin: 0 auto;
    padding: 1rem;
    max-width: 1400px;
    background-color: #1a1a1a;
    color: white;
}
.stats-panel, .map-container {
    background-color: #2a2a2a !important;
    padding: 1.5rem;
    border-radius: 0.5rem;
    margin: 0.5rem;
    box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
}
.metric-info, .all-metrics {
    margin-top: 1rem;
    padding: 1rem;
    background-color: #333333;
    border-radius: 0.5rem;
    color: white;
    box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
}
.all-metrics table {
    width: 100%;
    border-collapse: collapse;
}
.all-metrics th, .all-metrics td {
    padding: 0.75rem;
    text-align: left;
    border-bottom: 1px solid #444444;
}
.all-metrics th {
    background-color: #3a3a3a;
    font-weight: bold;
    color: #e0e0e0;
}
.all-metrics td {
    color: #d0d0d0;
}
.dataframe {
    background-color: #2a2a2a !important;
    color: white !important;
}
.dataframe th, .dataframe td {
    background-color: #2a2a2a !important;
    color: white !important;
    border: 1px solid #444444 !important;
}
"""

with gr.Blocks(theme=theme, css=css) as app:
    with gr.Row():
        gr.Markdown("# U.S. Fair Market Rent Analysis", elem_classes="container")
    
    with gr.Row(equal_height=True):
        with gr.Column(scale=1):
            with gr.Group(elem_classes="stats-panel"):
                bedroom_select = gr.Dropdown(
                    choices=["0-Bedroom", "1-Bedroom", "2-Bedroom", "3-Bedroom", "4-Bedroom"],
                    value="2-Bedroom",
                    label="Select Bedroom Size"
                )
                
                metric_select = gr.Dropdown(
                    choices=list(METRIC_INFO.keys()),
                    value="FMR",
                    label="Select Metric"
                )
                
                metric_description = gr.Markdown(
                    value="", 
                    elem_classes="metric-info"
                )
                
                stats_output = gr.Dataframe(
                    headers=["Metric", "Value"],
                    label="Statistics",
                    interactive=False
                )
                
                gr.Markdown(
                    ALL_METRICS_DISPLAY,
                    elem_classes="all-metrics"
                )

        with gr.Column(scale=2):
            with gr.Group(elem_classes="map-container"):
                map_output = gr.Plot()

    def update_display(bedroom_type, metric_type):
        stats = get_stats(bedroom_type, metric_type)
        stats_data = [
            ["Mean", stats[0]],
            ["Median", stats[1]],
            ["Minimum", stats[2]],
            ["Maximum", stats[3]],
            ["Counties", stats[4]],
            ["Std Dev", stats[5]],
            ["25th Percentile", stats[6]],
            ["75th Percentile", stats[7]]
        ]
        description = f"**{metric_type}**: {METRIC_INFO[metric_type]['description']}"
        return (
            create_map(bedroom_type, metric_type),
            stats_data,
            description
        )

    bedroom_select.change(
        update_display,
        inputs=[bedroom_select, metric_select],
        outputs=[map_output, stats_output, metric_description]
    )
    
    metric_select.change(
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