import map_helper
from main import location_coords
import time

print("Testing map_helper.py functionality...")

# 1. Test Download/Load Graph
start_time = time.time()
print("1. Loading Balikpapan Graph (may take a while first time)...")
try:
    osm_graph = map_helper.load_balikpapan_graph()
    print(f"   Success! Graph loaded in {time.time() - start_time:.2f}s")
    print(f"   Nodes: {len(osm_graph.nodes)}, Edges: {len(osm_graph.edges)}")
except Exception as e:
    print(f"   Failed to load graph: {e}")
    exit(1)

# 2. Test Conversion
print("\n2. Converting to Custom Graph...")
try:
    custom_graph = map_helper.convert_osm_to_custom_graph(osm_graph)
    print(f"   Success! Custom Graph Nodes: {len(custom_graph.nodes)}")
except Exception as e:
    print(f"   Failed to convert graph: {e}")
    exit(1)

# 3. Test Nearest Nodes
print("\n3. Mapping Locations to Nearest Nodes...")
try:
    mapped_nodes = map_helper.get_nearest_nodes(osm_graph, location_coords)
    print("   Mapped Nodes:")
    for name, node_id in mapped_nodes.items():
        print(f"   - {name}: Node ID {node_id}")
except Exception as e:
    print(f"   Failed to map nodes: {e}")
    exit(1)

# 4. Test Routing (Dijkstra)
print("\n4. Testing Routing (Dijkstra) from Depot to SPBU Karang Anyar...")
try:
    depot_node = mapped_nodes["Depot IT Balikpapan"]
    dest_node = mapped_nodes["SPBU Karang Anyar"]
    
    cost, path = custom_graph.dijkstra(depot_node, dest_node)
    
    if cost != float("inf") and path:
        print(f"   Success! Route found.")
        print(f"   Total Travel Time: {cost:.2f} minutes")
        print(f"   Path Length (nodes): {len(path)}")
    else:
        print("   Failed: No route found (infinity cost).")
except Exception as e:
    print(f"   Routing Error: {e}")

print("\nAll tests completed.")
