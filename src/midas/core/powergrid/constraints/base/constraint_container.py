class ConstraintContainer:
    def __init__(self, cid, model):
        self.grid_element = model.entity_map[cid]
        self.model = model
        self.cid = cid
        self.constraints = list()
        self.stable = True

    def add_constraint(self, constraint):
        self.constraints.append(constraint)

    def set_in_service(self, val):
        data = {"in_service": val}
        self.model.set_inputs(
            self.grid_element["etype"], self.grid_element["idx"], data
        )
        self.grid_element["static"]["in_service"] = val

    def handle_violation(self):
        self.stable = False
        self.set_in_service(False)

    def handle_stable(self):
        self.stable = True
        self.set_in_service(True)

    def can_reconnect(self):
        bus_id = self.grid_element["static"]["bus"]
        bus_id = f"0-bus-{bus_id}"
        output = self.model.get_outputs()
        voltage = output[bus_id]["vm_pu"]
        if voltage < 0.95:
            return False
        else:
            return True

    def check_constraints(self, time):
        unsatisfied_constraints = [
            constr
            for constr in self.constraints
            if constr.check(time) is False
        ]

        returnArray = [c.get_key() for c in unsatisfied_constraints]

        if not self.stable:
            if not unsatisfied_constraints and self.can_reconnect():
                self.handle_stable()
            # write this specific constraint violation only once to array
            if "ConstraintMaxPercentLine" in returnArray:
                returnArray.remove("ConstraintMaxPercentLine")
            if "ConstraintMaxPercentTrafo" in returnArray:
                returnArray.remove("ConstraintMaxPercentTrafo")
        if unsatisfied_constraints and self.stable:
            self.handle_violation()

        return returnArray
