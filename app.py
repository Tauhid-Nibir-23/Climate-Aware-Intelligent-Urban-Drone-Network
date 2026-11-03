"""
Climate-Aware Intelligent Urban Drone Network
Interactive Simulation Dashboard — Dumki Upazila & PSTU Campus Focus
Course: Simulation and Modeling
"""
import copy
import streamlit as st
import pandas as pd
import plotly.express as px
from streamlit_folium import st_folium

from src.config import WEATHER_SCENARIOS, DroneSpecs
from src.network import DumkiNetwork
from src.models import Drone
from src.generator import generate_synthetic_requests
from src.algorithms import FCFSDispatcher, BatteryAwareDispatcher
from src.simulation import DroneDeliverySimulation
from src.map_view import build_dumki_folium_map
from src.radar_view import generate_radar_theater_html
import streamlit.components.v1 as components

# Page configuration
st.set_page_config(
    page_title="PSTU & Dumki Drone Network",
    page_icon="🚁",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom modern CSS styling
st.markdown("""
<style>
    .main-header { font-size: 2.2rem; font-weight: 800; color: #00e5ff; margin-bottom: 2px; }
    .sub-header { font-size: 1.05rem; color: #cbd5e0; margin-bottom: 18px; }
    .badge-campus {
        background: #2b6cb0;
        color: white;
        padding: 3px 8px;
        border-radius: 4px;
        font-size: 0.82rem;
        font-weight: 600;
    }
    .badge-hub {
        background: #c53030;
        color: white;
        padding: 3px 8px;
        border-radius: 4px;
        font-size: 0.82rem;
        font-weight: 600;
    }
    .stTabs [data-baseweb="tab-list"] { gap: 8px; }
    .stTabs [data-baseweb="tab"] { border-radius: 6px; padding: 10px 18px; font-weight: 600; }
</style>
""", unsafe_allow_html=True)

# Initialize spatial network
@st.cache_resource
def load_network():
    return DumkiNetwork()

network = load_network()

# Sidebar: Simulation Controls
with st.sidebar:
    st.image("https://img.icons8.com/fluency/96/drone.png", width=64)
    st.markdown("### ⚙️ Simulation Controls")
    
    fleet_size = st.slider("Fleet Size (Drones)", min_value=2, max_value=8, value=4, step=1)
    charging_bays = st.slider("PSTU Central Charging Bays (c)", min_value=1, max_value=4, value=2, step=1)
    num_requests = st.slider("Total Delivery Orders", min_value=10, max_value=50, value=25, step=5)
    arrival_rate = st.slider("Arrival Rate (Orders/Hour)", min_value=2.0, max_value=12.0, value=6.0, step=1.0)
    
    st.divider()
    st.markdown("### 🌤️ Climate & Weather Scenario")
    weather_key = st.selectbox("Weather Condition", list(WEATHER_SCENARIOS.keys()), index=0)
    weather = WEATHER_SCENARIOS[weather_key]
    st.info(f"**{weather.name}**\n\n{weather.description}\n\n*Flight Power Penalty:* **{weather.climate_multiplier:.2f}x**")
    
    st.divider()
    random_seed = st.number_input("Random Seed (Reproducibility)", min_value=1, max_value=9999, value=42, step=1)

# Header Section
st.markdown('<div class="main-header">CLIMATE-AWARE INTELLIGENT URBAN DRONE NETWORK</div>', unsafe_allow_html=True)
st.markdown(
    '<div class="sub-header">'
    '<b>Spatial-Temporal Discrete-Event Simulation</b> | Primary Hub: '
    '<span class="badge-hub">PSTU Main Campus</span> | Regional Study Area: '
    '<span class="badge-campus">Dumki Upazila, Patuakhali</span>'
    '</div>',
    unsafe_allow_html=True
)

# Generate baseline requests
base_requests = generate_synthetic_requests(
    network=network,
    num_requests=num_requests,
    arrival_rate_per_hour=arrival_rate,
    random_seed=int(random_seed)
)

def build_fleet(n: int):
    return [Drone(drone_id=f"DRONE-{i+1:02d}", specs=DroneSpecs()) for i in range(n)]

# Main Navigation Tabs
tab_radar, tab_map, tab_benchmark, tab_logs, tab_about = st.tabs([
    "🎬 2D Live Mission Radar (Cinema)",
    "🗺️ Interactive Real-World Map (PSTU & Dumki)",
    "🚀 Benchmark Experiment",
    "📋 Discrete-Event Logs",
    "📖 Architecture & Viva Prep"
])

with tab_radar:
    st.markdown("### 🎬 2D Cinematic Drone Mission Radar • PSTU Command Center")
    st.caption("Live 60 FPS Canvas visualization showing autonomous drones taking off from PSTU, flying to delivery points, and recharging.")

    # Automatically generate live radar animation from simulation run
    fleet_demo = build_fleet(fleet_size)
    sim_demo = DroneDeliverySimulation(
        network=network,
        drones=fleet_demo,
        requests=copy.deepcopy(base_requests),
        dispatcher=BatteryAwareDispatcher(),
        weather=weather,
        num_charging_bays=charging_bays
    )
    sim_demo.run(max_duration_min=240.0)
    demo_events = sim_demo.events_log
    fleet_ids = [d.drone_id for d in fleet_demo]

    radar_html = generate_radar_theater_html(network, demo_events, fleet_ids)
    components.html(radar_html, height=620)
    
    st.info("💡 **Controls:** Use the Play/Pause button, drag the Timeline slider to scrub through simulated minutes, or speed up playback (1x, 3x, 8x).")

with tab_map:
    st.markdown("### 🛰️ Dumki & PSTU Campus Spatial Network Map")
    st.caption("Real geographic tiles from OpenStreetMap & Satellite. Click markers for node details and air corridor telemetry.")

    col_map_ctrl1, col_map_ctrl2, col_map_ctrl3 = st.columns([2, 2, 2])
    with col_map_ctrl1:
        map_focus = st.radio(
            "Map Focus View:",
            ["PSTU Campus View", "Full Dumki Regional View"],
            horizontal=True
        )
    with col_map_ctrl2:
        show_lines = st.checkbox("Show Air Corridors (Direct Flight Paths)", value=True)
    with col_map_ctrl3:
        st.markdown(
            f"**Depot:** `PSTU Central Command Hub`<br>"
            f"**Active Delivery Nodes:** `{len(network.delivery_nodes)} locations`",
            unsafe_allow_html=True
        )

    # Render Folium Map
    folium_map = build_dumki_folium_map(network, focus_mode=map_focus, show_flight_corridors=show_lines)
    st_folium(folium_map, width="100%", height=520)

    # Detailed Node Telemetry Table
    st.markdown("#### 📍 Air Corridor Distance & Flight Telemetry from PSTU Central Hub")
    depot_id = network.get_depot_id()
    node_rows = []
    for dest_id, n in network.delivery_nodes.items():
        dist = network.get_distance_km(depot_id, dest_id)
        flight_sec = (dist * 1000.0 / 12.0) + 60.0
        node_rows.append({
            "Location Name": n["name"],
            "Zone": n.get("zone", "Dumki Regional"),
            "Type": n["type"].replace("_", " ").title(),
            "Distance from PSTU (km)": f"{dist:.2f} km",
            "Est. Flight Time": f"{flight_sec/60.0:.1f} mins",
            "Base Energy (Loaded 1.5kg)": f"{(210.0 + 45.0*1.5) * (flight_sec/3600.0):.1f} Wh"
        })
    st.dataframe(pd.DataFrame(node_rows), use_container_width=True)

with tab_benchmark:
    st.markdown("### ⚔️ Comparative Performance: Baseline FCFS vs. Proposed Battery-Aware Dispatcher")
    st.caption("Evaluates mission safety under identical stochastic order arrival streams and physical battery constraints.")

    col_btn, col_blank = st.columns([1, 3])
    with col_btn:
        run_experiment = st.button("▶ Run Head-to-Head Simulation", use_container_width=True, type="primary")

    if run_experiment:
        # Run Baseline (FCFS)
        fleet_fcfs = build_fleet(fleet_size)
        sim_fcfs = DroneDeliverySimulation(
            network=network,
            drones=fleet_fcfs,
            requests=copy.deepcopy(base_requests),
            dispatcher=FCFSDispatcher(),
            weather=weather,
            num_charging_bays=charging_bays
        )
        sim_fcfs.run(max_duration_min=480.0)
        metrics_fcfs = sim_fcfs.get_summary_metrics()

        # Run Proposed (Battery-Aware)
        fleet_bapa = build_fleet(fleet_size)
        sim_bapa = DroneDeliverySimulation(
            network=network,
            drones=fleet_bapa,
            requests=copy.deepcopy(base_requests),
            dispatcher=BatteryAwareDispatcher(),
            weather=weather,
            num_charging_bays=charging_bays
        )
        sim_bapa.run(max_duration_min=480.0)
        metrics_bapa = sim_bapa.get_summary_metrics()

        # Metrics cards
        m1, m2, m3, m4 = st.columns(4)
        with m1:
            delta_sr = metrics_bapa["success_rate_pct"] - metrics_fcfs["success_rate_pct"]
            st.metric("Success Rate (Battery-Aware)", f"{metrics_bapa['success_rate_pct']}%", f"{delta_sr:+.1f}% vs FCFS Baseline")
        with m2:
            st.metric("Successful Deliveries", f"{metrics_bapa['delivered_orders']} / {num_requests}", f"{metrics_fcfs['failed_orders']} FCFS Crashes/Failures")
        with m3:
            st.metric("Avg Order Turnaround", f"{metrics_bapa['avg_delivery_time_min']} min", f"{metrics_bapa['avg_delivery_time_min'] - metrics_fcfs['avg_delivery_time_min']:+.1f} min")
        with m4:
            st.metric("Total Fleet Energy", f"{metrics_bapa['total_energy_consumed_wh']:.1f} Wh", f"{weather.climate_multiplier:.2f}x Weather Penalty")

        # Visual Comparison Charts
        st.markdown("#### 📊 Quantitative Benchmark Results")
        comp_df = pd.DataFrame([metrics_fcfs, metrics_bapa])
        
        c1, c2 = st.columns(2)
        with c1:
            fig_sr = px.bar(
                comp_df,
                x="algorithm",
                y="success_rate_pct",
                color="algorithm",
                title="Delivery Mission Success Rate (%)",
                text="success_rate_pct",
                color_discrete_map={"Baseline (FCFS + Greedy)": "#e53e3e", "Proposed (Battery-Aware)": "#38b2ac"}
            )
            fig_sr.update_layout(paper_bgcolor="#0c1724", plot_bgcolor="#0c1724", font=dict(color="#e2e8f0"), showlegend=False)
            st.plotly_chart(fig_sr, use_container_width=True)

        with c2:
            fig_wait = px.bar(
                comp_df,
                x="algorithm",
                y="total_charging_wait_min",
                color="algorithm",
                title="Total Charging Bay Queue Delay (min)",
                text="total_charging_wait_min",
                color_discrete_map={"Baseline (FCFS + Greedy)": "#e53e3e", "Proposed (Battery-Aware)": "#38b2ac"}
            )
            fig_wait.update_layout(paper_bgcolor="#0c1724", plot_bgcolor="#0c1724", font=dict(color="#e2e8f0"), showlegend=False)
            st.plotly_chart(fig_wait, use_container_width=True)

        # Fleet Telemetry
        st.markdown("#### 🚁 Individual Drone Fleet Telemetry (Battery-Aware Dispatch)")
        fleet_data = [{
            "Drone ID": d.drone_id,
            "Completed Missions": d.total_deliveries,
            "Distance Flown (km)": round(d.total_distance_km, 2),
            "Energy Used (Wh)": round(d.total_energy_consumed_wh, 2),
            "Final Battery Level (SoC)": f"{d.battery.current_soc*100:.1f}%",
            "Charging Queue Wait (min)": round(d.total_charging_wait_min, 1)
        } for d in fleet_bapa]
        st.dataframe(pd.DataFrame(fleet_data), use_container_width=True)

        # Store latest logs in session state
        st.session_state["latest_events"] = sim_bapa.get_event_log_df()
    else:
        st.info("👆 Click **'Run Head-to-Head Simulation'** above to run SimPy discrete-event simulation and generate live benchmark charts.")

with tab_logs:
    st.markdown("### 📋 Chronological Discrete-Event Execution Logs")
    if "latest_events" in st.session_state:
        df_logs = st.session_state["latest_events"]
        st.dataframe(df_logs, use_container_width=True)
        csv = df_logs.to_csv(index=False).encode('utf-8')
        st.download_button("📥 Download Event Logs (CSV)", csv, "dumki_pstu_drone_events.csv", "text/csv")
    else:
        st.warning("No simulation has been run yet in this session. Go to 'Benchmark Experiment' tab and click Run.")

with tab_about:
    st.markdown(r"""
    ### System Architecture & Mathematical Formulation
    
    #### 1. PSTU & Dumki Spatial Topology
    - **Central Hub**: Patuakhali Science and Technology University (PSTU) Central Drone Station ($22.4648^\circ\text{ N}, 90.3835^\circ\text{ E}$).
    - **Direct Air Corridors**: Modeled as straight-line Euclidean aerial vectors calculated via the **Haversine formula**.
    - **Service Radius**: Encompasses both high-frequency campus deliveries (CSE Faculty, Medical Center, Halls) and regional rural medical delivery (Dumki Hospital, Pangashia, Muradia, Lebukhali).
    
    #### 2. Flight Power & Climate Derating Formula
    $$P_{flight}(m_{payload}) = (P_{base} + \alpha_{payload} \cdot m_{payload}) \times \kappa_{climate}$$
    $$\kappa_{climate} = 1.0 + 0.015 \cdot \max(0, T_{ambient} - 28^\circ\text{C}) + 0.030 \cdot v_{headwind}$$
    
    #### 3. Course Viva Summary & Defense Points
    - **Why SimPy?** Avoids step-by-step frame looping; processes state transitions at discrete event timestamps, executing 8 hours of operations in < 2 seconds.
    - **Why Battery-Aware Dispatching?** Baseline FCFS naively dispatches drones without pre-checking round-trip energy feasibility, causing mid-flight battery exhaustion. Our proposed method verifies $SoC \ge SoC_{trip} + SoC_{reserve}$ before takeoff.
    - **Queuing Realism ($M/M/c$):** When fleet size ($N=4$) exceeds charging bays ($c=2$), returning drones must wait in queue, introducing measurable queue delays ($\bar{W}_q$).
    """)
