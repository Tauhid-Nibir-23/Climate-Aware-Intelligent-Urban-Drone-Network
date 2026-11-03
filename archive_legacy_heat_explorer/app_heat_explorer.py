"""Dumki Urban Heat Explorer — illustrative Phase 1 prototype."""
from __future__ import annotations

import streamlit as st
from streamlit_folium import st_folium

from src.charts import comparison_chart, distribution_chart, histogram_chart
from src.config import DISCLAIMER, STUDY_AREA
from src.demo_simulation import Scenario, run_demo_simulation
from src.geographic_data import load_boundary_context
from src.heatmap import build_map
from src.statistics import summary_statistics

st.set_page_config(page_title="Dumki Urban Heat Explorer", page_icon="🌡️", layout="wide")

st.markdown("""
<style>
 .stApp { background: #071522; color: #e7f4f6; }
 [data-testid="stSidebar"] { background: #0b2030; border-right: 1px solid #1d5262; }
 h1 { color: #dffbff; letter-spacing: .08em; font-size: 2.0rem !important; }
 h2, h3 { color: #61e2df; }
 .eyebrow { color:#77aeba; letter-spacing:.16em; font-size:.76rem; font-weight:700; }
 .disclaimer { background:#4d271d; border-left:4px solid #ff9d45; padding:11px 15px; border-radius:5px; color:#fff1dc; font-weight:600; }
 [data-testid="stMetric"] { background:#0e2838; border:1px solid #20536a; padding:12px; border-radius:8px; }
</style>
""", unsafe_allow_html=True)

with st.sidebar:
    st.markdown("### Simulation controls")
    scenario_label = st.selectbox("Illustrative scenario", [s.value for s in Scenario])
    scenario = Scenario(scenario_label)
    defaults = {Scenario.BASELINE: (0.52, 0.38), Scenario.GREEN: (0.72, 0.25), Scenario.BUILT: (0.30, 0.68)}
    vegetation, built_up = defaults[scenario]
    vegetation = st.slider("Vegetation coverage parameter", 0.0, 1.0, vegetation, 0.01)
    built_up = st.slider("Built-up surface parameter", 0.0, 1.0, built_up, 0.01)
    opacity = st.slider("Heatmap opacity", 0.10, 0.90, 0.58, 0.02)
    resolution = st.select_slider("Grid resolution", options=[12, 16, 20, 24, 30, 36], value=24)
    threshold = st.slider("Relative intensity threshold", 0.0, 1.0, 0.25, 0.01)
    st.divider()
    st.caption("All controls operate on a deterministic, synthetic demonstration model.")

st.markdown('<div class="eyebrow">SPATIAL ENVIRONMENTAL RESEARCH PROTOTYPE · PHASE 1</div>', unsafe_allow_html=True)
st.title("DUMKI URBAN HEAT EXPLORER")
st.caption("Interactive Urban Heat Island Simulation | Dumki, Patuakhali, Bangladesh")
st.markdown(f'<div class="disclaimer">{DISCLAIMER}</div>', unsafe_allow_html=True)

boundary = load_boundary_context()
grid = run_demo_simulation(STUDY_AREA, scenario, vegetation, built_up, resolution)
visible_grid = grid[grid["intensity"] >= threshold].copy()
stats = summary_statistics(grid)

left, right = st.columns([2.35, 1], gap="large")
with left:
    st.subheader("Illustrative Relative Heat Intensity (0–1)")
    st.caption(boundary.message)
    fmap = build_map(STUDY_AREA, visible_grid, opacity, boundary.geometry)
    map_state = st_folium(fmap, height=590, use_container_width=True, returned_objects=["last_clicked"])
    if map_state.get("last_clicked"):
        click = map_state["last_clicked"]
        st.info(f"Map click: {click['lat']:.5f}° N, {click['lng']:.5f}° E. Grid popups contain illustrative intensity values.")
with right:
    st.subheader("Synthetic demo summary")
    st.metric("Grid cells", f"{stats['count']:,}")
    st.metric("Mean relative intensity", f"{stats['mean']:.3f}")
    st.metric("Maximum relative intensity", f"{stats['maximum']:.3f}")
    st.metric("Minimum relative intensity", f"{stats['minimum']:.3f}")
    st.caption(f"{len(visible_grid):,} cells currently meet the display threshold of {threshold:.2f}.")
    st.markdown("#### Map key")
    st.markdown("🔵 Low  ·  🟦 Moderate  ·  🟨 Elevated  ·  🟧 High  ·  🔴 Highest")
    st.caption("No colour represents observed temperature, degrees Celsius, or a validated prediction.")

st.divider()
chart_a, chart_b = st.columns(2)
with chart_a:
    st.plotly_chart(distribution_chart(grid), use_container_width=True)
    st.plotly_chart(histogram_chart(grid), use_container_width=True)
with chart_b:
    st.plotly_chart(comparison_chart(STUDY_AREA, resolution), use_container_width=True)
    st.markdown("#### Geographic context")
    st.write("The map begins with the requested approximate Dumki viewing extent. It is intentionally labelled as an extent, not an official boundary, until a verified open administrative polygon is added to `data/boundaries/`.")
    st.caption("Verified union labels can be added only with reliable source coordinates; none are fabricated in this prototype.")
