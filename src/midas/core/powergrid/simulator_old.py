"""This module implements the mosaik simulator API for the
pandapower model.

"""
import json
import logging
import sys
from typing import Any, Dict, List

import numpy as np
import mosaik_api
from midas.util.dict_util import strtobool, update
from midas.util.logging import set_and_init_logger
from midas.util.print_format import mformat
from midas.util.runtime_config import RuntimeConfig

from .meta import META
from .model.constrainted import ConstraintedGrid
from .model.static import PandapowerGrid
from .plotter import Plotter

# Need to hard code the name because if started as separate
# procress, the __name__ is __main__ instead.
LOG = logging.getLogger("midas.modules.powergrid.simulator")
# KVLOG = logging.getLogger("midas.modules.powergrid.simulator.keyvalue")


class PandapowerSimulator(mosaik_api.Simulator):
    """The pandapower simulator."""

    def __init__(self):
        super().__init__(META)
        self.sid: str = ""
        self.models: Dict[str, PandapowerGrid] = {}
        self.entity_map: dict = {}
        self.entities: list = []

        self.step_size: int = 0
        self.now_dt = None
        self.cache = dict()

        self.plotting = False
        self.plotter_cfg = dict()
        self.plotter = None
        self._sim_time: int = 0
        self.key_value_logs: bool

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
        self.sid = sid
        if "step_size" not in sim_params:
            LOG.debug(
                "Param *step_size* not provided. "
                + "Using default step_size of 900."
            )

        self.step_size = sim_params.get("step_size", 900)

        self.plotting = sim_params.get("plotting", False)
        if not isinstance(self.plotting, bool):
            try:
                self.plotting = strtobool(self.plotting)
            except AttributeError:
                self.plotting = False

        if self.plotting:
            self.plotter = Plotter()
            self.plotter_cfg["plot_path"] = sim_params.get(
                "plot_path", "_plots"
            )

        self.key_value_logs = sim_params.get(
            "key_value_logs", RuntimeConfig().misc.get("key_value_logs", False)
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
        use_constraints = model_params.get("use_constraints", False)

        for _ in range(num):
            gidx = len(self.models)
            eid = f"{model}-{gidx}"

            if model == "Grid":
                if use_constraints:
                    self.models[eid] = ConstraintedGrid(
                        model_params.get("constraints", list())
                    )
                else:
                    self.models[eid] = PandapowerGrid()

            if "gridfile" not in model_params:
                LOG.debug(
                    "Param *gridfile* not provided in model_params. "
                    "Using default grid *midasmv*"
                )

            gridfile = model_params.get("gridfile", "midasmv")
            grid_params = model_params.get("grid_params", dict())
            self.models[eid].setup(gridfile, gidx, grid_params)
            self.plotter_cfg[eid] = {
                "grid_type": self.models[eid].grid_type,
                "plot_name": gridfile,
                "plotting": self.plotting,
            }

            children = list()
            for cid, attrs in sorted(self.models[eid].entity_map.items()):
                assert cid not in self.entity_map
                self.entity_map[cid] = attrs
                etype = attrs["etype"]

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
        self._sim_time = time
        if not self.key_value_logs:
            LOG.debug("At step %d received inputs %s", time, mformat(inputs))

        for eid, attrs in inputs.items():
            gidx = eid.split("-")[0]
            grid = self.models.get(f"Grid-{gidx}", None)

            if grid is None:
                LOG.critical("No grid found for grid index %s!", gidx)
                raise KeyError

            idx = self.entity_map[eid]["idx"]
            etype = self.entity_map[eid]["etype"]

            for attr, src_ids in attrs.items():
                setpoint = 0.0

                for val in src_ids.values():
                    setpoint += float(val)

                attrs[attr] = setpoint
            try:
                grid.set_inputs(etype, idx, attrs)
            except Exception as err:
                LOG.error(
                    f"Failed to set inputs {attrs} for etype {etype}"
                    f" at index {idx}: {err}"
                )
                raise ValueError(
                    f"Impossible input {attrs} for {etype} ({idx})."
                )

        for eid, model in self.models.items():
            try:
                model.run_powerflow(time)
            except Exception as err:
                LOG.error(f"Failed to perform power flow calculation: {err}")
                raise ValueError(
                    f"Failed to perform power flow calculation: {err}"
                )

            try:
                self.cache[eid] = model.get_outputs()
                for child, cache in self.cache[eid].items():
                    self.cache[child] = cache
            except Exception as err:
                LOG.error(f"Failed to get outputs: {err}")
                raise ValueError(f"Failed to get outputs: {err}")

            if self.plotter is not None and self.plotter_cfg[eid]["plotting"]:
                self.plotter.grid = model.grid
                self.plotter.plot_path = self.plotter_cfg["plot_path"]
                self.plotter.plot_name = self.plotter_cfg[eid]["plot_name"]
                self.plotter.grid_type = self.plotter_cfg[eid]["grid_type"]
                self.plotter.plot(eid, int(time / self.step_size))

        return time + self.step_size

    def get_data(
        self, outputs: Dict[str, List[str]]
    ) -> Dict[str, Dict[str, Any]]:
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

        data: dict = {}
        grid_json: dict = {}

        for eid, attrs in outputs.items():
            if "Grid" in eid:
                self._get_grid_attributes(eid, attrs, data, grid_json)
            else:
                self._get_children_attributes(eid, attrs, data)

        if not self.key_value_logs:
            LOG.debug(
                "At step %d gathered outputs %s", self._sim_time, mformat(data)
            )

        update(data, grid_json)
        return data

    def _get_grid_attributes(
        self,
        eid: str,
        attrs: List[str],
        data: Dict[str, Dict[str, Any]],
        grid_json: Dict[str, Any],
    ) -> None:
        if "health" in attrs:
            health = self.models[eid].grid.res_bus.vm_pu.values[1:].mean()
            if np.isnan(health):
                LOG.debug(
                    "Grid health is NaN. This might be okay so "
                    "setting health to 0. Just that you know!"
                )
                health = 0
            data.setdefault(eid, dict())["health"] = health

        if "grid_json" in attrs:
            grid_json.setdefault(eid, dict())["grid_json"] = self.models[
                eid
            ].to_json()

    def _get_children_attributes(
        self,
        eid: str,
        attrs: List[str],
        data: Dict[str, Dict[str, Any]],
    ) -> None:
        log_msg = {
            "id": f"{self.sid}_{eid}",
            "name": eid,
            "type": eid.split("-")[1],
        }
        for attr in attrs:
            val = self.cache[eid][attr]
            if np.isnan(val):
                LOG.debug(f"{attr} for {eid} is NaN. Setting to 0.")
                val = 0
            data.setdefault(eid, dict())[attr] = val
            if isinstance(val, np.bool_):
                val = bool(val)
            log_msg[attr] = val

        if self.key_value_logs:
            try:
                LOG.info(json.dumps(log_msg))
            except TypeError:
                print(log_msg)
                sys.exit(-1)


if __name__ == "__main__":
    set_and_init_logger(
        0, "powergrid-logfile", "midas-powergrid.log", replace=True
    )
    LOG.info("Starting mosaik simulation...")
    mosaik_api.start_simulation(PandapowerSimulator())
