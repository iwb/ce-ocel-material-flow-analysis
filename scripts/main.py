from datetime import datetime, timezone
import json
import os
import pathlib
import shutil
from typing import Optional

import pandas as pd

from disassembly_ocel import (
    CarModel,
    Condition,
    Resource,
    car_factory,
    create_ocel_json,
    disassemble_car,
    run_cytoscape_process_graph,
)


def main():
    # First we create a temporary folder to save the intermediate result for later visualization
    temp_folder = pathlib.Path(__file__).parent.absolute() / "temp"
    _reset_temp_folder(temp_folder)

    # We only consider one car model type, A
    model_a = CarModel["A"]

    # We 120 cars of type A in three different conditions
    arrival_car_models_with_conditions: list[tuple[CarModel, Condition]] = [
        *([(model_a, Condition("Target Disassembly"))] * 70),
        *([(model_a, Condition("Motor Damage"))] * 30),
        *([(model_a, Condition("Damper Damage"))] * 20),
    ]

    # We define initial variables for the disassembly process
    event_number = 1
    event_end_time = datetime(2023, 12, 22, 7, 0, 0).astimezone(timezone.utc)
    events_table: Optional[pd.DataFrame] = None
    component_objects_table: Optional[pd.DataFrame] = None

    # We now loop over all 120 cars and build our objects and event tables for disassembling them
    for car_number, (car_model, car_condition) in enumerate(arrival_car_models_with_conditions, 1):
        # Build a new car object depending on the car model and its condition
        car = car_factory(car_model, car_condition, car_number)

        # The disassembly process starts at the time when the disassembly of the previous car ended.
        # We do not disassemble in parallel
        event_start_time = event_end_time

        # Disassemble the car and get the events and objects as temporary tables
        objects_table_temp, events_table_temp = disassemble_car(car, event_start_time, event_number)
        if events_table is None:
            # If this is the first car, we initialize the tables
            events_table = events_table_temp
            component_objects_table = objects_table_temp
        else:
            # If this is not the first car, we append the temporary tables to the existing ones
            events_table = pd.concat([events_table, events_table_temp], ignore_index=True)
            component_objects_table = pd.concat([component_objects_table, objects_table_temp], ignore_index=True)

        # The event number for the next disassembly starts with the last event number of the current disassembly
        # incremented by one
        event_number = int(events_table["id"].iloc[-1][1:]) + 1
        # Same goes for the end time
        event_end_time = pd.to_datetime(events_table["time"].iloc[-1])

    # We initialize the resources, which are the workstations in our case
    resource_objects_table = pd.DataFrame(
        {
            "id": [resource.value + "_1" for resource in Resource],
            "type": [resource.value for resource in Resource],
        }
    )

    # Transform the dataframes into lists for the objects, the events, the object types, and the event types
    # This returns a dict of the following format:
    # ocel_json_log = {"objectTypes": object_types, "eventTypes": event_types, "objects": objects, "events": events}
    ocel_json_log = create_ocel_json(events_table, component_objects_table, resource_objects_table)

    # Save the OCEL log in case we need it for something else
    _save_ocel(temp_folder, ocel_json_log)

    # Visualize the log
    run_cytoscape_process_graph(ocel_json_log)
    return


def _reset_temp_folder(folder):
    if os.path.exists(folder):
        shutil.rmtree(folder)
    os.makedirs(folder, exist_ok=True)
    return


def _save_ocel(folder: pathlib.Path, ocel_log: dict):
    with open(folder / "ocel.json", "w") as f:
        json.dump(ocel_log, f, indent=2)
    return


if __name__ == "__main__":
    main()
