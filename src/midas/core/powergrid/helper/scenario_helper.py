class ScenarioHelper:
    def __init__(self, scenario_param, entity_map):
        self.scenario = scenario_param
        self.entity_map = entity_map

        self.old_values = dict()

    def handle(self, inputs, models, time):
        # filter execution by time step
        execs_by_time = [
            x[2] for x in self.scenario if eval(x[0]) <= time <= eval(x[1])
        ]

        for exec_by_time in execs_by_time:
            for key, value in exec_by_time.items():
                key_split = key.split(".")

                if len(key_split) > 1:
                    eid = key_split[0]
                    attr_key = key_split[1]

                    # check valid scenario attr
                    if attr_key not in [
                        "in_service",
                        "p_mw",
                        "tap_pos",
                        "tap_max",
                        "tap_min",
                        "closed",
                        "scaling",
                    ]:
                        continue

                    self.backup_old_values(eid, attr_key, models)

                    if eid in inputs.keys():
                        inputs[eid][attr_key] = {"scenario": eval(str(value))}
                    else:
                        inputs[eid] = dict()
                        inputs[eid][attr_key] = {"scenario": eval(str(value))}

        for eid, backup_values in self.old_values.copy().items():
            for attr_key, backup_value in backup_values.copy().items():
                inputs = self.update_old_values(
                    eid, attr_key, backup_value, inputs, execs_by_time
                )

        return inputs

    def update_old_values(
        self, eid, attr_key, backup_value, inputs, execs_by_time
    ):
        for exec_by_time in execs_by_time:
            if f"{eid}.{attr_key}" in exec_by_time.keys():
                return inputs

        if eid not in inputs.keys():
            inputs[eid] = dict()
            inputs[eid][attr_key] = {"scenario": backup_value}
        elif attr_key not in inputs[eid].keys():
            inputs[eid][attr_key] = {"scenario": backup_value}

        del self.old_values[eid][attr_key]

        if len(self.old_values[eid]) == 0:
            del self.old_values[eid]

        return inputs

    def backup_old_values(self, eid, attr_key, models):
        gidx = eid.split("-")[0]
        grid = models.get(f"Grid-{gidx}", models.get(f"GridTS-{gidx}", None))

        idx = self.entity_map[eid]["idx"]
        etype = self.entity_map[eid]["etype"]

        # backup old values
        old_value = grid.grid[etype.lower()].iloc[idx][attr_key]
        if eid not in self.old_values.keys():
            self.old_values[eid] = dict()
        if attr_key not in self.old_values[eid].keys():
            self.old_values[eid][attr_key] = old_value
