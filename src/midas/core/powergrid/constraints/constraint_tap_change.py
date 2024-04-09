import datetime
import copy
import numpy as np

from midas.core.powergrid.constraints.base.constraint import Constraint


class ConstraintTapChange(Constraint):
    def __init__(self, constraint_container):
        super().__init__(constraint_container)
        self.trafo_id = self.constraint_container.grid_element["idx"]
        self.trafo_id = f"0-trafo-{self.trafo_id}"
        self.changes_per_hour = 120
        self.last_change = 0
        self.changes = dict()
        self.old_pos = 0.0
        self.satisfied = True

    def check(self, time):
        current_pos = self.constraint_container.grid_element["static"][
            "tap_pos"
        ]
        if current_pos != self.old_pos:
            self.changes[time] = current_pos

            start = max(0, time - 3600)
            num_changes = 0
            for t in range(start, time):
                if t in self.changes:
                    num_changes += 1

            if num_changes > self.changes_per_hour:
                self.constraint_container.grid_element["static"][
                    "tap_pos"
                ] = self.old_pos

        self.old_pos = self.constraint_container.grid_element["static"][
            "tap_pos"
        ]
        return self.satisfied

    def get_key(self):
        return "ConstraintTapChange"
