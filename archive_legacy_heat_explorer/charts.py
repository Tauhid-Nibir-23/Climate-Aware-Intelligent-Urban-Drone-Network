import plotly.express as px
import plotly.graph_objects as go
from .demo_simulation import Scenario, run_demo_simulation

THEME = dict(template="plotly_dark", paper_bgcolor="#071522", plot_bgcolor="#0b2030", font_color="#d9f2f4")

def distribution_chart(grid):
    fig = px.histogram(grid, x="intensity", nbins=25, color_discrete_sequence=["#ff9b35"], title="Relative heat intensity distribution")
    fig.update_layout(**THEME, xaxis_title="Illustrative relative intensity (0–1)", yaxis_title="Synthetic grid-cell count")
    return fig

def histogram_chart(grid):
    fig = px.scatter(grid, x="lon", y="lat", color="intensity", color_continuous_scale=["#1856a8", "#00cbd1", "#ffe348", "#ff8b2b", "#d72d25"], title="Spatial intensity pattern (synthetic)")
    fig.update_layout(**THEME, xaxis_title="Longitude", yaxis_title="Latitude", coloraxis_colorbar_title="Relative<br>intensity")
    return fig

def comparison_chart(area, resolution):
    defaults = {Scenario.BASELINE:(.52,.38), Scenario.GREEN:(.72,.25), Scenario.BUILT:(.30,.68)}
    means = [run_demo_simulation(area, s, *defaults[s], resolution)["intensity"].mean() for s in Scenario]
    fig = go.Figure(go.Bar(x=[s.value.replace(" Demo", "") for s in Scenario], y=means, marker_color=["#38a7cb", "#55d89b", "#ff754b"]))
    fig.update_layout(**THEME, title="Illustrative scenario comparison", yaxis_title="Mean relative intensity (synthetic)", yaxis_range=[0, 1])
    return fig
