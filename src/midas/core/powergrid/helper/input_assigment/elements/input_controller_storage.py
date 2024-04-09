from midas.core.powergrid.helper.input_assigment.base.input_controller import (
    InputController,
)


class InputControllerStorage(InputController):
    def assigment(self, attrs):
        if "in_service" in attrs and type(attrs["in_service"]) == float:
            attrs["in_service"] = attrs["in_service"] >= 0.5
        return attrs
