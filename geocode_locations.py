import osmnx as ox
from backend import location_coords
import json

# Dictionary untuk menyimpan koordinat baru
new_coords = {}

for name, (lon, lat) in location_coords.items():
    try:
        # Coba geocode dengan nama lokasi + Balikpapan
        query = f"{name}, Balikpapan, Indonesia"
        result = ox.geocode(query)
        if result:
            new_lat, new_lon = result  # osmnx returns (lat, lon)
            new_coords[name] = (new_lon, new_lat)
            print(f"{name}: {lon:.6f}, {lat:.6f} -> {new_lon:.6f}, {new_lat:.6f}")
        else:
            print(f"No result for {name}")
            new_coords[name] = (lon, lat)  # Keep old if no result
    except Exception as e:
        print(f"Error geocoding {name}: {e}")
        new_coords[name] = (lon, lat)

# Save to file
with open('new_coords.json', 'w') as f:
    json.dump(new_coords, f, indent=2)

print("Geocoding completed. Check new_coords.json")
