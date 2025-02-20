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

    # Convert to web mercator projection
    gdf = gdf.to_crs(epsg=4326)
    
    # Remove rows where FMRs are 0
    fmr_cols = [f'fmr_{i}' for i in range(5)]
    gdf = gdf[~(gdf[fmr_cols] == 0).all(axis=1)]
    
    # Convert numeric columns
    numeric_cols = (
        fmr_cols +
        [f'rent_to_income_ratio_{i}' for i in range(5)] +
        [f'fmr_vs_median_rent_diff_{i}' for i in range(5)] +
        [f'affordability_gap_{i}' for i in range(5)] +
        ['pct_cost_burdened', 'pct_severe_cost_burdened', 'housing_wage_2']
    )
    gdf[numeric_cols] = gdf[numeric_cols].apply(pd.to_numeric, errors='coerce')
    
    return gdf, gdf.__geo_interface__

@functools.lru_cache(maxsize=5)
def create_map(bedroom_type, metric_type):
    """Generate interactive choropleth map"""
    gdf, geojson = load_data()
    bedroom_num = int(bedroom_type[0])
    
    metric_mapping = {
        'FMR': f'fmr_{bedroom_num}',
        'Rent-to-Income Ratio': f'rent_to_income_ratio_{bedroom_num}',
        'FMR vs Median Rent Difference': f'fmr_vs_median_rent_diff_{bedroom_num}',
        'Affordability Gap': f'affordability_gap_{bedroom_num}',
        'Cost Burden': 'pct_cost_burdened',
        'Severe Cost Burden': 'pct_severe_cost_burdened',
        'Housing Wage': 'housing_wage_2'
    }
    
    metric_col = metric_mapping[metric_type]
    
    # Configure hover text based on metric type
    if metric_type == 'FMR':
        format_str = '${:.2f}'
        prefix = '$'
    elif 'Ratio' in metric_type or 'Burden' in metric_type:
        format_str = '{:.1f}%'
        prefix = ''
    elif 'Wage' in metric_type:
        format_str = '${:.2f}/hr'
        prefix = '$'
    else:
        format_str = '${:.2f}'
        prefix = '$'
    
    gdf['hover_text'] = gdf.apply(
        lambda x: f"<b>{x['county_name']}</b><br>"
                 f"State: {x['state_name']}<br>"
                 f"{metric_type}: {format_str.format(x[metric_col])}",
        axis=1
    )

    fig = go.Figure(go.Choropleth(
        geojson=geojson,
        locations=gdf['GEOID'],
        z=gdf[metric_col],
        featureidkey="properties.GEOID",
        colorscale='RdYlBu_r',
        marker_line_width=0.3,
        marker_line_color='white',
        hoverinfo="text",
        hovertext=gdf['hover_text'],
        colorbar=dict(
            title=dict(text=metric_type, font=dict(size=14)),
            thickness=20,
            len=0.75,
            tickfont=dict(size=12),
            tickformat=f"{prefix},.0f" if 'FMR' in metric_type else ".1f"
        )
    ))

    # Improved layout with larger map size
    fig.update_layout(
        height=700,  # Increased height
        width=1200,  # Set explicit width
        margin=dict(r=0, t=0, l=0, b=0),
        geo=dict(
            scope='usa',
            projection=dict(type='albers usa'),
            showlakes=True,
            lakecolor='#d4e8f2',
            landcolor='#f5f5f5',
            bgcolor='rgba(255,255,255,1)',
            # Adjust map position and size
            center=dict(lat=39.8283, lon=-98.5795),
            lonaxis=dict(range=[-130, -65]),
            lataxis=dict(range=[20, 50]),
        ),
        hoverlabel=dict(
            bgcolor="white",
            font_size=14,
            font_family="Arial"
        ),
        autosize=True  # Enable responsive sizing
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
        'Affordability Gap': f'affordability_gap_{bedroom_num}',
        'Cost Burden': 'pct_cost_burdened',
        'Severe Cost Burden': 'pct_severe_cost_burdened',
        'Housing Wage': 'housing_wage_2'
    }
    
    metric_col = metric_mapping[metric_type]
    
    if metric_type == 'FMR' or 'Gap' in metric_type or 'Wage' in metric_type:
        format_str = '${:.2f}'
    else:
        format_str = '{:.1f}%'
    
    return (
        format_str.format(gdf[metric_col].mean()),
        format_str.format(gdf[metric_col].median()),
        f"{format_str.format(gdf[metric_col].min())} ({gdf.loc[gdf[metric_col].idxmin(), 'county_name']})",
        f"{format_str.format(gdf[metric_col].max())} ({gdf.loc[gdf[metric_col].idxmax(), 'county_name']})",
        f"{len(gdf):,}",
        format_str.format(gdf[metric_col].std()),
        format_str.format(gdf[metric_col].quantile(0.25)),
        format_str.format(gdf[metric_col].quantile(0.75))
    )

with gr.Blocks(
    theme=gr.themes.Soft(primary_hue="blue"),
    title="Enhanced FMR Dashboard",
    css="""
    .gradio-container {
        background: white !important;
        max-width: 100% !important;
        padding: 0 !important;
    }
    .plot-container {
        width: 100% !important;
        height: 100% !important;
    }
    """
) as app:
    
    # Header
    gr.Markdown("""
    <div style="text-align: center; padding: 1.5rem; 
                background: linear-gradient(135deg, #2563eb, #1d4ed8);
                color: white; 
                margin-bottom: 1rem;">
        <h1 style="margin: 0; font-size: 2rem; font-weight: 600;
                   font-family: 'Inter', sans-serif;">
            🏘️ U.S. Fair Market Rent Analysis
        </h1>
        <div style="margin-top: 0.6rem; font-size: 1.1rem;
                   font-family: 'Inter', sans-serif;">
            FY 2025 County-Level Housing Cost and Affordability Analysis
        </div>
    </div>
    """)

    # Main content with improved layout
    with gr.Row(equal_height=True):
        # Controls Column (made narrower)
        with gr.Column(scale=1, min_width=250):
            gr.Markdown("### Dashboard Controls")
            bedroom_select = gr.Dropdown(
                choices=["0-Bedroom", "1-Bedroom", "2-Bedroom", "3-Bedroom", "4-Bedroom"],
                value="2-Bedroom",
                label="Select Unit Type"
            )
            
            metric_select = gr.Dropdown(
                choices=[
                    "FMR",
                    "Rent-to-Income Ratio",
                    "FMR vs Median Rent Difference",
                    "Affordability Gap",
                    "Cost Burden",
                    "Severe Cost Burden",
                    "Housing Wage"
                ],
                value="FMR",
                label="Select Metric"
            )
            
            gr.Markdown("---")
            
            # Metrics Display
            gr.Markdown("### Market Statistics")
            avg_metric = gr.Markdown()
            median_metric = gr.Markdown()
            min_metric = gr.Markdown()
            max_metric = gr.Markdown()
            counties = gr.Markdown()
            std_dev = gr.Markdown()
            pct25 = gr.Markdown()
            pct75 = gr.Markdown()

        # Map Column (made wider)
        with gr.Column(scale=5):
            map_title = gr.Markdown()
            map_output = gr.Plot(label="", scale=1)

    # Footer
    gr.Markdown("""
    <div style="text-align: center; padding: 1rem; 
              color: #64748b; font-size: 0.85rem;
              margin-top: 1rem;">
        Source: U.S. Department of Housing and Urban Development (HUD) FY 2025 Fair Market Rent Data
    </div>
    """)

    def update_all(bedroom_type, metric_type):
        stats = get_stats(bedroom_type, metric_type)
        title = f"## {metric_type} Distribution - {bedroom_type} Units"
        return (
            create_map(bedroom_type, metric_type),
            title,
            f"**Average {metric_type}:** {stats[0]}",
            f"**Median {metric_type}:** {stats[1]}",
            f"**Minimum {metric_type}:** {stats[2]}",
            f"**Maximum {metric_type}:** {stats[3]}",
            f"**Counties Analyzed:** {stats[4]}",
            f"**Standard Deviation:** {stats[5]}",
            f"**25th Percentile:** {stats[6]}",
            f"**75th Percentile:** {stats[7]}"
        )

    # Event handlers
    bedroom_select.change(
        update_all,
        inputs=[bedroom_select, metric_select],
        outputs=[map_output, map_title, avg_metric, median_metric,
                min_metric, max_metric, counties, std_dev, pct25, pct75]
    )
    
    metric_select.change(
        update_all,
        inputs=[bedroom_select, metric_select],
        outputs=[map_output, map_title, avg_metric, median_metric,
                min_metric, max_metric, counties, std_dev, pct25, pct75]
    )

    # Initial load
    app.load(
        lambda: update_all("2-Bedroom", "FMR"),
        outputs=[map_output, map_title, avg_metric, median_metric,
                min_metric, max_metric, counties, std_dev, pct25, pct75]
    )

if __name__ == "__main__":
    app.launch(server_port=2000, share=True)