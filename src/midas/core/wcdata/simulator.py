"""This module contains a simulator for timeseries for PG ASC
WIP waste incineration plant
CCGT Combined cycle power plant - in German "Gas-und-Dampf-Kombikraftwerk"
"""
import os

import pandas as pd
from midas.util.base_data_simulator import BaseDataSimulator
from midas.util.print_format import mformat
from midas.util.runtime_config import RuntimeConfig
from midas.util.base_data_specific_cos_phi_model import (
    BaseDataSpecificCosPhiModel,
)

from . import LOG
from .meta import META


class WIPAndGasDataSimulator(BaseDataSimulator):
    def __init__(self):
        super().__init__(META)

        self.data = None

        self.num_models = dict()

    def init(self, sid, **sim_params):
        super().init(sid, **sim_params)

        # Load the data
        data_path = sim_params.get(
            "data_path", RuntimeConfig().paths["data_path"]
        )
        file_path = os.path.join(
            data_path,
            sim_params.get(
                "filename",
                RuntimeConfig().data["generator_timeseries"][1]["name"],
            ),
        )
        LOG.debug("Using db file at '%s", file_path)
        self.data = pd.read_hdf(file_path, "sgen_pmw")

        return self.meta

    def create(self, num, model, **model_params):
        entities = list()
        self.num_models.setdefault(model, 0)
        for _ in range(num):
            eid = f"{model}-{self.num_models[model]}"

            p_peak_mw = model_params.get("p_peak_mw", None)
            if p_peak_mw is not None:
                scaling = p_peak_mw / self.data[model].max()
            else:
                scaling = model_params.get("scaling", 1.0)

            self.models[eid] = BaseDataSpecificCosPhiModel(
                data_p=self.data[model],
                data_q=None,
                data_step_size=900,
                scaling=scaling,
                eid_cos_phi=model_params["eid_cos_phi"],
                seed=self.rng.randint(self.seed_max),
                interpolate=model_params.get("interpolate", self.interpolate),
                randomize_data=model_params.get(
                    "randomize_data", self.randomize_data
                ),
                randomize_cos_phi=model_params.get(
                    "randomize_cos_phi", self.randomize_cos_phi
                ),
            )
            self.num_models[model] += 1
            entities.append({"eid": eid, "type": model})

        return entities

    def step(self, time, inputs, max_advance=0):
        LOG.debug("At step %d received inputs %s", time, mformat(inputs))

        return super().step(time, inputs, max_advance)

    def get_data(self, outputs):
        data = super().get_data(outputs)

        LOG.debug("Gathered outputs %s", mformat(data))

        return data

    def get_data_info(self):
        info = {
            key: {"p_mwh_per_a": model.p_mwh_per_a, "scaling": model.scaling}
            for key, model in self.models.items()
        }
        info["num_wip"] = self.num_models.get("WIP", 0)
        info["num_ccgt"] = self.num_models.get("CCGT", 0)
        info["num_sgens"] = info["num_wip"] + info["num_ccgt"]

        return info
