import copy


def directions(origin, destination, cost, nodes, edges):
    # Extract edge segments and total coordinates of path
    segments = {"type": "FeatureCollection", "features": []}
    coords = [edges[0]["_geometry"]["coordinates"][0]]
    total_distance = 0
    for edge in edges:
        if "length" in edge:
            total_distance += edge["length"]
        feature = {
            "type": "Feature",
            "geometry": edge["_geometry"],
            "properties": {
                k: v
                for k, v in edge.items() if k != "_geometry" and v is not None
            },
        }
        segments["features"].append(feature)
        coords += edge["_geometry"]["coordinates"][1:]

    # Extract steps information
    track = [
        "crossing",
        "curbramps",
        "incline",
        "indoor",
        "length",
        "surface",
    ]

    steps_data = path_to_directions(edges, track)

    route = {
        "geometry": {
            "type": "LineString",
            "coordinates": coords,
        },
        "segments": segments,
        "legs": [steps_data],
        "summary": "",
        "duration": int(cost),
        "distance": total_distance,
        "total_cost": round(cost, 2),
    }

    result = {
        "origin": origin,
        "destination": destination,
        "waypoints": [origin, destination],
        "code": "Ok",
        "routes": [route],
    }

    return result


def path_to_directions(edges, track):
    # TODO: add another list of features on which to always 'split' rather than
    # merge, e.g. multiple edges along one sidewalk should be merged, so way type
    # should be added.
    # Iterate over each edge in the path
    steps = []
    for edge in edges:
        # TODO: remove? Might be slow point. Profile!
        edge = copy.deepcopy(edge)
        geometry = edge.pop("_geometry")
        step = {
            "type": "Feature",
            "geometry": geometry,
            "properties": {},
        }
        # If it"s a `minor` properties, skip it. Being `minor` can either be a
        # category match (e.g., if we have a `link` property type we"d skip it)
        # or a check on numeric attributes (e.g. filter out very short steps).
        if "length" in edge and edge is not None and edge["length"] < 3:
            continue

        for k in track:
            if k in edge and edge[k] is not None:
                step["properties"][k] = edge[k]

        steps.append(step)

    return steps
