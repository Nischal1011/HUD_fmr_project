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

@functools.lru_cache(maxsize=5)
def create_map(bedroom_type, metric_type):
    """Generate interactive choropleth map"""
    gdf, geojson = load_data()
    bedroom_num = int(bedroom_type[0])
    
    metric_mapping = {
        'FMR': f'fmr_{bedroom_num}',
        'Rent-to-Income Ratio': f'rent_to_income_ratio_{bedroom_num}',
        'FMR vs Median Rent Difference': f'fmr_vs_median_rent_diff_{bedroom_num}',
        'FMR Deviation from Median Rent (%)': f'fmr_vs_median_rent_percent_{bedroom_num}',
        'Affordability Gap': f'affordability_gap_{bedroom_num}',
        'Voucher Feasibility': f'voucher_feasibility_{bedroom_num}',
        'Cost Burden': 'pct_cost_burdened',
        'Severe Cost Burden': 'pct_severe_cost_burdened',
        'Housing Wage': f'housing_wage_{bedroom_num}'
    }
    
    metric_col = metric_mapping[metric_type]
    
    if metric_type == 'FMR':
        format_str = '${:.2f}'
        prefix = '$'
    elif metric_type in ['Rent-to-Income Ratio', 'Cost Burden', 'Severe Cost Burden', 
                         'Voucher Feasibility', 'FMR Deviation from Median Rent (%)']:
        format_str = '{:.1f}%'
        prefix = ''
    elif metric_type == 'Housing Wage':
        format_str = '${:.2f}/hr'
        prefix = '$'
    else:
        format_str = '${:.2f}'
        prefix = '$'
    
    gdf['hover_text'] = gdf.apply(
        lambda x: f"<b>{x['county_name']}</b><br>"
                 f"State: {x['state_name']}<br>"
                 f"{metric_type}: {format_str.format(x[metric_col])}" if pd.notna(x[metric_col]) else "",
        axis=1
    )

    fig = go.Figure(go.Choropleth(
        geojson=geojson,
        locations=gdf['GEOID'],
        z=gdf[metric_col],
        featureidkey="properties.GEOID",
        colorscale='RdYlBu_r',
        marker_line_width=0.5,
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

    fig.update_layout(
        height=700,
        width=1200,
        margin=dict(r=20, t=40, l=20, b=20),
        geo=dict(
            scope='usa',
            projection=dict(type='albers usa'),
            showlakes=True,
            lakecolor='#e6f3f8',
            landcolor='#f9fafb',
            bgcolor='rgba(255,255,255,1)',
            center=dict(lat=39.8283, lon=-98.5795),
            lonaxis=dict(range=[-130, -65]),
            lataxis=dict(range=[20, 50]),
        ),
        hoverlabel=dict(
            bgcolor="white",
            font_size=14,
            font_family="Arial"
        ),
        font=dict(family="Inter", size=12),
        title={
            'text': f"{metric_type} Distribution - {bedroom_type} Units",
            'y': 0.95,
            'x': 0.5,
            'xanchor': 'center',
            'yanchor': 'top',
            'font': dict(size=20, family='Inter')
        }
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
        'FMR Deviation from Median Rent (%)': f'fmr_vs_median_rent_percent_{bedroom_num}',
        'Affordability Gap': f'affordability_gap_{bedroom_num}',
        'Voucher Feasibility': f'voucher_feasibility_{bedroom_num}',
        'Cost Burden': 'pct_cost_burdened',
        'Severe Cost Burden': 'pct_severe_cost_burdened',
        'Housing Wage': f'housing_wage_{bedroom_num}'
    }
    
    metric_col = metric_mapping[metric_type]
    gdf = gdf.dropna(subset=[metric_col])
    
    if metric_type in ['FMR', 'Affordability Gap']:
        format_str = '${:.2f}'
    elif metric_type == 'Housing Wage':
        format_str = '${:.2f}/hr'
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
    theme=gr.themes.Soft(
        primary_hue="blue",
        secondary_hue="gray",
        neutral_hue="stone",
        radius_size="md",
        font=["Arial", "sans-serif"]
    ),
    title="U.S. Fair Market Rent Analysis Dashboard",
    css="""
    /* Overall container styling */
    .gradio-container {
        background: #f3f4f6 !important; /* Light gray background for better contrast */
        width: 100% !important;
        max-width: none !important;
        margin: 0 !important;
        padding: 2rem !important;
        border-radius: 0 !important;
        box-shadow: none !important;
    }
    
    /* Map container */
    .plot-container {
        background: white !important;
        border-radius: 8px !important;
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1) !important;
        padding: 1rem !important;
    }
    
    /* Text styling */
    .prose {
        font-family: 'Arial', sans-serif !important;
        line-height: 1.6 !important;
        color: #1f2937 !important; /* Darker gray for better legibility */
    }
    
    /* Control and stats panels */
    .controls, .stats {
        background: white !important;
        padding: 1.5rem !important;
        border-radius: 8px !important;
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1) !important;
        border: 1px solid #e5e7eb !important; /* Light gray border */
    }
    
    /* Dropdown styling (matches screenshot) */
    .gradio-dropdown {
        background: white !important;
        border: 1px solid #d1d5db !important; /* Light gray border */
        border-radius: 4px !important;
        font-size: 1rem !important;
        color: #374151 !important; /* Dark gray text */
        padding: 0.5rem 1rem !important;
        box-shadow: none !important;
    }
    
    .gradio-dropdown:hover {
        border-color: #9ca3af !important; /* Slightly darker gray on hover */
        box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1) !important;
    }
    
    /* Accordion styling */
    .gradio-accordion {
        background: white !important;
        border-radius: 8px !important;
        border: 1px solid #e5e7eb !important;
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1) !important;
    }
    
    /* Stats list styling (matches screenshot) */
    .stats-list {
        list-style: none !important;
        padding: 0 !important;
        margin: 0 !important;
    }
    
    .stats-list li {
        margin-bottom: 0.75rem !important;
        font-size: 0.95rem !important;
        color: #4a5568 !important; /* Medium gray for values */
        line-height: 1.5 !important;
    }
    
    .stats-list li strong {
        color: #1f2937 !important; /* Darker gray for labels */
        font-weight: 600 !important;
        margin-right: 0.5rem !important;
    }
    
    /* Metric descriptions styling (matches screenshot) */
    .metric-descriptions {
        margin-top: 1rem !important;
        padding: 1rem !important;
        background: #f9fafb !important; /* Very light gray background */
        border-radius: 4px !important;
        border: 1px solid #e5e7eb !important;
    }
    
    .metric-descriptions p {
        margin: 0.5rem 0 !important;
        font-size: 0.9rem !important;
        color: #4a5568 !important; /* Medium gray text */
        line-height: 1.6 !important;
    }
    
    .metric-descriptions strong {
        color: #1f2937 !important; /* Darker gray for labels */
        font-weight: 600 !important;
    }
    
    .metric-descriptions em {
        color: #3b82f6 !important; /* Blue for emphasis, matching Gradio Soft theme */
        font-style: italic !important;
        font-weight: 500 !important;
    }
    
    /* Header styling */
    h1, h2, h3 {
        font-family: 'Arial', sans-serif !important;
        color: #1f2937 !important;
    }
    """
) as app:
    
    gr.Markdown("""
    <div style="text-align: center; padding: 2rem; 
                background: #3b82f6 !important; /* Blue from Soft theme */
                color: white;
                margin: -2rem -2rem 2rem -2rem;
                border-radius: 0;
                box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);">
        <h1 style="margin: 0; font-size: 2rem; font-weight: 700;
                   text-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);">
            🏘️ U.S. Fair Market Rent Analysis
        </h1>
        <p style="margin: 0.5rem 0 0; font-size: 1rem;
                  opacity: 0.9;">
            FY 2025 County-Level Housing Cost and Affordability Analysis
        </p>
    </div>
    """)

    with gr.Row(equal_height=False):
        with gr.Column(scale=1, min_width=350):  # Reduced width for compactness
            with gr.Group(elem_classes="controls"):
                gr.Markdown("### Dashboard Controls", elem_classes="prose")
                bedroom_select = gr.Dropdown(
                    choices=["0-Bedroom", "1-Bedroom", "2-Bedroom", "3-Bedroom", "4-Bedroom"],
                    value="2-Bedroom",
                    label="Bedroom",
                    container=False
                )
                
                metric_select = gr.Dropdown(
                    choices=[
                        "FMR",
                        "Rent-to-Income Ratio",
                        "FMR vs Median Rent Difference",
                        "FMR Deviation from Median Rent (%)",
                        "Affordability Gap",
                        "Voucher Feasibility",
                        "Cost Burden",
                        "Severe Cost Burden",
                        "Housing Wage"
                    ],
                    value="FMR vs Median Rent Difference",
                    label="Metric",
                    container=False
                )
                
                gr.Markdown("---", elem_classes="prose")
                
                with gr.Group(elem_classes="stats"):
                    gr.Markdown("### Market Statistics", elem_classes="prose")
                    stats_output = gr.HTML("""
                    <ul class="stats-list">
                        <li><strong>Average:</strong> -</li>
                        <li><strong>Median:</strong> -</li>
                        <li><strong>Minimum:</strong> -</li>
                        <li><strong>Maximum:</strong> -</li>
                        <li><strong>Counties:</strong> -</li>
                        <li><strong>Std Dev:</strong> -</li>
                        <li><strong>25th Pct:</strong> -</li>
                        <li><strong>75th Pct:</strong> -</li>
                    </ul>
                    """)

                gr.Markdown("---", elem_classes="prose")
                
                with gr.Accordion("Metric Descriptions", open=False):
                    gr.HTML("""
                    <div class="metric-descriptions">
                        <p><strong>FMR:</strong> Fair Market Rent set by HUD for different bedroom sizes ($). <em>Neutral - depends on context.</em></p>
                        <p><strong>Rent-to-Income Ratio:</strong> Annual FMR as a percentage of median household income (%). <em>Lower is better (less burden).</em></p>
                        <p><strong>FMR vs Median Rent Difference:</strong> Dollar difference between FMR and median gross rent ($). <em>Higher is better (FMR exceeds market rent).</em></p>
                        <p><strong>FMR Deviation from Median Rent (%):</strong> Percentage difference between FMR and median gross rent (%). <em>Higher is better (FMR exceeds market rent).</em></p>
                        <p><strong>Affordability Gap:</strong> Excess annual rent over 30% of median household income ($). <em>Lower is better (less unaffordable). Areas with no gap are excluded.</em></p>
                        <p><strong>Voucher Feasibility:</strong> FMR as a percentage of median gross rent, indicating voucher effectiveness (%). <em>Higher is better (vouchers cover more rent).</em></p>
                        <p><strong>Cost Burden:</strong> Percentage of renters spending more than 30% of income on rent (%). <em>Lower is better (fewer burdened renters).</em></p>
                        <p><strong>Severe Cost Burden:</strong> Percentage of renters spending more than 50% of income on rent (%). <em>Lower is better (fewer severely burdened).</em></p>
                        <p><strong>Housing Wage:</strong> Hourly wage needed to afford the selected bedroom FMR at 30% of income ($/hr). <em>Lower is better (more affordable).</em></p>
                    </div>
                    """)

        with gr.Column(scale=2):
            with gr.Group(elem_classes="plot-container"):
                map_title = gr.Markdown("## FMR vs Median Rent Difference Distribution - 2-Bedroom Units",
                                      elem_classes="prose")
                map_output = gr.Plot(label="", scale=1)

    gr.Markdown("""
    <div style="text-align: center; padding: 1rem; 
                color: #4a5568;
                font-size: 0.9rem;
                margin-top: 2rem;
                background: #f9fafb;
                border-radius: 8px;
                border: 1px solid #e5e7eb;
                box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);">
        Source: U.S. Department of Housing and Urban Development (HUD) FY 2025 Fair Market Rent Data
    </div>
    """, elem_classes="prose")

    def update_all(bedroom_type, metric_type):
        stats = get_stats(bedroom_type, metric_type)
        title = f"## {metric_type} Distribution - {bedroom_type} Units"
        stats_html = f"""
        <ul class="stats-list">
            <li><strong>Average:</strong> {stats[0]}</li>
            <li><strong>Median:</strong> {stats[1]}</li>
            <li><strong>Minimum:</strong> {stats[2]}</li>
            <li><strong>Maximum:</strong> {stats[3]}</li>
            <li><strong>Counties:</strong> {stats[4]}</li>
            <li><strong>Std Dev:</strong> {stats[5]}</li>
            <li><strong>25th Pct:</strong> {stats[6]}</li>
            <li><strong>75th Pct:</strong> {stats[7]}</li>
        </ul>
        """
        return (
            create_map(bedroom_type, metric_type),
            title,
            stats_html
        )

    bedroom_select.change(
        update_all,
        inputs=[bedroom_select, metric_select],
        outputs=[map_output, map_title, stats_output]
    )
    
    metric_select.change(
        update_all,
        inputs=[bedroom_select, metric_select],
        outputs=[map_output, map_title, stats_output]
    )

    app.load(
        lambda: update_all("2-Bedroom", "FMR vs Median Rent Difference"),
        outputs=[map_output, map_title, stats_output]
    )

if __name__ == "__main__":
    app.launch(server_port=2001, share=True)