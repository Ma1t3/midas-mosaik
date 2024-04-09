"""This module contains the model for data simulators."""

import math

import numpy as np
from midas.util.compute_q import compute_q
from midas.util.base_data_model import DataModel


class BaseDataSpecificCosPhiModel(DataModel):
    """A model for a single load or sgen time series.

    There are a few assumptions for the time series that are not
    checked. First, the time series ranges over a whole year and
    secondly, the time passed between two values is 15 minutes.
    Therefore, not less than 35040 value are expected to be in each
    time series (for *data_p* and for *data_q*).

    However, the *DataModel* could be extended to support other timely
    resolutions and make use of data of a second (third, fourth,...)
    year.

    Parameters
    ----------
    data_p : pandas.DataFrame
        Contains values (either load or sgen) for active power. The
        index columns are simple *int*.
    data_q : pandas.DataFrame
        Contains values (either load or sgen) for reactive power. The
        index columns are simple *int*. If *None* is provided for
        *data_q*, the cos phi is used in each step to calculate a value
        for *q*.
    data_step_size: int
        Timely resolution of the data in seconds.
    scaling : float
        An overall scaling for this model. This scaling is applied in
        each to step both of *p* and *q*.
    cos_phi : float
    seed : int, optional
        A seed for the random number generator.
    interpolate : bool, optional
        If set to *True*, interpolation is applied when values between
        full 15-minute intervalls are requested.
    randomize_data : bool, optional
        If set to *True*, a normally distributed random noise is
        applied to all outputs.
    randomize_cos_phi : bool, optional
        If set to *True* and data_q is not provided, the cos phi for
        the calculation of *q* is randomized.
    date_index : bool, optional
        Set this to *True* if the has datetime as index instead of ints.
    noise_factor: float, optional
        Set this to increase or lower the noise if randomization is
        activated.

    Attributes
    ----------
    now_dt : datetime.datetime
        *now_dt is an input and needs to be provided in each step.*
        The current simulated time. Is used to calculate the index for
        the current value in the time series.
    cos_phi : float
        *cos_phi is an input and needs to be provided in each step.*
        The phase angle used to calculate reactive power if no reactive
        power time series is provided.
    p_mw : float
        *p_mw is an output.* The active power for the current step.
    q_mvar : float
        *q_mvar is an output.* The reactive power for the current step.

    """

    def __init__(
        self, data_p, data_q, data_step_size, eid_cos_phi, scaling, **params
    ):
        self.data_p = data_p
        self.data_q = data_q
        self.sps = data_step_size
        self.scaling = scaling
        self.date_index = params.get("date_index", False)

        # RNG
        self.seed = params.get("seed", None)
        self.rng = np.random.RandomState(self.seed)

        self.interpolate = params.get("interpolate", False)
        self.randomize_data = params.get("randomize_data", False)
        self.randomize_cos_phi = params.get("randomize_cos_phi", False)
        self.noise_factor = params.get("noise_factor", 0.2)
        self.p_std = self.data_p.std() * self.scaling
        self.p_mwh_per_a = self.data_p.sum() * self.scaling / self.sps * 3_600
        if self.data_q is not None:
            self.q_std = self.data_q.std() * self.scaling
        else:
            self.q_std = None
        self.eid_cos_phi = eid_cos_phi

        # Inputs
        self.cos_phi = None
        self.now_dt = None

        # Outputs
        self.p_mw = None
        self.q_mvar = None

    def step(self):
        """Perform a simulation step."""

        self.p_mw = None
        self.q_mvar = None

        super()._interpolation()
        super()._randomization()

        self._random_cos_phi()

        if self.q_mvar is None:
            self.q_mvar = compute_q(self.p_mw, self.eid_cos_phi)

        # Numpy multiply failes for int and float if *= is used
        self.p_mw = self.p_mw * self.scaling
        self.q_mvar = self.q_mvar * self.scaling
