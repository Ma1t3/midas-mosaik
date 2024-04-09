from midas.core.powergrid.helper.input_assigment.base.input_controller import (
    InputController,
)


class InputControllerSwitch(InputController):
    def assigment(self, attrs):
        if "closed" in attrs and type(attrs["closed"]) == float:
            attrs["closed"] = attrs["closed"] >= 0.5
        return attrs
