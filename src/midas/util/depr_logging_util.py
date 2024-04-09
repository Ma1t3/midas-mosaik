"""This module contains the logging configuration for midas."""
import logging


SETUP_CALLED = False


def setup_logging(loglevel=None, logfilename=None):
    """Setup logging with *loglevel* level."""
    global SETUP_CALLED

    if loglevel is None:
        if not SETUP_CALLED:
            loglevel = "DEBUG"
        else:
            return

    numeric_level = getattr(logging, loglevel.upper(), None)
    if not isinstance(numeric_level, int):
        raise ValueError(f"Invalid log level: {loglevel}.")

    if logfilename is None or logfilename == "None":
        logfilename = "midas"
    logging.basicConfig(
        filename=f"{logfilename}.log",
        filemode="w",
        level=numeric_level,
        format="%(asctime)s [%(name)s][%(levelname)s] %(message)s",
    )
    logging.getLogger("matplotlib").setLevel(logging.WARNING)
    logging.getLogger("numba").setLevel(logging.WARNING)
    logging.getLogger("simbench").setLevel(logging.WARNING)
    logging.getLogger("pandapower").setLevel(logging.WARNING)
    logging.getLogger("numexpr").setLevel(logging.WARNING)
