"""MIDAS upgrade module for WIP and CCGT timeseries data simulator."""
import logging

from midas.util.runtime_config import RuntimeConfig
from .pwdata import PVWindDataModule

LOG = logging.getLogger(__name__)


class WIPAndGasDataModule(PVWindDataModule):
    def __init__(self):
        super().__init__("wcdata")
        self.default_grid = "midasmv"
        self.default_sim_name = "WIPAndGasData"
        self.default_import_str = "midas.core:WIPAndGasDataSimulator"
        self.models = {"WIP": ["p_mw", "q_mvar"], "CCGT": ["p_mw", "q_mvar"]}

    def check_sim_params(self, module_params, **kwargs):
        self.sim_params.setdefault(
            "filename", RuntimeConfig().data["generator_timeseries"][1]["name"]
        )
        super().check_sim_params(module_params, **kwargs)

    def create_default_mapping(self):
        default_mapping = dict()
        if self.sim_name == self.default_grid:
            default_mapping = {13: [["WIP", 1.0]], 14: [["CCGT", 1.0]]}

        return default_mapping
