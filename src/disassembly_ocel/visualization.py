import json
import re

import dash
from dash import Input, Output, State, callback, ctx, html
from dash.exceptions import PreventUpdate
import dash_cytoscape as cyto


def run_cytoscape_process_graph(ocel_json):
    events = ocel_json["events"]
    objects = ocel_json["objects"]
    object_types = ocel_json["objectTypes"]
    event_types = ocel_json["eventTypes"]

    def is_station_type(s):
        # Use a regular expression to check if the string starts with 'ws' followed only by an integer
        pattern = r"^ws\d+$"
        match = re.fullmatch(pattern, s)  # Use fullmatch to ensure the entire string matches the pattern

        return bool(match)

    component_types = [object_type for object_type in object_types if not is_station_type(object_type["name"])]
    station_types = [object_type for object_type in object_types if is_station_type(object_type["name"])]
    event_type_to_station = {}

    # Map event types to stations
    for event in events:
        event_type = event["type"]
        for event_objects in event["relationships"]:
            if event_objects["qualifier"] == "Station":
                event_station = event_objects["objectId"]
                break
        else:
            raise ValueError("Event does not have a station.")
        event_type_to_station[event_type] = event_station

    # Initialize the node elements
    elements = []

    # Create maps to hold object-event counts
    from_objects_count_map = {}
    to_objects_count_map = {}
    stations_count_map = {}

    # Collect counts from relationships in the events
    for event in events:
        event_type = event["type"]
        for event_objects in event["relationships"]:
            if event_objects["qualifier"] == "Input component":
                from_object = event_objects["objectId"]
                from_object_type = [object_["type"] for object_ in objects if object_["id"] == from_object][0]
                if from_object_type not in from_objects_count_map:
                    from_objects_count_map[from_object_type] = {}
                if event_type not in from_objects_count_map[from_object_type]:
                    from_objects_count_map[from_object_type][event_type] = 0
                from_objects_count_map[from_object_type][event_type] += 1
            elif event_objects["qualifier"] == "Output component":
                to_object = event_objects["objectId"]
                to_object_type = [object_["type"] for object_ in objects if object_["id"] == to_object][0]
                if to_object_type not in to_objects_count_map:
                    to_objects_count_map[to_object_type] = {}
                if event_type not in to_objects_count_map[to_object_type]:
                    to_objects_count_map[to_object_type][event_type] = 0
                to_objects_count_map[to_object_type][event_type] += 1
            elif event_objects["qualifier"] == "Station":
                station_object = event_objects["objectId"]
                station_type = [object_["type"] for object_ in objects if object_["id"] == station_object][0]
                if station_type not in stations_count_map:
                    stations_count_map[station_type] = {}
                if event_type not in stations_count_map[station_type]:
                    stations_count_map[station_type][event_type] = 0
                stations_count_map[station_type][event_type] += 1

    # Add object and event nodes to the elements list
    for object_type in component_types:
        if object_type["name"].startswith("a"):
            group = "subassembly"
        elif object_type["name"] == "car":
            group = "product"
        else:
            group = "component"
        elements.append(
            {
                "data": {
                    "id": object_type["name"],
                    "label": object_type["name"],
                },
                "classes": f"object-node group-{group}",
            }
        )

    # create nodes for station objects
    for object_type in station_types:
        elements.append(
            {
                "data": {
                    "id": object_type["name"],
                    "label": object_type["name"],
                },
                "classes": "station-node",
            }
        )

    for event_type in event_types:
        elements.append(
            {
                "data": {
                    "id": event_type["name"],
                    "label": event_type["name"],
                    "group": event_type_to_station[event_type["name"]],
                },
                "classes": 'event-node station-{event_type_to_station[event_type["name"]]}',
            }
        )

    # Create edges using from_objects_count_map and to_objects_count_map
    for from_object, event_types_count in from_objects_count_map.items():
        for event_type, count in event_types_count.items():
            elements.append(
                {
                    "data": {
                        "id": f"{from_object}-{event_type}",
                        "source": from_object,
                        "target": event_type,
                        "weight": count,
                        "arrow": "yes",
                    },
                    "classes": "edge-component-event",
                }
            )

    for to_object, event_types_count in to_objects_count_map.items():
        for event_type, count in event_types_count.items():
            elements.append(
                {
                    "data": {
                        "id": f"{event_type}-{to_object}",
                        "source": event_type,
                        "target": to_object,
                        "weight": count,
                        "arrow": "yes",
                    },
                    "classes": "edge-component-event",
                }
            )

    for station_type, event_types_count in stations_count_map.items():
        for event_type, count in event_types_count.items():
            elements.append(
                {
                    "data": {
                        "id": f"{station_type}-{event_type}",
                        "source": station_type,
                        "target": event_type,
                        "weight": count,
                        "arrow": "no",
                    },
                    "classes": "edge-station-event",
                }
            )

    cyto.load_extra_layouts()
    app = dash.Dash(__name__)

    app.layout = html.Div(
        [
            html.Div(
                children=[
                    cyto.Cytoscape(
                        id="cytoscape",
                        layout={
                            "name": "preset",
                            "directed": True,
                            # 'roots': '[id = "Car"]',  # Root node (change "Car" if needed)
                            # 'spacingFactor': 0.5,
                        },
                        style={"height": "90vh", "width": "100%"},
                        elements=elements,
                        stylesheet=[
                            {
                                "selector": ".object-node",
                                "style": {
                                    "shape": "circle",  # Use roundrectangle to better fit text
                                    "background-color": "white",  # White background inside the node
                                    "border-width": 1,  # Add a border
                                    "border-color": "black",  # Border color
                                    "label": "data(label)",  # Display the label from data
                                    "text-valign": "center",  # Center text vertically
                                    "text-halign": "center",  # Center text horizontally
                                    "padding": "5px",  # Add padding around the text to fit properly
                                    "width": "label",  # Resize the node width to fit the label
                                    "height": "label",  # Resize the node height to fit the label
                                    "font-size": "14px",  # Adjust font size if needed
                                },
                            },
                            {
                                "selector": ".station-node",
                                "style": {
                                    "shape": "rectangle",
                                    "background-color": "white",  # White background inside the node
                                    "border-width": 1,  # Add a border
                                    "border-color": "black",  # Border color
                                    "label": "data(label)",  # Display the label from data
                                    "text-valign": "center",  # Center text vertically
                                    "text-halign": "center",  # Center text horizontally
                                    "padding": "5px",  # Add padding around the text to fit properly
                                    "width": "25px",  # Resize the node width to fit the label
                                    "height": "5px",  # Resize the node height to fit the label
                                    "font-size": "14px",  # Adjust font size if needed
                                },
                            },
                            {
                                "selector": ".event-node",
                                "style": {
                                    "shape": "rectangle",  # Same for event nodes
                                    "background-color": "white",  # White background inside the node
                                    "border-width": 1,  # Add a border
                                    "border-color": "black",  # Border color
                                    "label": "data(label)",  # Display the label from data
                                    "text-valign": "center",  # Center text vertically
                                    "text-halign": "center",  # Center text horizontally
                                    "padding": "5px",  # Add padding around the text to fit properly
                                    "width": "25px",  # Resize the node width to fit the label
                                    "height": "25px",  # Resize the node height to fit the label
                                    "font-size": "14px",  # Adjust font size if needed
                                },
                            },
                            {
                                "selector": ".group-product",
                                "style": {
                                    "background-color": "black",  # White background inside the node
                                    "border-color": "black",  # Border color
                                    "text-outline-color": "white",  # Outline text with black
                                    "color": "white",  # Set text color (black)
                                    "width": "label",  # Resize the node width to fit the label
                                    "height": "label",  # Resize the node height to fit the label
                                },
                            },
                            {
                                "selector": ".group-component",
                                "style": {
                                    "background-color": "black",  # White background inside the node
                                    "border-color": "black",  # Border color
                                    "text-outline-color": "white",  # Outline text with black
                                    "color": "white",  # Set text color (black)
                                    "width": "label",  # Resize the node width to fit the label
                                    "height": "label",  # Resize the node height to fit the label
                                },
                            },
                            {
                                "selector": ".group-subassembly",
                                "style": {
                                    "background-color": "lightgrey",  # White background inside the node
                                    "border-color": "darkgrey",  # Border color
                                    "border-style": "dotted",  # Border color
                                    # dotted border line
                                    "text-outline-color": "black",  # Outline text with black
                                    "color": "black",  # Set text color (black)
                                    "width": "label",  # Resize the node width to fit the label
                                    "height": "label",  # Resize the node height to fit the label
                                },
                            },
                            # Display edge weight as a label with proper styling
                            {
                                "selector": '[arrow = "yes"]',
                                "style": {
                                    "width": 0.5,
                                    "line-color": "black",
                                    "target-arrow-shape": "triangle",
                                    "target-arrow-color": "black",
                                    "arrow-scale": 1,
                                    "label": "data(weight)",
                                    "font-size": "14px",
                                    "background-color": "white",
                                    "text-valign": "center",
                                    "text-halign": "center",
                                    "color": "#000",
                                    "curve-style": "bezier",  # Ensure smooth edges
                                    "text-background-color": "white",  # White background for text
                                    "text-background-opacity": 1,  # Make the background opaque
                                    # 'text-border-color': 'white',  # Black border around the text
                                    # 'text-border-width': 0,  # Border width
                                    "text-border-opacity": 1,
                                    "text-outline-color": "white",  # Simulate padding with outline
                                    "text-outline-width": "3",
                                },
                            },
                            {
                                "selector": '[arrow = "no"]',
                                "style": {
                                    "width": 0.5,
                                    "line-color": "black",
                                    "label": "data(weight)",
                                    "font-size": "14px",
                                    "background-color": "white",
                                    "text-valign": "center",
                                    "text-halign": "center",
                                    "color": "#000",
                                    "curve-style": "bezier",  # Ensure smooth edges
                                    "text-background-color": "white",  # White background for text
                                    "text-background-opacity": 1,  # Make the background opaque
                                    # 'text-border-color': 'white',  # Black border around the text
                                    # 'text-border-width': 0,  # Border width
                                    "text-border-opacity": 1,
                                    "text-outline-color": "white",  # Simulate padding with outline
                                    "text-outline-width": "3",
                                },
                            },
                        ],
                    ),
                ]
            ),
            html.Div(
                children=[
                    html.Div("Download graph:"),
                    html.Button("as jpg", id="btn-get-jpg"),
                    html.Button("as png", id="btn-get-png"),
                    html.Button("as svg", id="btn-get-svg"),
                ],
                style={"textAlign": "center", "marginTop": "20px"},
            ),
            html.Button("Save Positions", id="save-positions-button"),
        ]
    )

    @app.callback(
        Output("save-positions-button", "n_clicks"),
        [Input("save-positions-button", "n_clicks")],
        [State("cytoscape", "elements")],
    )
    def save_node_positions(n_clicks, elements):
        if n_clicks:
            save_positions(elements)
        return n_clicks

    # Reload positions on page load
    @app.callback(Output("cytoscape", "elements"), [Input("cytoscape", "id")])
    def apply_saved_positions_on_reload(_):
        saved_positions = load_positions()
        return merge_positions(elements, saved_positions)

    @callback(
        Output("cytoscape", "generateImage"),
        [
            Input("btn-get-jpg", "n_clicks"),
            Input("btn-get-png", "n_clicks"),
            Input("btn-get-svg", "n_clicks"),
        ],
        prevent_initial_call=True,
    )
    def get_image(tab, get_png_clicks, get_svg_clicks):
        ftype = None
        if ctx.triggered:
            ftype = ctx.triggered_id.split("-")[-1]
        if ftype is None:
            raise PreventUpdate

        return {"type": ftype, "action": "download", "options": {"full": False}, "filename": "graph"}

    app.run(debug=True)
    return elements


def load_positions():
    try:
        with open("node_positions.json", "r") as f:
            return json.load(f)
    except FileNotFoundError:
        return {}


# Function to save positions to file
def save_positions(elements):
    positions = {el["data"]["id"]: el.get("position", {}) for el in elements if "position" in el}
    with open("node_positions.json", "w") as f:
        json.dump(positions, f)
    return


def merge_positions(elements, saved_positions):
    for el in elements:
        node_id = el["data"]["id"]
        if node_id in saved_positions:
            el["position"] = saved_positions[node_id]
    return elements
