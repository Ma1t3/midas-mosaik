"""Convert a PG-Arl Load profile in HDF5 database."""
import pandas as pd
import logging
import os.path

LOG = logging.getLogger("midas.cli")
import os
from .runtime_config import RuntimeConfig


def pg_arl_converter(data_path, tmp_path, if_necessary, force):
    LOG.info("Preparing generator wip and ccgt timeseries...")
    config = RuntimeConfig().data["generator_timeseries"][1]
    if if_necessary and not config.get("load_on_start", False):
        return
    output_path = os.path.abspath(os.path.join(data_path, config["name"]))

    if os.path.exists(output_path):
        LOG.debug("Found existing dataset at '%s'.", output_path)
        if not force:
            return

    data = _download_and_read(config)
    data.to_hdf(output_path, "sgen_pmw", "w")

    LOG.info("Successfully created database for WIP and CCGT.")


def _download_and_read(config):
    resource_path = os.path.join(os.path.split(__file__)[0], "../")
    data = pd.DataFrame()
    for key, val in config["source"].items():
        ydata = pd.read_csv(resource_path + key, sep=";")
        data["Datum"] = ydata["Datum"]
        data[val] = ydata["MW"]
    return data.set_index("Datum")
