import folium
from branca.colormap import LinearColormap
from .config import StudyArea

COLORS = ["#1856a8", "#00cbd1", "#ffe348", "#ff8b2b", "#d72d25"]

def build_map(area: StudyArea, grid, opacity: float, boundary=None):
    fmap = folium.Map(location=[(area.south+area.north)/2, (area.west+area.east)/2], zoom_start=11, tiles="OpenStreetMap", control_scale=True)
    colormap = LinearColormap(COLORS, vmin=0, vmax=1, caption="Illustrative Relative Heat Intensity (0–1)")
    for cell in grid.itertuples():
        folium.Rectangle(
            bounds=[[cell.south, cell.west], [cell.north, cell.east]],
            color=None, fill=True, fill_color=colormap(cell.intensity), fill_opacity=opacity,
            popup=folium.Popup(f"<b>Illustrative Relative Heat Intensity</b><br>{cell.intensity:.3f}<br><small>Synthetic demo value — not temperature.</small>", max_width=250),
        ).add_to(fmap)
    if boundary is not None:
        folium.GeoJson(boundary, name="Verified Dumki boundary", style_function=lambda _: {"fillOpacity": 0, "color": "#6ef1e6", "weight": 2}).add_to(fmap)
    else:
        folium.Rectangle([[area.south, area.west], [area.north, area.east]], color="#69d7e4", weight=2, fill=False, tooltip="Approximate study extent — not an administrative boundary").add_to(fmap)
    colormap.add_to(fmap)
    folium.LayerControl().add_to(fmap)
    return fmap
