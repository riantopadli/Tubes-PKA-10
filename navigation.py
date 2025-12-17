import streamlit as st
import folium
import map as map_utils
from typing import List, Tuple
from backend import Graph, location_coords, compute_multi_stop_route, haversine_km

def calculate_route_distances(osm_graph, path: List[str]) -> Tuple[float, List[float]]:
    """Calculate total distance and segment distances for a route path."""
    if len(path) < 2:
        return 0.0, []

    import networkx as nx

    total_distance = 0.0
    segment_distances = []

    for i in range(len(path) - 1):
        from_node_id = int(path[i])
        to_node_id = int(path[i + 1])

        try:
            distance_m = nx.shortest_path_length(osm_graph, from_node_id, to_node_id, weight='length')
            distance_km = distance_m / 1000.0
            segment_distances.append(distance_km)
            total_distance += distance_km
        except (nx.NetworkXNoPath, nx.NodeNotFound):
            if osm_graph.has_node(from_node_id) and osm_graph.has_node(to_node_id):
                from_coord = (osm_graph.nodes[from_node_id]['y'], osm_graph.nodes[from_node_id]['x'])
                to_coord = (osm_graph.nodes[to_node_id]['y'], osm_graph.nodes[to_node_id]['x'])
                distance_km = haversine_km(from_coord, to_coord)
                segment_distances.append(distance_km)
                total_distance += distance_km
            else:
                segment_distances.append(0.0)

    return total_distance, segment_distances

@st.cache_resource(show_spinner=True)
def get_real_time_graph(vehicle_type="car"):
    with st.spinner("🔄 Loading Balikpapan road network..."):
        osm_graph = map_utils.load_balikpapan_graph(vehicle_type=vehicle_type)
        custom_graph = map_utils.convert_osm_to_custom_graph(osm_graph)
        mapped_nodes = map_utils.get_nearest_nodes(osm_graph, location_coords)
    return osm_graph, custom_graph, mapped_nodes

def navigate_real_time_route(start_location, destinations, algorithm="Dijkstra", return_to_start=False, vehicle_type="car"):
    osm_graph, custom_graph, mapped_nodes = get_real_time_graph(vehicle_type=vehicle_type)

    if start_location not in mapped_nodes:
        raise ValueError(f"Start location '{start_location}' not found")
    if not destinations:
        raise ValueError("At least one destination required")

    start_node = mapped_nodes[start_location]
    dest_nodes = [mapped_nodes[dest] for dest in destinations if dest in mapped_nodes]

    cost, path = compute_multi_stop_route(
        custom_graph, start_node, dest_nodes, algorithm, return_to_start
    )

    if cost == float("inf") or not path:
        raise ValueError("Cannot find connecting route")

    id_to_name = {v: k for k, v in mapped_nodes.items()}
    readable_path = [id_to_name.get(node_id) for node_id in path if node_id in id_to_name]

    total_distance, segment_distances = calculate_route_distances(osm_graph, path)

    return {
        'cost': cost,
        'path': path,
        'readable_path': readable_path,
        'osm_graph': osm_graph,
        'mapped_nodes': mapped_nodes,
        'total_distance': total_distance,
        'segment_distances': segment_distances
    }

def navigate_multi_stop_route(start_location, destinations, algorithm="Dijkstra", return_to_start=False, vehicle_type="car"):
    return navigate_real_time_route(start_location, destinations, algorithm, return_to_start, vehicle_type=vehicle_type)

def create_navigation_map(navigation_result, targets=None, show_traffic=False):
    if isinstance(navigation_result, list):
        routes = navigation_result
        osm_graph = routes[0]['osm_graph'] if routes else None
    else:
        routes = [navigation_result]
        osm_graph = navigation_result['osm_graph']

    if not osm_graph:
        osm_graph, _, _ = get_real_time_graph()

    filtered_locations = {name: coord for name, coord in location_coords.items() if "Depot" in name or "SPBU" in name}
    m = map_utils.create_folium_map(osm_graph, locations=filtered_locations, targets=targets)

    route_colors = ["#E31B23", "#005DAA", "#5CB85C", "#FF8C00", "#8A2BE2", "#DC143C"]
    all_coords = []

    for route_idx in reversed(range(len(routes))):
        route_data = routes[route_idx]
        path = route_data['path']
        readable_path = route_data['readable_path']
        cost = route_data['cost']

        key_locations = [readable_path[0]] if readable_path else []
        if targets and readable_path:
            key_locations.extend([loc for loc in readable_path[1:-1] if loc in targets])
        if len(readable_path) > 1:
            key_locations.append(readable_path[-1])

        route_tooltip = f"Route {route_idx+1}: {' → '.join(key_locations)}\nTime: {cost:.1f} min"

        start_location = readable_path[0] if readable_path else None

        if path and len(path) > 1 and start_location:
            route_coords = []
            if start_location in location_coords:
                lon, lat = location_coords[start_location]
                route_coords.append([lat, lon])

            for node_id in path[1:]:
                try:
                    nid = int(node_id)
                    if osm_graph.has_node(nid):
                        node_data = osm_graph.nodes[nid]
                        lat, lon = node_data['y'], node_data['x']
                        if -90 <= lat <= 90 and -180 <= lon <= 180:
                            route_coords.append([lat, lon])
                except (ValueError, KeyError):
                    continue

            if len(route_coords) > 1:
                color = route_colors[route_idx % len(route_colors)]
                folium.PolyLine(
                    route_coords, color=color, weight=6, opacity=0.85,
                    tooltip=route_tooltip, popup=f"Route {route_idx+1}: Fuel Distribution"
                ).add_to(m)
                all_coords.extend(route_coords)

    if all_coords:
        for loc_coords in location_coords.values():
            all_coords.append([loc_coords[1], loc_coords[0]])
        try:
            m.fit_bounds(all_coords)
        except:
            pass

    return m

def generate_route_statistics(navigation_result, targets=None):
    """Generate detailed route statistics table data."""
    readable_path = navigation_result['readable_path']
    path = navigation_result['path']
    total_distance = navigation_result.get('total_distance', 0.0)
    segment_distances = navigation_result.get('segment_distances', [])
    travel_time_only = navigation_result['cost']

    LOADING_TIME_MIN = 15
    FUEL_CONSUMPTION_L_PER_100KM = 25
    AVG_SPEED_KMH = 30.0

    id_to_name = {v: k for k, v in navigation_result['mapped_nodes'].items()}

    cumulative_distances = []
    current_distance = 0.0

    for i, node_id in enumerate(path):
        location_name = id_to_name.get(node_id)
        if location_name and location_name in readable_path:
            cumulative_distances.append(current_distance)
        if i < len(segment_distances):
            current_distance += segment_distances[i]

    while len(cumulative_distances) < len(readable_path):
        cumulative_distances.append(total_distance)

    table_data = []
    cumulative_time = 0.0

    for i, location in enumerate(readable_path):
        segment_distance = 0.0 if i == 0 else cumulative_distances[i] - cumulative_distances[i-1]
        segment_time = (segment_distance / AVG_SPEED_KMH) * 60 if segment_distance > 0 else 0.0

        row = {
            'Urutan': i + 1,
            'Lokasi': location,
            'Jarak_dari_Sebelumnya_km': segment_distance,
            'Waktu_Tempuh_min': segment_time,
            'Aktivitas': '',
            'Estimasi_Tiba': ''
        }

        if i == 0:
            row['Aktivitas'] = 'Berangkat dari Depot'
        elif location in (targets or []):
            row['Aktivitas'] = 'Bongkar BBM'
            row['Waktu_Tempuh_min'] += LOADING_TIME_MIN
        elif i == len(readable_path) - 1 and location == readable_path[0]:
            row['Aktivitas'] = 'Tiba kembali di Depot'
        elif i == len(readable_path) - 1:
            row['Aktivitas'] = 'Tiba di Tujuan Akhir'
        else:
            row['Aktivitas'] = 'Perjalanan'

        cumulative_time += row['Waktu_Tempuh_min']
        row['Estimasi_Tiba'] = f"{cumulative_time:.1f}"

        table_data.append(row)

    num_stops = len([t for t in targets or []])
    total_loading_time = LOADING_TIME_MIN * num_stops
    total_operational_time = travel_time_only + total_loading_time

    estimated_fuel_consumption = (total_distance / 100) * FUEL_CONSUMPTION_L_PER_100KM

    summary = {
        'total_distance_km': total_distance,
        'total_time_min': total_operational_time,
        'estimated_fuel_liters': estimated_fuel_consumption,
        'number_of_stops': num_stops,
        'table_data': table_data
    }

    return summary

def get_route_summary(navigation_result):
    return {
        'total_time': f"{navigation_result['cost']:.1f} min",
        'total_stops': len(navigation_result['readable_path']) - 1,
        'route_stops': navigation_result['readable_path'],
        'algorithm_used': 'Real-time Navigation'
    }
