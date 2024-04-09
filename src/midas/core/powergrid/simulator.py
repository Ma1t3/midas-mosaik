"""This module implements the mosaik simulator API for the
pandapower model.

"""
import distutils.util
import numpy as np
import copy

import mosaik_api
from midas.core.powergrid import LOG
from midas.util.dict_util import update
from midas.util.plotter import Plotter
from midas.util.print_format import mformat

from .meta import META
from .meta_constraint import META_CONSTRAINT
from .model.static import PandapowerGrid
from .constraints.base.constraint_container import ConstraintContainer
from .helper.input_assigment.InputAssigmentHelper import InputAssigmentHelper
from .helper.scenario_helper import ScenarioHelper


class PandapowerSimulator(mosaik_api.Simulator):
    """The pandapower simulator."""

    def __init__(self):
        super().__init__(META)
        self.sid = None
        self.models = dict()
        self.entity_map = dict()
        self.entities = list()
        self.input_assigment_helper = InputAssigmentHelper()

        self.step_size = None
        self.constraint = False
        self.now_dt = None
        self.cache = dict()

        self.constraints = dict()
        self.constraints_log = {}
        self.plotter_cfg = dict()
        self.duplicate_actuators_suffix = None
        self.plotter = None
        self.sensors = None
        self.scenario_helper = None

    def init(self, sid, **sim_params):
        """Called exactly ones after the simulator has been started.

        Parameters
        ----------
        sid : str
            Simulator ID for this simulator.
        step_size : int, optional
            Step size for this simulator. Defaults to 900.

        Returns
        -------
        dict
            The meta dict (set by mosaik_api.Simulator)

        """
        if "step_size" not in sim_params:
            LOG.debug(
                "Param *step_size* not provided. "
                + "Using default step_size of 900."
            )

        self.step_size = sim_params.get("step_size", 900)

        plotting = sim_params.get("plotting", False)
        self.sensors = sim_params.get("sensors", dict())[0]
        self.constraint = sim_params.get("constraint", False)
        self.scenario_params = sim_params.get("scenario", [])
        self.duplicate_actuators_suffix = sim_params.get(
            "duplicate_actuators_suffix", "_prio-"
        )

        if not isinstance(plotting, bool):
            try:
                plotting = bool(distutils.util.strtobool(plotting))
            except AttributeError:
                plotting = False

        if plotting:
            self.plotter = Plotter()
            self.plotter_cfg["plot_path"] = sim_params.get(
                "plot_path", "_plots"
            )

        return self.meta

    def create(self, num, model, **model_params):
        """Initialize the simulation model instance (entity)

        Returns
        -------
        list
            A list with information on the created entity.

        """

        entities = list()

        for _ in range(num):
            gidx = len(self.models)
            eid = f"{model}-{gidx}"

            if model == "Grid":
                self.models[eid] = PandapowerGrid()

            if model == "GridTS":
                # Add the time series grid here
                pass

            if "gridfile" not in model_params:
                LOG.debug(
                    "Param *gridfile* not provided in model_params. "
                    "Using default grid *midasmv*"
                )

            gridfile = model_params.get("gridfile", "midasmv")
            self.models[eid].setup(gridfile, gidx)
            self.plotter_cfg[eid] = {
                "grid_type": self.models[eid].grid_type,
                "plot_name": gridfile,
                "plotting": model_params.get("plotting", False),
            }

            children = list()
            self.constraints[eid] = dict()

            for cid, attrs in sorted(self.models[eid].entity_map.items()):
                assert cid not in self.entity_map
                self.entity_map[cid] = attrs
                etype = attrs["etype"]

                # create all constraints for powergrid element
                if self.constraint:
                    self.create_constraints(eid, cid, etype)

                # We'll only add relations from lines to nodes (and not
                # from nodes to lines) because this is sufficient for
                # mosaik to build the entity graph
                relations = list()
                if etype.lower() in [
                    "trafo",
                    "line",
                    "load",
                    "sgen",
                    "storage",
                ]:
                    relations = attrs["related"]

                children.append({"eid": cid, "type": etype, "rel": relations})

            entity = {
                "eid": eid,
                "type": model,
                "rel": list(),
                "children": children,
            }
            entities.append(entity)
            self.entities.append(entity)

        self.scenario_helper = ScenarioHelper(
            self.scenario_params, self.entity_map
        )

        return entities

    def step(self, time, inputs, max_advance=0):
        """Perform a simulation step.
        Parameters
        ----------
        time : int
            The current simulation step (by convention in seconds since
            simulation start.
        inputs : dict
            A *dict* containing inputs for entities of this simulator.

        Returns
        -------
        int
            The next step this simulator wants to be stepped.
        """
        LOG.debug("At step %d received inputs %s", time, mformat(inputs))

        inputs = self.scenario_helper.handle(inputs, self.models, time)
        for eid, attrs in inputs.items():
            gidx = eid.split("-")[0]
            grid = self.models.get(
                f"Grid-{gidx}", self.models.get(f"GridTS-{gidx}", None)
            )

            if grid is None:
                LOG.critical("No grid found for grid index %s!", gidx)
                raise KeyError

            idx = self.entity_map[eid]["idx"]
            etype = self.entity_map[eid]["etype"]

            # Filter Agent actuators
            filter_agent_attrs = {
                key: val
                for key, val in attrs.items()
                if self.duplicate_actuators_suffix in key
            }
            filter_attrs_cache = dict()

            for key, val in filter_agent_attrs.items():
                key_split = key.split(self.duplicate_actuators_suffix)
                attr_key = key_split[0]
                agent_id = -1
                if len(key_split) > 0:
                    agent_id = key_split[1]

                if list(val.values())[0] is not None:
                    if attr_key in filter_attrs_cache:
                        # highest Agent-actuator will be set for attr
                        if (
                            agent_id < filter_attrs_cache[attr_key]["agent_id"]
                            and agent_id != -1
                        ):
                            filter_attrs_cache[attr_key] = {
                                "agent_id": agent_id,
                                "entity": val,
                            }
                    else:
                        filter_attrs_cache[attr_key] = {
                            "agent_id": agent_id,
                            "entity": val,
                        }
                    # remove Agent keys
                    del attrs[key]
            for key, val in filter_attrs_cache.items():
                # replace attrs[key] with Agent values
                attrs[key] = val["entity"]

            for attr, src_ids in attrs.items():
                setpoint = 0.0

                for src_id, val in src_ids.items():
                    setpoint += float(val)

                attrs[attr] = setpoint

            attrs = self.input_assigment_helper.assigment_failed_values(
                etype, attrs
            )

            for key, value in attrs.items():
                # sync static variables from grid instance with the model instance
                if key in ["scaling", "in_service", "tap_pos", "p_mw"]:
                    self.models[f"Grid-{gidx}"].entity_map[eid]["static"][
                        key
                    ] = value
            grid.set_inputs(etype, idx, attrs)

        for eid, model in self.models.items():
            model.run_powerflow()

            # reset constraint log
            self.constraints_log[eid] = {}

            # check all constraints for all powergrid elements
            for cid, attrs in sorted(self.models[eid].entity_map.items()):
                self.check_constraints(eid, cid, time)

            self.cache[eid] = model.get_outputs()
            for child, cache in self.cache[eid].items():
                self.cache[child] = cache

            if self.plotter is not None and self.plotter_cfg[eid]["plotting"]:
                self.plotter.grid = model.grid
                self.plotter.plot_path = self.plotter_cfg["plot_path"]
                self.plotter.plot_name = self.plotter_cfg[eid]["plot_name"]
                self.plotter.grid_type = self.plotter_cfg[eid]["grid_type"]
                self.plotter.plot(eid, int(time / self.step_size))

        return time + self.step_size

    def create_constraints(self, eid, cid, type):
        if len(self.meta["models"][type]["constraints"]) > 0:
            constraint_container = ConstraintContainer(cid, self.models[eid])

            for constraintKey in self.meta["models"][type]["constraints"]:
                constraint = META_CONSTRAINT[constraintKey](
                    constraint_container
                )
                constraint_container.add_constraint(constraint)

            self.constraints[eid][cid] = constraint_container

    def check_constraints(self, eid, cid, time):
        if cid in self.constraints[eid]:
            failed_constraints = self.constraints[eid][cid].check_constraints(
                time
            )
            self.constraints_log[eid][cid] = failed_constraints

    def get_data(self, outputs):
        """Return the requested outputs (if feasible).

        Parameters
        ----------
        outputs : dict
            A *dict* containing requested outputs of each entity.

        Returns
        -------
        dict
            A *dict* containing the values of the requested outputs.

        """
        data = dict()
        grid_json = dict()
        for eid, attrs in outputs.items():
            if "Grid" in eid:
                model_not_nan = self.get_not_nan_model(self.models[eid])

                if "health" in attrs:
                    data.setdefault(eid, dict())[
                        "health"
                    ] = model_not_nan.grid.res_bus.vm_pu.values[1:].mean()
                if "constraints" in attrs:
                    data.setdefault(eid, dict())[
                        "constraints"
                    ] = self.constraints_log
                if "grid_json" in attrs:
                    grid_json.setdefault(eid, dict())[
                        "grid_json"
                    ] = model_not_nan.to_json()
                continue

            for attr in attrs:
                if attr in self.cache[eid]:
                    val = self.cache[eid][attr]
                    if np.isnan(val):
                        aEid = eid.split("-")
                        val = self.get_default_value(aEid[1], attr)
                    data.setdefault(eid, dict())[attr] = val
                else:
                    attr_key = attr
                    if attr_key == "p_mw_flex":
                        attr_key = "p_mw"
                    val = self.models[list(self.models.keys())[0]].entity_map[
                        eid
                    ]["static"][attr_key]
                    data.setdefault(eid, dict())[attr] = val

        LOG.debug("Gathered outputs %s", mformat(data))
        update(data, grid_json)
        return data

    def get_not_nan_model(self, model):
        model_copy = copy.deepcopy(model)

        model_copy.grid.res_bus.vm_pu.values[1:] = np.nan_to_num(
            model_copy.grid.res_bus.vm_pu.values[1:],
            nan=self.get_default_value("bus", "vm_pu"),
        )

        model_copy.grid.res_bus.va_degree.values[1:] = np.nan_to_num(
            model_copy.grid.res_bus.va_degree.values[1:],
            nan=self.get_default_value("bus", "va_degree"),
        )

        model_copy.grid.res_trafo.loading_percent.values[1:] = np.nan_to_num(
            model_copy.grid.res_trafo.loading_percent.values[1:],
            nan=self.get_default_value("trafo", "loading_percent"),
        )

        model_copy.grid.res_line.loading_percent.values[1:] = np.nan_to_num(
            model_copy.grid.res_line.loading_percent.values[1:],
            nan=self.get_default_value("line", "loading_percent"),
        )

        return model_copy

    def get_default_value(self, type, attr):
        if type.capitalize() in self.sensors:
            attrs_values = [
                val
                for val in self.sensors[type.capitalize()]
                if val[0] == attr
            ]
            if len(attrs_values) > 0 and len(attrs_values[0]) > 3:
                return attrs_values[0][3]
            return 0.0


if __name__ == "__main__":
    mosaik_api.start_simulation(PandapowerSimulator())
