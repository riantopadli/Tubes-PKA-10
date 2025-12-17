import streamlit as st
import folium
import map as map_utils
from backend import Graph, location_coords, compute_multi_stop_route

@st.cache_resource(show_spinner=True)
def get_real_time_graph():
    with st.spinner("🔄 Loading Balikpapan road network..."):
        osm_graph = map_utils.load_balikpapan_graph()
        custom_graph = map_utils.convert_osm_to_custom_graph(osm_graph)
        mapped_nodes = map_utils.get_nearest_nodes(osm_graph, location_coords)
    return osm_graph, custom_graph, mapped_nodes

def navigate_real_time_route(start_location, destinations, algorithm="Dijkstra", return_to_start=False):
    osm_graph, custom_graph, mapped_nodes = get_real_time_graph()

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

    return {
        'cost': cost,
        'path': path,
        'readable_path': readable_path,
        'osm_graph': osm_graph,
        'mapped_nodes': mapped_nodes
    }

def navigate_multi_stop_route(start_location, destinations, algorithm="Dijkstra", return_to_start=False):
    return navigate_real_time_route(start_location, destinations, algorithm, return_to_start)

def create_navigation_map(navigation_result, targets=None, show_traffic=False):
    if isinstance(navigation_result, list):
        routes = navigation_result
        osm_graph = routes[0]['osm_graph'] if routes else None
    else:
        routes = [navigation_result]
        osm_graph = navigation_result['osm_graph']

    if not osm_graph:
        osm_graph, _, _ = get_real_time_graph()

    m = map_utils.create_folium_map(osm_graph, locations=location_coords)

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

def get_route_summary(navigation_result):
    return {
        'total_time': f"{navigation_result['cost']:.1f} min",
        'total_stops': len(navigation_result['readable_path']) - 1,
        'route_stops': navigation_result['readable_path'],
        'algorithm_used': 'Real-time Navigation'
    }
