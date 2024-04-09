from midas.core.powergrid.constraints.base.constraint import Constraint


class ConstraintMaxPercentLine(Constraint):
    def __init__(self, constraint_container):
        # loading_percent is not allowed to be over 100 %

        super().__init__(constraint_container)
        self.line_id = self.constraint_container.grid_element["idx"]
        self.line_id = f"0-line-{self.line_id}"
        self.max_percentage = 100.0

    def check(self, time):
        output = self.constraint_container.model.get_outputs()
        loading_percent = output[self.line_id]["loading_percent"]

        if loading_percent >= self.max_percentage:
            self.satisfied = False

        return self.satisfied

    def get_key(self):
        return "ConstraintMaxPercentLine"
