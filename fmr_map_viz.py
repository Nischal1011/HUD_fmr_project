import gradio as gr
import geopandas as gpd
import pandas as pd
import functools
import plotly.graph_objects as go

@functools.lru_cache(maxsize=None)
def load_data():
    """Load and validate geographic data"""
    df = pd.read_csv("data/county_fmr.csv", dtype={'GEOID': str})
    df['geometry'] = gpd.GeoSeries.from_wkt(df['geometry'])
    gdf = gpd.GeoDataFrame(df, crs="EPSG:4269").to_crs(epsg=4326)
    
    fmr_cols = [f'fmr_{i}' for i in range(5)]
    gdf[fmr_cols] = gdf[fmr_cols].apply(pd.to_numeric, errors='coerce')
    
    return gdf, gdf.__geo_interface__

@functools.lru_cache(maxsize=5)
def create_map(bedroom_type):
    """Generate interactive choropleth map"""
    gdf, geojson = load_data()
    bedroom_num = int(bedroom_type[0])
    fmr_col = f'fmr_{bedroom_num}'
    
    gdf['hover_text'] = gdf.apply(
        lambda x: f"<b>{x['county_name']}</b><br>"
                  f"State: {x['state_name']}<br>"
                  f"FMR: ${x[fmr_col]:.2f}",
        axis=1
    )

    fig = go.Figure(go.Choropleth(
        geojson=geojson,
        locations=gdf['GEOID'],
        z=gdf[fmr_col],
        featureidkey="properties.GEOID",
        colorscale='RdYlBu_r',
        marker_line_width=0.3,
        marker_line_color='white',
        hoverinfo="text",
        hovertext=gdf['hover_text'],
        colorbar=dict(
            title=dict(text="Monthly Rent ($)", font=dict(size=14)),
            thickness=20,
            len=0.75,
            tickfont=dict(size=12),
            tickformat="$,.0f"
        )
    ))

    fig.update_layout(
        height=800,
        margin=dict(r=0, t=0, l=0, b=0),
        geo=dict(
            scope='usa',
            projection=dict(type='albers usa'),
            showlakes=True,
            lakecolor='#d4e8f2',
            landcolor='#f5f5f5',
            bgcolor='rgba(255,255,255,1)',
        ),
        hoverlabel=dict(
            bgcolor="white",
            font_size=14,
            font_family="Arial"
        )
    )
    
    return fig

def get_stats(bedroom_type):
    """Calculate market statistics"""
    gdf, _ = load_data()
    bedroom_num = int(bedroom_type[0])
    fmr_col = f'fmr_{bedroom_num}'
    
    return (
        f"${gdf[fmr_col].mean():.2f}",
        f"${gdf[fmr_col].median():.2f}",
        f"${gdf[fmr_col].min():.2f} ({gdf.loc[gdf[fmr_col].idxmin(), 'county_name']})",
        f"${gdf[fmr_col].max():.2f} ({gdf.loc[gdf[fmr_col].idxmax(), 'county_name']})",
        f"{len(gdf):,}",
        f"${gdf[fmr_col].std():.2f}",
        f"${gdf[fmr_col].quantile(0.25):.2f}",
        f"${gdf[fmr_col].quantile(0.75):.2f}"
    )

with gr.Blocks(theme=gr.themes.Soft(primary_hue="blue"), 
              title="FMR Dashboard",
              css=".gradio-container {background: white !important}") as app:
    
    # Header
    gr.Markdown("""
    <div style="text-align: center; padding: 1.5rem; 
                background: linear-gradient(135deg, #2563eb, #1d4ed8);
                color: white; 
                margin-bottom: 1rem;
                border-radius: 8px;">
        <h1 style="margin: 0; font-size: 2rem; font-weight: 600;
                   font-family: 'Inter', sans-serif;">
            🏘️ U.S. Fair Market Rent Analysis
        </h1>
        <div style="margin-top: 0.6rem; font-size: 1.1rem;
                   font-family: 'Inter', sans-serif;">
            FY 2025 County-Level Housing Cost Distribution
        </div>
    </div>
    """)
    
    with gr.Row(variant="panel", equal_height=True):
        # Controls Column
        with gr.Column(scale=1, min_width=300):
            gr.Markdown("### Dashboard Controls")
            bedroom_select = gr.Dropdown(
                choices=["0-Bedroom", "1-Bedroom", "2-Bedroom", "3-Bedroom", "4-Bedroom"],
                value="2-Bedroom",
                label="Select Unit Type"
            )
            
            gr.Markdown("---")
            
            # Metrics Display
            gr.Markdown("### Market Statistics")
            avg_rent = gr.Markdown()
            median_rent = gr.Markdown()
            min_rent = gr.Markdown()
            max_rent = gr.Markdown()
            counties = gr.Markdown()
            std_dev = gr.Markdown()
            pct25 = gr.Markdown()
            pct75 = gr.Markdown()

        # Map Column
        with gr.Column(scale=4):
            map_title = gr.Markdown("## Fair Market Rent Distribution - 2-Bedroom Units")
            map_output = gr.Plot(label="")

    # Footer
    gr.Markdown("""
    <div style="text-align: center; padding: 1rem; 
              color: #64748b; font-size: 0.85rem;
              margin-top: 1rem;">
        Source: U.S. Department of Housing and Urban Development (HUD) FY 2025 Fair Market Rent Data
    </div>
    """)
    
    # Custom CSS
    app.css = """
    .gradio-container {
        padding: 1rem !important;
        background: white !important;
        max-width: 100% !important;
    }
    
    .gradio-plot {
        border-radius: 8px !important;
        border: 1px solid #e5e7eb !important;
        box-shadow: 0 1px 3px rgba(0,0,0,0.05);
        margin-top: 0.5rem !important;
    }
    
    .gradio-markdown {
        padding: 0.75rem !important;
        background: white !important;
        border-radius: 6px !important;
        margin: 0.25rem 0 !important;
    }
    
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600&display=swap');
    """

    # Update function
    def update_all(bedroom_type):
        stats = get_stats(bedroom_type)
        title = f"## Fair Market Rent Distribution - {bedroom_type} Units"
        return (create_map(bedroom_type), title, \
            f"**Average Rent:** {stats[0]}", \
            f"**Median Rent:** {stats[1]}", \
            f"**Minimum Rent:** {stats[2]}", \
            f"**Maximum Rent:** {stats[3]}", \
            f"**Counties Analyzed:** {stats[4]}", \
            f"**Standard Deviation:** {stats[5]}", \
            f"**25th Percentile:** {stats[6]}", \
            f"**75th Percentile:** {stats[7]}")

    bedroom_select.change(
        update_all,
        inputs=bedroom_select,
        outputs=[map_output, map_title, avg_rent, median_rent, 
                min_rent, max_rent, counties, std_dev, pct25, pct75]
    )

    app.load(
        lambda: update_all("2-Bedroom"),
        outputs=[map_output, map_title, avg_rent, median_rent, 
                min_rent, max_rent, counties, std_dev, pct25, pct75]
    )

if __name__ == "__main__":
    app.launch(server_port=2000, share=True)