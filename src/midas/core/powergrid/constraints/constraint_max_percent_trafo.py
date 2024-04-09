from midas.core.powergrid.constraints.base.constraint import Constraint


class ConstraintMaxPercentTrafo(Constraint):
    def __init__(self, constraint_container):
        # loading_percent is not allowed to be over 150 %

        # exact definition for max-loading value for oil-immersed trafos
        # https://www.se.com/eg/en/faqs/FA335947/

        super().__init__(constraint_container)
        self.trafo_id = self.constraint_container.grid_element["idx"]
        self.trafo_id = f"0-trafo-{self.trafo_id}"
        self.max_percentage = 150.0

    def check(self, time):
        output = self.constraint_container.model.get_outputs()
        loading_percent = output[self.trafo_id]["loading_percent"]

        if loading_percent >= self.max_percentage:
            self.satisfied = False

        return self.satisfied

    def get_key(self):
        return "ConstraintMaxPercentTrafo"
