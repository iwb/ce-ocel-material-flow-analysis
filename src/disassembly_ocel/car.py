import copy
from datetime import datetime, timedelta
import enum

import pandas as pd

from disassembly_ocel import base
from disassembly_ocel.base import Component, Event


class Condition(base.Condition):
    """
    Represents the condition of the car arriving for disassembly.
    """

    TD = "Target Disassembly"
    DD = "Damper Damage"
    MD = "Motor Damage"


class Resource(base.Resource):
    """
    Represents the resources (workstations) used in the disassembly process for the disassembly steps.
    """

    S1 = "ws1"
    S2 = "ws2"
    S3 = "ws3"
    S4 = "ws4"
    S5 = "ws5"


class EventType(base.EventType):
    """
    Represents the different types of steps that can occur during the disassembly process.
    """

    SPOIL_CAR = "d1"
    BODY_CHASSIS_SEPARATION = "d2"
    SPLIT_CHASSIS = "d3"
    BATTERY_FROM_CHASSIS = "d7"
    TYRES_FROM_REAR_CHASSIS = "d8"
    MOTOR_MOTOR_HOUSING_BASE_PLATE_FROM_REAR_CHASSIS = "d9"
    LARGE_DAMPER_ASSEMBLY_FROM_BASE_PLATE = "d10"
    LARGE_DAMPERS_FROM_ASSEMBLY = "d11"
    TYRES_FROM_FRONT_CHASSIS = "d4"
    SMALL_DAMPER_ASSEMBLY_FROM_FRONT_CHASSIS = "d5"
    SMALL_DAMPERS_FROM_ASSEMBLY = "d6"


class CarModel(base.CarModel):
    """
    Represents the different models of cars that can be disassembled.
    """

    A = enum.auto()


"""
This map defines the duration of each disassembly step for each car model.
"""
car_model_to_duration_map = {
    CarModel.A: {
        EventType.SPOIL_CAR: 180,
        EventType.BODY_CHASSIS_SEPARATION: 120,
        EventType.SPLIT_CHASSIS: 120,
        EventType.BATTERY_FROM_CHASSIS: 70,
        EventType.TYRES_FROM_REAR_CHASSIS: 30,
        EventType.MOTOR_MOTOR_HOUSING_BASE_PLATE_FROM_REAR_CHASSIS: 30,
        EventType.LARGE_DAMPER_ASSEMBLY_FROM_BASE_PLATE: 30,
        EventType.LARGE_DAMPERS_FROM_ASSEMBLY: 30,
        EventType.TYRES_FROM_FRONT_CHASSIS: 30,
        EventType.SMALL_DAMPER_ASSEMBLY_FROM_FRONT_CHASSIS: 30,
        EventType.SMALL_DAMPERS_FROM_ASSEMBLY: 30,
    },
}


def car_factory(car_model: CarModel, condition: Condition, car_number: int) -> Component:
    """
    This function creates a car component with its subcomponents based on the provided model and condition.
    Create the components for the car and put them in relation to one another using the .install_component methods.
    The car component is the root component, and all other components are installed on it or its subcomponents.

    :param car_model: The model of the car, e.g., CarModel.A
    :param condition: Condition of the car, e.g., Target Disassembly (TD), Damper Damage (DD), or Motor Damage (MD)
    :param car_number: The number of the car, should be unique
    :return: Component representing the car with its installed subcomponents depending on the condition
    """
    # At the beginning, all conditions have the same main components
    car = Component("car", condition, car_number, model=car_model.name)
    spoiler = Component("sp", condition, car_number)
    body = Component("bo", condition, car_number)
    chassis = Component("a2", condition, car_number)
    car.install_component(spoiler)
    car.install_component(body)
    car.install_component(chassis)

    front_chassis = Component("a3", condition, car_number)
    rear_chassis = Component("a6", condition, car_number)
    chassis.install_component(front_chassis)
    chassis.install_component(rear_chassis)

    front_tyres = Component("ft", condition, car_number)

    front_damper_assembly = Component("a5", condition, car_number)
    front_dampers = Component("sd", condition, car_number)
    front_damper_damaged = Component("dd", condition, car_number)

    rear_tyres = Component("rt", condition, car_number)

    motor = Component("mo", condition, car_number)
    motor_damaged = Component("md", condition, car_number)
    motor_housing = Component("ho", condition, car_number)
    base_plate = Component("a10", condition, car_number)
    rear_damper_assembly = Component("a11", condition, car_number)
    rear_dampers = Component("ld", condition, car_number)

    battery = Component("bt", condition, car_number)

    # The target disassembly (TD) condition has all components installed
    if condition == Condition.TD:
        rear_chassis.install_component(battery)

        front_chassis.install_component(front_tyres)
        front_chassis.install_component(front_damper_assembly)
        front_damper_assembly.install_component(front_dampers)

        rear_chassis.install_component(rear_tyres)
        rear_chassis.install_component(motor)
        rear_chassis.install_component(motor_housing)
        rear_chassis.install_component(base_plate)
        base_plate.install_component(rear_damper_assembly)
        rear_damper_assembly.install_component(rear_dampers)

    elif condition == Condition.DD or condition == Condition.MD:
        rear_chassis.install_component(rear_tyres)
        if condition == Condition.DD:
            # If the car has damper damage (DD), we install the damaged front damper assembly
            front_chassis.install_component(front_tyres)
            front_chassis.install_component(front_damper_assembly)
            front_damper_assembly.install_component(front_damper_damaged)
        if condition == Condition.MD:
            # If the car has motor damage (MD), we install the damaged motor
            rear_chassis.install_component(motor_housing)
            rear_chassis.install_component(motor_damaged)
    else:
        raise ValueError(f"Invalid condition {condition}.")

    return car


def disassemble_car(car: Component, start_time: datetime, first_event_number: int) -> (pd.DataFrame, pd.DataFrame):
    """
    Disassembles a car and returns the objects and events as pandas DataFrames.

    :param car: The car component to disassemble
    :param start_time: The start time of the disassembly process
    :param first_event_number: The event number to start with for the disassembly events
    :return: Two pandas DataFrames: one for the objects and one for the events
    """
    if not car.type == "car":
        raise ValueError(f"Component must be of type Car, was {car.type}.")

    # Define lists to store the events and objects
    event_ids = list()
    event_types = list()
    event_times = list()
    event_input_component = list()
    event_output_components = list()
    event_resource = list()

    object_ids = list()
    object_types = list()
    object_parents = list()
    object_condition = list()
    object_car_type = list()
    car_type = car.model

    # Get the durations for the disassembly steps based on the car model
    durations = car_model_to_duration_map[CarModel[car.model]]

    def disassembly_step(
        event_number: int,
        event_type: EventType,
        start_time: datetime,
        main_component: Component,
        components_to_pop: list[str],
        resource: Resource,
        main_component_new_type: str = None,
    ):
        """
        This function performs a disassembly step, popping components from the main component and creating an event
        for it.

        :param event_number: The number of the event, used to create a unique ID for the event
        :param event_type: The type of the event, e.g., EventType.SPOIL_CAR
        :param start_time: The start time of the event, when the disassembly step starts
        :param main_component: The main component that is being disassembled, e.g., the car
        :param components_to_pop: A list of component types to pop from the main component, e.g., ["sp", "a2"]
        :param resource: The resource (workstation) where the disassembly step takes place, e.g., Resource.S1
        :param main_component_new_type: If the main component's type should change after the disassembly step,
            provide the new type here
        :return: A tuple containing the main component and a list of popped components, and the event created for
            this disassembly step
        """
        event = Event(id_=f"e{event_number}", type_=event_type, start_time=start_time)
        event.end_time = event.start_time + timedelta(minutes=durations[event_type])
        popped_components = list()
        for component_to_pop in components_to_pop:
            popped_components.append(main_component.pop_component(component_to_pop))
        for component in popped_components:
            # Components are only added to the list of objects if they are actually disassembled
            append_to_objects_list(component)

        main_component_original_id = copy.copy(main_component.id)
        if main_component_new_type is not None:
            main_component.type = main_component_new_type
            append_to_objects_list(main_component, parent_id=main_component_original_id)
            popped_components.append(main_component)
        append_to_events_list(event, main_component_original_id, popped_components, resource)
        return (main_component, popped_components), event

    def append_to_events_list(
        event: Event, main_component_original_id: str, output_objects: list[Component], resource
    ):
        event_ids.append(event.id)
        event_types.append(event.type.value)
        event_input_component.append(main_component_original_id)
        event_output_components.append([object_.id for object_ in output_objects])
        event_times.append(event.end_time)
        # ToDo: Resource instances are currently hardcoded and limited to one instance per resource:
        event_resource.append(resource.value + "_1")
        return

    def append_to_objects_list(component: Component, parent_id: str = None):
        if parent_id is not None:
            pass
        elif component.parent_component is not None:
            parent_id = component.parent_component.id
        else:
            parent_id = None

        if component.type.startswith("Station"):
            raise ValueError(f"Component type cannot start with 'Station', but was: {component.type}")

        object_ids.append(component.id)
        object_types.append(component.type)
        object_parents.append(parent_id)
        object_condition.append(component.condition.name)
        object_car_type.append(car_type)
        return

    event_number = first_event_number
    append_to_objects_list(car)

    output_objects, event = disassembly_step(
        event_number, EventType.SPOIL_CAR, start_time, car, ["sp"], Resource.S1, main_component_new_type="a1"
    )
    event_number += 1
    car_wo_spoiler, _ = output_objects

    output_objects, event = disassembly_step(
        event_number, EventType.BODY_CHASSIS_SEPARATION, event.end_time, car_wo_spoiler, ["a2", "bo"], Resource.S1
    )
    event_number += 1
    _, (chassis, body) = output_objects

    if car.condition == Condition.TD:
        output_objects, event = disassembly_step(
            event_number, EventType.SPLIT_CHASSIS, start_time, chassis, ["a3", "a6"], Resource.S2
        )
        event_number += 1
        _, (
            front_chassis,
            rear_chassis,
        ) = output_objects

        output_objects, event = disassembly_step(
            event_number, EventType.TYRES_FROM_FRONT_CHASSIS, event.end_time, front_chassis, ["ft"], Resource.S4, "a4"
        )
        event_number += 1
        _, _ = output_objects

        output_objects, event = disassembly_step(
            event_number,
            EventType.SMALL_DAMPER_ASSEMBLY_FROM_FRONT_CHASSIS,
            event.end_time,
            front_chassis,
            ["a5"],
            Resource.S4,
        )
        event_number += 1
        _, (front_damper_assembly,) = output_objects

        output_objects, event = disassembly_step(
            event_number,
            EventType.SMALL_DAMPERS_FROM_ASSEMBLY,
            event.end_time,
            front_damper_assembly,
            ["sd"],
            Resource.S4,
        )
        event_number += 1
        _, _ = output_objects

        output_objects, event = disassembly_step(
            event_number, EventType.BATTERY_FROM_CHASSIS, event.end_time, rear_chassis, ["bt"], Resource.S3, "a7"
        )
        event_number += 1
        rear_chassis_wo_battery, _ = output_objects

        output_objects, event = disassembly_step(
            event_number,
            EventType.TYRES_FROM_REAR_CHASSIS,
            event.end_time,
            rear_chassis_wo_battery,
            ["rt"],
            Resource.S3,
            "a9",
        )
        event_number += 1
        rear_chassis_wo_tyres, _ = output_objects

        output_objects, event = disassembly_step(
            event_number,
            EventType.MOTOR_MOTOR_HOUSING_BASE_PLATE_FROM_REAR_CHASSIS,
            event.end_time,
            rear_chassis_wo_tyres,
            ["mo", "ho", "a10"],
            Resource.S5,
        )
        event_number += 1
        _, (motor, motor_housing, base_plate) = output_objects

        output_objects, event = disassembly_step(
            event_number,
            EventType.LARGE_DAMPER_ASSEMBLY_FROM_BASE_PLATE,
            event.end_time,
            base_plate,
            ["a11"],
            Resource.S5,
        )
        event_number += 1
        _, (rear_damper_assembly,) = output_objects

        output_objects, event = disassembly_step(
            event_number,
            EventType.LARGE_DAMPERS_FROM_ASSEMBLY,
            event.end_time,
            rear_damper_assembly,
            ["ld"],
            Resource.S5,
        )
        event_number += 1
        _, _ = output_objects

    elif car.condition == Condition.DD:
        output_objects, event = disassembly_step(
            event_number, EventType.TYRES_FROM_REAR_CHASSIS, event.end_time, chassis, ["rt"], Resource.S3, "a8"
        )
        event_number += 1
        chassis_wo_tyres, _ = output_objects

        output_objects, event = disassembly_step(
            event_number,
            EventType.SMALL_DAMPER_ASSEMBLY_FROM_FRONT_CHASSIS,
            event.end_time,
            chassis_wo_tyres,
            ["dd"],
            Resource.S4,
        )
        event_number += 1
        _, _ = output_objects

    elif car.condition == Condition.MD:
        output_objects, event = disassembly_step(
            event_number, EventType.TYRES_FROM_REAR_CHASSIS, event.end_time, chassis, ["rt"], Resource.S3, "a8"
        )
        event_number += 1
        chassis_wo_tyres, _ = output_objects

        output_objects, event = disassembly_step(
            event_number,
            EventType.MOTOR_MOTOR_HOUSING_BASE_PLATE_FROM_REAR_CHASSIS,
            event.end_time,
            chassis_wo_tyres,
            ["md", "ho"],
            Resource.S5,
        )
        event_number += 1
        _, _ = output_objects

    else:
        raise ValueError(f"Invalid condition {car.condition}.")

    objects_table = pd.DataFrame(
        {
            "id": object_ids,
            "type": object_types,
            "parent": object_parents,
            "condition": object_condition,
            "car_type": object_car_type,
        }
    )
    events_table = pd.DataFrame(
        {
            "id": event_ids,
            "type": event_types,
            "time": event_times,
            "input_component_id": event_input_component,
            "output_components_id": event_output_components,
            "resource": event_resource,
        }
    )

    return objects_table, events_table
