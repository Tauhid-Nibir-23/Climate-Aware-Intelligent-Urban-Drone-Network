"""
Interactive Folium Map Builder for Dumki and PSTU Campus Drone Network.
Provides realistic OpenStreetMap and Satellite tile views with custom markers and flight corridors.
"""
from __future__ import annotations
import folium
from folium import plugins
from src.network import DumkiNetwork

def build_dumki_folium_map(
    network: DumkiNetwork,
    focus_mode: str = "PSTU Campus View",
    show_flight_corridors: bool = True
) -> folium.Map:
    """
    Creates an interactive Folium Leaflet map with real geographic tiles.
    """
    depot_id = network.get_depot_id()
    depot_info = network.depots[depot_id]
    depot_lat, depot_lon = depot_info["lat"], depot_info["lon"]

    # Choose center and zoom based on focus
    if focus_mode == "PSTU Campus View":
        center = [depot_lat, depot_lon]
        zoom_start = 15
    else:  # Full Dumki Regional View
        center = [22.4550, 90.3800]
        zoom_start = 13

    # Base Map with multiple switchable tile layers
    m = folium.Map(
        location=center,
        zoom_start=zoom_start,
        tiles=None,
        control_scale=True
    )

    # Add Clean Free Tile Layers (No API key needed)
    folium.TileLayer(
        tiles="OpenStreetMap",
        name="🗺️ Street & Building View (OpenStreetMap)",
        overlay=False,
        control=True
    ).add_to(m)

    folium.TileLayer(
        tiles="https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}",
        attr="Esri World Imagery",
        name="🛰️ High-Res Satellite View (Esri)",
        overlay=False,
        control=True
    ).add_to(m)

    folium.TileLayer(
        tiles="https://{s}.tile.opentopomap.org/{z}/{x}/{y}.png",
        attr="OpenTopoMap",
        name="🏔️ Topographic Terrain View",
        overlay=False,
        control=True
    ).add_to(m)

    # 1. Add Central Depot (PSTU Command Center)
    depot_html = f"""
    <div style="font-family: Arial, sans-serif; width: 230px; padding: 6px;">
        <h4 style="margin: 0 0 6px 0; color: #d9381e;">🚁 {depot_info['name']}</h4>
        <p style="margin: 0; font-size: 12px; color: #444;"><b>Role:</b> Central Base & Battery Dock</p>
        <p style="margin: 2px 0; font-size: 12px; color: #444;"><b>Charging Bays:</b> {depot_info['charging_bays']} slots</p>
        <p style="margin: 2px 0; font-size: 12px; color: #444;"><b>Coordinates:</b> {depot_lat:.4f}° N, {depot_lon:.4f}° E</p>
        <hr style="margin: 6px 0; border: none; border-top: 1px solid #ddd;">
        <span style="background: #e53e3e; color: white; padding: 2px 6px; border-radius: 4px; font-size: 11px;">Primary Drone Depot</span>
    </div>
    """
    
    # Pulse circle around depot
    folium.Circle(
        location=[depot_lat, depot_lon],
        radius=300,
        color="#e53e3e",
        weight=2,
        fill=True,
        fill_color="#e53e3e",
        fill_opacity=0.15,
        tooltip="PSTU Campus Drone Operational Radius"
    ).add_to(m)

    folium.Marker(
        location=[depot_lat, depot_lon],
        popup=folium.Popup(depot_html, max_width=300),
        tooltip=f"★ Central Hub: {depot_info['name']}",
        icon=folium.Icon(color="red", icon="plane", prefix="fa")
    ).add_to(m)

    # 2. Add Delivery Nodes
    corridor_group = folium.FeatureGroup(name="✈️ Air Corridors (Direct Flight Paths)", show=show_flight_corridors)

    for node_id, node in network.delivery_nodes.items():
        dist_km = network.get_distance_km(depot_id, node_id)
        est_time_min = round((dist_km * 1000.0 / 12.0 + 60.0) / 60.0, 1)
        is_campus = "PSTU" in node.get("zone", "")

        node_popup = f"""
        <div style="font-family: Arial, sans-serif; width: 220px; padding: 4px;">
            <h4 style="margin: 0 0 4px 0; color: #1a365d;">📍 {node['name']}</h4>
            <p style="margin: 0; font-size: 12px;"><b>Zone:</b> {node.get('zone', 'Dumki')}</p>
            <p style="margin: 2px 0; font-size: 12px;"><b>Distance from PSTU:</b> <b>{dist_km:.2f} km</b></p>
            <p style="margin: 2px 0; font-size: 12px;"><b>Est. Flight Time:</b> ~{est_time_min} mins</p>
            <p style="margin: 2px 0; font-size: 12px;"><b>Type:</b> {node['type']}</p>
        </div>
        """

        # Custom icon colors based on zone/type
        marker_color = node.get("color", "blue")
        icon_name = node.get("icon", "info-sign")

        folium.Marker(
            location=[node["lat"], node["lon"]],
            popup=folium.Popup(node_popup, max_width=280),
            tooltip=f"{'🎓 ' if is_campus else '🏥 '}{node['name']} ({dist_km:.2f} km)",
            icon=folium.Icon(color=marker_color, icon=icon_name, prefix="fa")
        ).add_to(m)

        # Draw flight corridor polyline
        line_color = "#3182ce" if is_campus else "#dd6b20"
        line_weight = 3 if is_campus else 2
        line_dash = "4, 6"

        corridor_popup = f"Corridor PSTU ➔ {node['name']}<br>Distance: {dist_km:.2f} km | Cruising: ~{est_time_min} min"

        folium.PolyLine(
            locations=[[depot_lat, depot_lon], [node["lat"], node["lon"]]],
            color=line_color,
            weight=line_weight,
            opacity=0.85,
            dash_array=line_dash,
            tooltip=corridor_popup
        ).add_to(corridor_group)

    corridor_group.add_to(m)

    # Add Layer Control and Fullscreen
    folium.LayerControl(position="topright", collapsed=False).add_to(m)
    plugins.Fullscreen(position="topleft").add_to(m)

    return m
