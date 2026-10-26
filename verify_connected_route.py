
import heapq
import requests
import geopandas as gpd
from shapely.geometry import shape, Point

START = (-118.308881, 34.062100)
END = (-118.309011, 34.068419)

URL = (
    "https://maps.lacity.org/arcgis/rest/services/"
    "Core/Street_Information/MapServer/9/query"
)

params = {
    "where": "UPPER(STNAME) LIKE '%WESTERN%'",
    "outFields": "*",
    "returnGeometry": "true",
    "geometry": "-118.33,34.05,-118.29,34.08",
    "geometryType": "esriGeometryEnvelope",
    "inSR": 4326,
    "outSR": 4326,
    "spatialRel": "esriSpatialRelIntersects",
    "f": "geojson",
}

response = requests.get(URL, params=params, timeout=60)
response.raise_for_status()
features = response.json().get("features", [])

if not features:
    raise RuntimeError("No road features returned.")

rows = []
for f in features:
    p = f.get("properties", {})
    g = f.get("geometry")

    if not g or "WESTERN" not in str(p.get("STNAME", "")).upper():
        continue

    if p.get("INT_ID_FROM") is None or p.get("INT_ID_TO") is None:
        continue

    rows.append({
        "objectid": p.get("OBJECTID"),
        "from_id": str(p["INT_ID_FROM"]),
        "to_id": str(p["INT_ID_TO"]),
        "address_from": p.get("ADRF"),
        "address_to": p.get("ADRT"),
        "geometry": shape(g),
    })

roads = gpd.GeoDataFrame(rows, geometry="geometry", crs="EPSG:4326")

if roads.empty:
    raise RuntimeError("No usable Western Avenue road records.")

roads = roads.to_crs("EPSG:32611").reset_index(drop=True)

start = gpd.GeoSeries(
    [Point(START)], crs="EPSG:4326"
).to_crs("EPSG:32611").iloc[0]

end = gpd.GeoSeries(
    [Point(END)], crs="EPSG:4326"
).to_crs("EPSG:32611").iloc[0]

# Build an undirected graph from official intersection IDs.
# Each edge stores its measured length in projected metres.
edges = []

for i, row in roads.iterrows():
    geom = row.geometry
    if geom is None or geom.is_empty or geom.length <= 0:
        continue

    if geom.geom_type != "LineString":
        print("Skipping non-LineString record:", row["objectid"])
        continue

    edges.append({
        "index": i,
        "from": row["from_id"],
        "to": row["to_id"],
        "length": geom.length,
        "geometry": geom,
        "objectid": row["objectid"],
        "address_from": row["address_from"],
        "address_to": row["address_to"],
    })

def nearest_candidates(point, count=5):
    ranked = sorted(
        edges,
        key=lambda e: e["geometry"].distance(point)
    )
    return ranked[:count]

start_candidates = nearest_candidates(start)
end_candidates = nearest_candidates(end)

print("\nNEAREST START ROAD FEATURES")
for e in start_candidates:
    print(
        f"OBJECTID={e['objectid']} | "
        f"offset={e['geometry'].distance(start):.1f} m | "
        f"length={e['length']:.1f} m | "
        f"nodes={e['from']}->{e['to']}"
    )

print("\nNEAREST END ROAD FEATURES")
for e in end_candidates:
    print(
        f"OBJECTID={e['objectid']} | "
        f"offset={e['geometry'].distance(end):.1f} m | "
        f"length={e['length']:.1f} m | "
        f"nodes={e['from']}->{e['to']}"
    )

def shortest_route(start_edge, end_edge):
    # Adjacency entries: neighbour, weight, road-record ID
    graph = {}

    def add_edge(a, b, weight, objectid):
        graph.setdefault(a, []).append((b, weight, objectid))
        graph.setdefault(b, []).append((a, weight, objectid))

    for e in edges:
        add_edge(e["from"], e["to"], e["length"], e["objectid"])

    source = "__START__"
    target = "__END__"

    # Attach each endpoint to both ends of its nearest road feature.
    # Assumes geometry's first/last coordinates correspond to FROM/TO.
    def attach_virtual_node(node, edge, point):
        geom = edge["geometry"]
        projected_distance = geom.project(point)
        projected_distance = max(
            0.0, min(projected_distance, geom.length)
        )

        add_edge(
            node, edge["from"], projected_distance,
            f"partial-{edge['objectid']}"
        )
        add_edge(
            node, edge["to"], geom.length - projected_distance,
            f"partial-{edge['objectid']}"
        )

    attach_virtual_node(source, start_edge, start)
    attach_virtual_node(target, end_edge, end)

    distances = {source: 0.0}
    previous = {}
    queue = [(0.0, source)]

    while queue:
        distance, node = heapq.heappop(queue)

        if distance != distances.get(node):
            continue
        if node == target:
            break

        for neighbour, weight, objectid in graph.get(node, []):
            new_distance = distance + weight

            if new_distance < distances.get(neighbour, float("inf")):
                distances[neighbour] = new_distance
                previous[neighbour] = (node, objectid)
                heapq.heappush(queue, (new_distance, neighbour))

    if target not in distances:
        return None

    node = target
    path_nodes = [node]
    path_records = []

    while node != source:
        prev_node, objectid = previous[node]
        path_records.append(objectid)
        node = prev_node
        path_nodes.append(node)

    path_nodes.reverse()
    path_records.reverse()

    # Remove virtual partial-edge labels and repeated road IDs.
    record_ids = []
    for rid in path_records:
        if isinstance(rid, str) and rid.startswith("partial-"):
            rid = rid.replace("partial-", "", 1)
        if rid not in record_ids:
            record_ids.append(rid)

    return distances[target], record_ids, path_nodes

results = []

for se in start_candidates:
    for ee in end_candidates:
        result = shortest_route(se, ee)
        if result is None:
            continue

        route_length, record_ids, nodes = result

        offset_total = (
            se["geometry"].distance(start)
            + ee["geometry"].distance(end)
        )

        results.append((
            route_length + offset_total,
            route_length,
            offset_total,
            se,
            ee,
            record_ids,
            nodes,
        ))

print("\nCONNECTED ROUTE CANDIDATES")
print("--------------------------")

if not results:
    print("No connected path found between the candidate features.")
    print("The returned road network may be incomplete.")
else:
    results.sort(key=lambda x: x[0])

    for rank, result in enumerate(results[:5], start=1):
        _, length, offsets, se, ee, record_ids, nodes = result
        print(f"\nCandidate {rank}")
        print("Start OBJECTID:", se["objectid"])
        print("End OBJECTID:", ee["objectid"])
        print("Road path length:", round(length, 1), "m")
        print("Endpoint offsets total:", round(offsets, 1), "m")
        print("Road OBJECTIDs:", record_ids)
        print("Intersection sequence:", nodes)

print("\nNote: this is a network-path diagnostic, not a final boundary.")
print("Check the selected records and endpoint offsets before rebuilding.")
