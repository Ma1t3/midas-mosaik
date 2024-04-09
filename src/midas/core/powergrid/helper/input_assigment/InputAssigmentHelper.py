from midas.core.powergrid.helper.input_assigment.elements.input_controller_switch import (
    InputControllerSwitch,
)
from midas.core.powergrid.helper.input_assigment.elements.input_controller_trafo import (
    InputControllerTrafo,
)
from midas.core.powergrid.helper.input_assigment.elements.input_controller_line import (
    InputControllerLine,
)
from midas.core.powergrid.helper.input_assigment.elements.input_controller_sgen import (
    InputControllerSgen,
)
from midas.core.powergrid.helper.input_assigment.elements.input_controller_load import (
    InputControllerLoad,
)
from midas.core.powergrid.helper.input_assigment.elements.input_controller_storage import (
    InputControllerStorage,
)
from midas.core.powergrid.helper.input_assigment.elements.input_controller_ext_grid import (
    InputControllerExtGrid,
)

META_CONSTRAINT = {
    "Switch": InputControllerSwitch(),
    "Trafo": InputControllerTrafo(),
    "Sgen": InputControllerSgen(),
    "Load": InputControllerLoad(),
    "Line": InputControllerLine(),
    "Storage": InputControllerStorage(),
    "Ext_grid": InputControllerExtGrid(),
}


class InputAssigmentHelper:
    def assigment_failed_values(self, etype, attrs):
        replacedAttrs = attrs
        if etype in META_CONSTRAINT:
            replacedAttrs = META_CONSTRAINT[etype].assigment(attrs)
        return replacedAttrs
