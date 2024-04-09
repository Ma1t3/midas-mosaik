import collections
import datetime
import copy

from midas.core.powergrid.constraints.base.constraint import Constraint

TimedVoltage = collections.namedtuple("TimedVoltage", ["time", "value"])


class ConstraintVoltageChange(Constraint):
    """
    TAB1
    The voltage change of a generator is not allowed to rise over 5%
    The voltage change of a load is not allowed to rise over 2%
    """

    def __init__(self, constraint_container):
        super().__init__(constraint_container)
        self.bus_id = self.constraint_container.grid_element["static"]["bus"]
        self.bus_id = f"0-bus-{self.bus_id}"

        self.etype = self.constraint_container.grid_element["etype"]
        if self.etype == "Load":
            self.expected_value = 0.02  # Load
        elif self.etype == "Sgen":
            self.expected_value = 0.05  # Gen

        self.time_frame = datetime.timedelta(minutes=3)
        self.time_voltages = []

    def check(self, time):
        output = self.constraint_container.model.get_outputs()
        voltage = output[self.bus_id]["vm_pu"]
        # Remove all (Time, Voltage) entries from list that are older
        # than 3 minutes; afterwards add the current tuple
        self.time_voltages = [
            entry
            for entry in self.time_voltages
            if time - entry.time < self.time_frame.total_seconds()
        ]
        current_t_v = TimedVoltage(time=time, value=voltage)
        self.time_voltages.append(current_t_v)

        # Create a list of all voltage values without their timestamp
        # to find smallest and largest value
        voltage_values = [entry.value for entry in self.time_voltages]
        min_voltage = min(voltage_values)
        max_voltage = max(voltage_values)

        if min_voltage == 0:
            self.satisfied = False
        else:
            # Calculate deviation of smallest and largest value
            voltage_change_percent = (
                abs(max_voltage - min_voltage) / min_voltage
            )
            voltage_change_percent = round(voltage_change_percent, 6)

            if voltage_change_percent > self.expected_value:
                # Violation
                self.satisfied = False
                self.violated_value = voltage_change_percent
                self.time_voltages.clear()
            else:
                # Everything is fine
                if self.satisfied is False:
                    # Simulate what would happen if constraint would be deactivated
                    model_copy = copy.deepcopy(self.constraint_container.model)

                    copy_output = model_copy.get_outputs()
                    old_voltage = copy_output[self.bus_id]["vm_pu"]

                    grid_element_copy = model_copy.entity_map[
                        self.constraint_container.cid
                    ]
                    grid_element_copy["static"]["in_service"] = True
                    data = {"in_service": True}
                    model_copy.set_inputs(
                        grid_element_copy["etype"],
                        grid_element_copy["idx"],
                        data,
                    )

                    model_copy.run_powerflow()

                    copy_output = model_copy.get_outputs()
                    new_voltage = copy_output[self.bus_id]["vm_pu"]

                    new_voltage_change_percent = (
                        abs(new_voltage - old_voltage) / old_voltage
                    )

                    if new_voltage_change_percent > self.expected_value:
                        # Still broken
                        self.satisfied = False
                    else:
                        self.satisfied = True
                else:
                    self.satisfied = True
        return self.satisfied

    def get_key(self):
        return "ConstraintVoltageChange"
