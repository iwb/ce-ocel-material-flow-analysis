from datetime import datetime

import pandas as pd
import pytz


def create_ocel_json(
    events_table: pd.DataFrame, component_objects_table: pd.DataFrame, resource_objects_table: pd.DataFrame
) -> dict[str, list]:
    """
    Create an OCEL JSON log from the given dataframes. This is done by transforming the events_table to OCEL events
    and tge component_objects_table and resource_objects_table to OCEL objects. The object types and event types are
    generated from the unique values in the respective tables and do not need to be supplied.

    :param events_table: A DataFrame containing the events with columns:
        - id: The event ID
        - type: The event type
        - time: The event time as a datetime object
        - input_component_id: The ID of the input component
        - output_components_id: A list of IDs of the output components
        - resource: The ID of the resource (station)
    :param component_objects_table: A DataFrame containing the component objects with columns:
        - id: The object ID
        - type: The object type
        - condition: The condition of the component
        - car_type: The type of the car (if applicable)
        - parent: The ID of the parent component (if applicable)
    :param resource_objects_table: A DataFrame containing the resource objects with columns:
        - id: The object ID
        - type: The object type (e.g., workstation)
    :return: The generate OCEL JSON log as a dictionary with the following structure:
        {
            "objectTypes": [...],  # List of object types
            "eventTypes": [...],   # List of event types
            "objects": [...],      # List of objects
            "events": [...]        # List of events
        }
    """
    datetime_format = "%Y-%m-%dT%H:%M:%SZ"
    default_timestamp = datetime.fromtimestamp(0, tz=pytz.UTC).strftime(datetime_format)

    objects = list()
    for _, row in component_objects_table.iterrows():
        if row["parent"] is None:
            objects.append(
                {
                    "id": row["id"],
                    "type": row["type"],
                    "attributes": [
                        {"name": "condition", "time": default_timestamp, "value": row["condition"]},
                        {"name": "car_type", "time": default_timestamp, "value": row["car_type"]},
                    ],
                }
            )
        else:
            objects.append(
                {
                    "id": row["id"],
                    "type": row["type"],
                    "attributes": [
                        {"name": "condition", "time": default_timestamp, "value": row["condition"]},
                        {"name": "car_type", "time": default_timestamp, "value": row["car_type"]},
                    ],
                    "relationships": [{"objectId": row["parent"], "qualifier": "Parent component"}],
                }
            )

    for _, row in resource_objects_table.iterrows():
        objects.append(
            {
                "id": row["id"],
                "type": row["type"],
            }
        )

    object_type_names = generate_object_type_names(
        component_objects_table["type"].to_list() + resource_objects_table["type"].to_list()
    )
    object_types = list()
    for object_type_name in object_type_names:
        if object_type_name not in resource_objects_table["type"].values:
            object_types.append({"name": object_type_name, "attributes": [{"name": "condition", "type": "string"}]})
        else:
            object_types.append({"name": object_type_name, "attributes": []})

    events = list()
    for _, row in events_table.iterrows():
        events.append(
            {
                "id": row["id"],
                "type": row["type"],
                "time": row["time"].strftime(datetime_format),
                "attributes": [],
                "relationships": [{"objectId": row["input_component_id"], "qualifier": "Input component"}]
                + [
                    {"objectId": output_component_id, "qualifier": "Output component"}
                    for output_component_id in row["output_components_id"]
                ]
                + [{"objectId": row["resource"], "qualifier": "Station"}],
            }
        )

    event_type_names = generate_event_type_names(events_table["type"].to_list())
    event_types = list()
    for event_type_name in event_type_names:
        event_types.append({"name": event_type_name, "attributes": []})

    ocel_json_log = {"objectTypes": object_types, "eventTypes": event_types, "objects": objects, "events": events}
    return ocel_json_log


def generate_object_type_names(object_types_instances: list[str]) -> list[str]:
    return list(set(object_types_instances))


def generate_event_type_names(event_types_instances: list[str]) -> list[str]:
    return list(set(event_types_instances))
