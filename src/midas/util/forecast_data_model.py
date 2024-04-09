"""This module contains the model for data simulators."""

from datetime import timedelta

import numpy as np
from midas.util.compute_q import compute_q


class ForecastDataModel:
    """A model for a forecast of a single load or sgen time series.

    This model can be used to "simulate" the forecast of a time series
    of active and, if provided, reactive power values. The model is
    designed to simulate one year but the time resolution of the data needs
    to be specified. This time resolution can be different than the step
    size for one step but if the step size is lower, values will be
    returned repeatedly.

    If that behavior is not desired, the linear interpolation function
    of the model can be used (not yet supported).This can also be combined
    with the randomization function.
    Those can be activated by passing the corresponding flags (see Parameter section).

    If the data does not contain a reactive power time series, the
    model will calculate reactive power based on the cos phi, which
    should be provided before each step. There is an option to
    randomize the output of the cos phi calculation as well.

    The main input for the model is a datetime object for the time to
    be simulated. Month, day, hour, minute, and second will be used to
    determine the corresponding value of the data set. Year information
    will be dropped.

    This has two consequences. First, the model can be used to simulate
    several years and, secondly, the data set needs to be exactly for
    one year. Larger data sets will be "cropped" to one year and
    smaller data sets will probably lead to an error.

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
    seed : int, optional
        A seed for the random number generator.
    interpolate : bool, optional (not yet supported)
        If set to *True*, interpolation is applied when values between
        full 15-minute intervalls are requested.
    randomize_data : bool, optional
        If set to *True*, a normally distributed random noise is
        applied to all outputs.
    randomize_cos_phi : bool, optional (not yet supported)
        If set to *True* and data_q is not provided, the cos phi for
        the calculation of *q* is randomized.
    horizon_hours: float, optional
        Defines for how much into the future, the forecast is given.
        Default: 1 hour.
    date_index : bool, optional
        Set this to *True* if the data has datetime as index instead of
        ints (planned but not yet supported).
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
        The phase angle is used to calculate reactive power if no reactive
        power time series is provided.
    p_mw : float
        *p_mw is an output.* The active power for the current step.
    q_mvar : float
        *q_mvar is an output.* The reactive power for the current step.

    """

    def __init__(self, data_p, data_q, data_step_size, scaling, **params):
        self.data_p = data_p
        self.data_q = data_q
        self.sps = data_step_size
        self.scaling = scaling
        horizon_hours = params.get("forecast_horizon_hours", 1.0)
        self.horizon_hours = int(horizon_hours)
        self.horizon_minutes = int(60 * (horizon_hours - self.horizon_hours))
        self.horizon_seconds = int(
            3600
            * (horizon_hours - self.horizon_hours - self.horizon_minutes / 60)
        )
        self.date_index = params.get("date_index", False)

        # RNG
        self.seed = params.get("seed", None)
        self.rng = np.random.RandomState(self.seed)

        self.interpolate = params.get("interpolate", False)
        self.randomize_data = params.get("randomize_data", False)
        self.randomize_cos_phi = params.get("randomize_cos_phi", False)
        self.noise_factor = params.get("noise_factor", 0.2)
        self.p_std = self.data_p.std() * self.scaling
        self.p_mw_forecasth_per_a = (
            self.data_p.sum() * self.scaling / self.sps * 3_600
        )
        if self.data_q is not None:
            self.q_std = self.data_q.std() * self.scaling
        else:
            self.q_std = None

        # Inputs
        self.now_dt = None
        self.cos_phi = None

        # Outputs
        self.p_mw_forecast = None
        self.q_mvar_forecast = None

    def step(self):
        """Perform a simulation step."""

        self.p_mw_forecast = []
        self.q_mvar_forecast = []

        self._interpolation()
        self._randomization()

        self._random_cos_phi()
        q_mvar_from_cos_phi = False

        for tidx in range(len(self.p_mw_forecast)):
            if len(self.q_mvar_forecast) == 0 or q_mvar_from_cos_phi:
                q_mvar_from_cos_phi = True
                self.q_mvar_forecast.append(
                    compute_q(self.p_mw_forecast[tidx], self.cos_phi)
                )

            # Numpy multiply failes for int and float if *= is used
            self.p_mw_forecast[tidx] = self.p_mw_forecast[tidx] * self.scaling
            self.q_mvar_forecast[tidx] = (
                self.q_mvar_forecast[tidx] * self.scaling
            )

            # tmp = self.p_mw_forecast[tidx]**2 + self.q_mvar_forecast[tidx]**2
            # if tmp != 0:
            #     self.cos_phi = self.p_mw_forecast[tidx] / math.sqrt(tmp)
            # else:
            #     self.cos_phi = 0

    def _interpolation(self):
        # index from now_dt
        tidx_start = self._time_index_from_dt(self.now_dt)
        # add forecast horizon to now_dt
        end_dt = self.now_dt + timedelta(
            hours=self.horizon_hours,
            minutes=self.horizon_minutes,
            seconds=self.horizon_seconds,
        )
        # index from end_dt
        tidx_end = self._time_index_from_dt(end_dt)

        # Apply interpolation
        if self.interpolate:
            raise NotImplementedError
        else:
            # get values from self.data_p/.data_q
            # within yearly data
            if tidx_start < tidx_end:
                self.p_mw_forecast = list(
                    self.data_p.values[tidx_start:tidx_end]
                )
                if self.data_q is not None:
                    self.q_mvar_forecast = list(
                        self.data_q.values[tidx_start:tidx_end]
                    )
            # across end/start of yearly data
            else:
                p_mw1 = list(self.data_p.values[tidx_start:])
                p_mw2 = list(self.data_p.values[:tidx_end])
                self.p_mw_forecast = p_mw1 + p_mw2
                if self.data_q is not None:
                    q_mvar1 = list(self.data_p.values[tidx_start:])
                    q_mvar2 = list(self.data_p.values[:tidx_end])
                    self.q_mvar_forecast = q_mvar1 + q_mvar2

    def _time_index_from_dt(self, dt):
        # We assume that the dataset starts on the first of the year.
        dif = dt - dt.replace(month=1, day=1, hour=0, minute=0, second=0)
        dif_s = dif.total_seconds()

        tidx = int(dif_s // self.sps) % len(
            self.data_p.index
        )  # step size of the data
        return tidx

    def _interpolate(self, tidx, data):

        raise NotImplementedError

    def _randomization(self):
        # Not yet debugged
        if self.randomize_data:
            for tidx in range(len(self.p_mw_forecast)):
                noise = self.rng.normal(
                    scale=(self.p_std * self.noise_factor), loc=0.0
                )
                self.p_mw_forecast[tidx] = max(
                    0, self.p_mw_forecast[tidx] + noise
                )

                if self.q_mvar_forecast is not None:
                    noise = self.rng.normal(
                        scale=(self.q_std * self.noise_factor), loc=0.0
                    )
                    self.q_mvar_forecast[tidx] = max(
                        0, self.q_mvar_forecast[tidx] + noise
                    )

    def _random_cos_phi(self):
        if len(self.q_mvar_forecast) == 0 and self.randomize_cos_phi:
            self.cos_phi = max(
                0, min(1.0, self.rng.normal(scale=0.02, loc=0.9))
            )
