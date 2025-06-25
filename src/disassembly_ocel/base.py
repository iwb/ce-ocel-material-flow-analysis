from datetime import datetime
from enum import Enum
from typing import Optional


class Condition(str, Enum):  # the str is intentional!
    pass


class Resource(str, Enum):
    pass


class EventType(str, Enum):
    pass


class CarModel(Enum):
    pass


class Event:
    def __init__(self, id_: str, type_: EventType, start_time: datetime, end_time: datetime = None):
        self._id: str = id_
        self._type: EventType = type_
        self._start_time: datetime = start_time
        self.end_time: datetime = end_time

    @property
    def id(self):
        return self._id

    @property
    def type(self):
        return self._type

    @property
    def start_time(self):
        return self._start_time

    @property
    def end_time(self):
        return self._end_time

    @end_time.setter
    def end_time(self, value):
        if value is not None:
            if value < self.start_time:
                raise ValueError("End time must be larger than start time.")
        self._end_time = value


class Component:
    def __init__(
        self,
        component_type: str,
        condition: Condition,
        number: int = None,
        model: str = None,
        sub_components: list["Component"] = None,
    ):
        self.type: str = str(component_type)

        self.condition: Condition = condition
        self.number: Optional[int] = number
        self.model: Optional[str] = model

        if sub_components is None:
            sub_components = list()
        self.sub_components: list[Component] = sub_components
        self.parent_component: Optional[Component] = None
        self.is_installed_on_parent: bool = False

    @property
    def id(self):
        if self.number is not None:
            return f"{self.type}_{self.number}"
        else:
            raise ValueError("Component number is not set.")

    def install_component(self, component: "Component"):
        if component.is_installed_on_parent:
            raise ValueError(
                f"Component {component.type} is already installed on another parent component: "
                f"{component.parent_component}."
            )

        if component.number is not None and component.number != self.number:
            raise ValueError(
                f"Component number {component.number} does not match parent component number {self.number}."
            )
        self.sub_components.append(component)
        component.parent_component = self
        component.is_installed_on_parent = True
        return

    def pop_component(self, type_: str):
        if self.type == type_:  # The component we are looking for is the current component
            component = self
        elif self.sub_components is None:
            # The component we are looking for is not the current component, and we also have no subcomponents
            # -> raise error
            raise ValueError(f"(Sub-)Component {type_} not found for Component {self.type}.")
        else:  # We have subcomponents that might be the component we are looking for.
            for i, sub_component in enumerate(self.sub_components):
                if sub_component.type == type_:
                    component = self.sub_components.pop(i)
                    break
                elif sub_component.sub_components is not None:
                    try:
                        component = sub_component.pop_component(type_)
                        break
                    except ValueError:
                        pass
            else:  # We did not break out of the for-loop, so the component was not found -> raise error
                raise ValueError(f"Subcomponent {type_} not found for Component {self.type}.")

        component.is_installed_on_parent = False
        return component
