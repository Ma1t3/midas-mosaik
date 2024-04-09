from midas.core.powergrid.constraints.base.constraint import Constraint


class ConstraintReactivePower(Constraint):
    """
    TAR MS 10.2.2
    Generators must provide reactive power in the
    range -0.48 <= Q/P nominal <= 0.48
    """

    def __init__(self, constraint_container):
        super().__init__(constraint_container)
        self.expected_value = 0.48
        self.re_satisfied_in_last_step: bool = False

        self.gen_id = self.constraint_container.grid_element["idx"]
        self.bus_id = self.constraint_container.grid_element["static"]["bus"]
        self.gen_id = f"0-sgen-{self.gen_id}-{self.bus_id}"

    def check(self, time):
        output = self.constraint_container.model.get_outputs()

        rated_power = output[self.gen_id]["p_mw"]
        reactive_power = output[self.gen_id]["q_mvar"]

        try:
            rated_power = float(rated_power)
            reactive_power = float(reactive_power)
            if abs(reactive_power / rated_power) > self.expected_value:
                if self.re_satisfied_in_last_step:
                    self.re_satisfied_in_last_step = False
                    self.satisfied = True
                else:
                    self.violated_value = reactive_power / rated_power
                    self.satisfied = False
            else:
                if not self.satisfied:
                    self.re_satisfied_in_last_step = True
                else:
                    self.re_satisfied_in_last_step = False
                self.satisfied = True

        except ZeroDivisionError:
            self.satisfied = True

        return self.satisfied

    def get_key(self):
        return "ConstraintReactivePower"
