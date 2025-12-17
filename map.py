import osmnx as ox
import networkx as nx
import folium
from backend import Graph, location_coords

def load_balikpapan_graph(place_name="Balikpapan, Indonesia", vehicle_type="car"):
    """Load Balikpapan road network from OpenStreetMap, filtered based on vehicle type."""
    if vehicle_type.lower() == "truck":
        network_type = "drive"
        custom_filter = (
            '["highway"~"motorway|trunk|primary|secondary"]["area"!~"yes"]["access"!~"private"]["highway"!~"residential|living_street|unclassified|service"]'
        )
    else:
        network_type = "drive"
        custom_filter = (
            '["highway"]["area"!~"yes"]["access"!~"private"]["highway"!~"abandoned|bridleway|bus_guideway|construction|corridor|cycleway|elevator|footway|path|pedestrian|planned|platform|proposed|raceway|steps|track"]'
            '["highway"!~"abandoned|bridleway|bus_guideway|construction|corridor|cycleway|elevator|footway|path|pedestrian|planned|platform|proposed|raceway|steps|track"]'
        )

    G = ox.graph_from_place(
        place_name,
        network_type=network_type,
        simplify=False,  # More detailed but smaller graph
        custom_filter=custom_filter
    )

    G = ox.add_edge_speeds(G)
    G = ox.add_edge_travel_times(G)

    return G

def convert_osm_to_custom_graph(osm_graph):
    """Convert OSMnx graph to custom Graph format."""
    custom_graph = Graph()

    for node_id, data in osm_graph.nodes(data=True):
        custom_graph.add_node(str(node_id), (data['x'], data['y']))

    for u, v, data in osm_graph.edges(data=True):
        weight = 0.0
        if 'travel_time' in data:
            weight = data['travel_time'] / 60.0
        elif 'length' in data:
            length_km = data['length'] / 1000.0
            speed_kmph = data.get('speed_kph', 30.0)
            if isinstance(speed_kmph, list):
                speed_kmph = float(speed_kmph[0])
            weight = (length_km / speed_kmph) * 60.0

        weight = max(weight, 0.01)

        u_str, v_str = str(u), str(v)

        if u_str not in custom_graph.edges:
            custom_graph.edges[u_str] = []
        custom_graph.edges[u_str].append((v_str, weight))

        if v_str not in custom_graph.edges:
            custom_graph.edges[v_str] = []

    return custom_graph

def get_nearest_nodes(osm_graph, locations):
    """Find nearest road nodes for each location. Returns dict: {'Location': 'Node_ID'}"""
    mapped_nodes = {}
    for name, (lon, lat) in locations.items():
        nearest_node = ox.distance.nearest_nodes(osm_graph, lon, lat)
        mapped_nodes[name] = str(nearest_node)
    return mapped_nodes

def create_folium_map(osm_graph, path_nodes=None, locations=None):
    """Create Folium map with markers and route visualization."""

    center_lat = -1.25
    center_lon = 116.83

    m = folium.Map(location=[center_lat, center_lon], zoom_start=13)

    if locations:
        for name, (lon, lat) in locations.items():
            color = "green" if "Depot" in name else "blue"
            icon = folium.Icon(color=color, icon="gas-pump", prefix="fa")
            folium.Marker(
                location=[lat, lon],
                popup=name,
                tooltip=name,
                icon=icon
            ).add_to(m)

    if path_nodes and len(path_nodes) > 1:
        route_coords = []
        for node_id in path_nodes:
            nid = int(node_id)
            if osm_graph.has_node(nid):
                node_data = osm_graph.nodes[nid]
                route_coords.append((node_data['y'], node_data['x']))

        folium.PolyLine(
            route_coords,
            color="red",
            weight=5,
            opacity=0.8,
            tooltip="Rute Terpilih"
        ).add_to(m)

        if route_coords:
            m.fit_bounds(route_coords)

    return m
