import datetime
import copy
import numpy as np

from midas.core.powergrid.constraints.base.constraint import Constraint


class ConstraintVoltage(Constraint):
    """
    TAB4
    The voltage value of a generator is allowed to move between 85% and 115%
    of its expected value
    """

    def __init__(self, constraint_container):
        super().__init__(constraint_container)
        self.bus_id = self.constraint_container.grid_element["static"]["bus"]
        self.bus_id = f"0-bus-{self.bus_id}"
        self.low_barrier = 0.85
        self.high_barrier = 1.15

    def check(self, time):
        output = self.constraint_container.model.get_outputs()
        voltage = output[self.bus_id]["vm_pu"]

        if np.isnan(voltage):
            # Bus is dead because of a trafo
            self.satisfied = True
        elif not self.low_barrier < voltage < self.high_barrier:
            # Violation
            self.satisfied = False
            self.violated_value = voltage
        else:
            # Everything is fine
            if self.satisfied is False:
                # Simulate what would happen if constraint would be deactivated
                model_copy = copy.deepcopy(self.constraint_container.model)

                # Set in_service parameter for ppModel AND instance of midas.static.py
                grid_element_copy = model_copy.entity_map[
                    self.constraint_container.cid
                ]

                grid_element_copy["static"]["in_service"] = True
                data = {"in_service": True}
                model_copy.set_inputs(
                    grid_element_copy["etype"], grid_element_copy["idx"], data
                )

                model_copy.run_powerflow()

                new_output = model_copy.get_outputs()
                new_voltage = new_output[self.bus_id]["vm_pu"]

                if not self.low_barrier < new_voltage < self.high_barrier:
                    # Still broken
                    self.satisfied = False
                    self.violated_value = new_voltage
                else:
                    self.satisfied = True
            else:
                self.satisfied = True

        return self.satisfied

    def get_key(self):
        return "ConstraintVoltage"
