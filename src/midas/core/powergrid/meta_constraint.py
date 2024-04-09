from midas.core.powergrid.constraints.constraint_max_percent_line import (
    ConstraintMaxPercentLine,
)
from midas.core.powergrid.constraints.constraint_max_percent_trafo import (
    ConstraintMaxPercentTrafo,
)
from midas.core.powergrid.constraints.constraint_reactive_power import (
    ConstraintReactivePower,
)
from midas.core.powergrid.constraints.constraint_tap_change import (
    ConstraintTapChange,
)
from midas.core.powergrid.constraints.constraint_voltage import (
    ConstraintVoltage,
)
from midas.core.powergrid.constraints.constraint_voltage_change import (
    ConstraintVoltageChange,
)
from midas.core.powergrid.constraints.constraint_voltage_timed import (
    ConstraintVoltageTimed,
)

META_CONSTRAINT = {
    "constraint_voltage_timed": ConstraintVoltageTimed,
    "constraint_voltage_change": ConstraintVoltageChange,
    "constraint_max_percent_line": ConstraintMaxPercentLine,
    "constraint_max_percent_trafo": ConstraintMaxPercentTrafo,
    "constraint_voltage": ConstraintVoltage,
    "constraint_reactive_power": ConstraintReactivePower,
    "constraint_tap_change": ConstraintTapChange,
}
