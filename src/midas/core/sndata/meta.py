"""This module contains the meta for the household data simulator.

Eight 'low voltage lands' are present in the data with different
number of households. They are distributed as following:
    #name   #num        #house ids      #annual con #avg con
    Land 0:  41 houses (hids   0 -  40) (130 MWh/a) (0.36 kW)
    Land 1: 139 houses (hids  41 - 179) (661 MWh/a) (0.54 kW)
    Land 2:  67 houses (hids 180 - 246) (323 MWh/a) (0.55 kW)
    Land 3:  57 houses (hids 247 - 303) (223 MWh/a) (0.45 kW)
    Land 4: 169 houses (hids 304 - 472) (741 MWh/a) (0.5 kW)
    Land 5: 299 houses (hids 473 - 771) (1377 MWh/a) (0.53 kW)
    Land 6:  66 houses (hids 772 - 837) (309 MWh/a) (0.54 kW)
    Land 7: 103 houses (hids 838 - 940) (421 MWh/a) (0.47 kW)

Resulting in 941 households or 8 lands in total.

"""

INFO = {
    "Land0": {
        "num_houses": 41,
        "first_hid": 0,
        "last_hid": 40,
        "p_mwh_per_a": 130,
        "average_consumption": 0.00036,
    },
    "Land1": {
        "num_houses": 139,
        "first_hid": 41,
        "last_hid": 179,
        "p_mwh_per_a": 661,
        "average_consumption": 0.00054,
    },
    "Land2": {
        "num_houses": 67,
        "first_hid": 180,
        "last_hid": 246,
        "p_mwh_per_a": 323,
        "average_consumption": 0.00055,
    },
    "Land3": {
        "num_houses": 57,
        "first_hid": 247,
        "last_hid": 303,
        "p_mwh_per_a": 223,
        "average_consumption": 0.00045,
    },
    "Land4": {
        "num_houses": 169,
        "first_hid": 304,
        "last_hid": 472,
        "p_mwh_per_a": 741,
        "average_consumption": 0.0005,
    },
    "Land5": {
        "num_houses": 299,
        "first_hid": 473,
        "last_hid": 771,
        "p_mwh_per_a": 1377,
        "average_consumption": 0.00053,
    },
    "Land6": {
        "num_houses": 66,
        "first_hid": 772,
        "last_hid": 837,
        "p_mwh_per_a": 309,
        "average_consumption": 0.00054,
    },
    "Land7": {
        "num_houses": 103,
        "first_hid": 838,
        "last_hid": 940,
        "p_mwh_per_a": 421,
        "average_consumption": 0.00047,
    },
}

META = {
    "type": "time-based",
    "models": {
        "Household": {
            "public": True,
            "params": [
                "scaling",
                "eidx",
                "interpolate",
                "randomize_data",
                "randomize_cos_phi",
            ],
            "attrs": ["cos_phi", "p_mw", "q_mvar"],
        },
        "Land": {
            "public": True,
            "params": [
                "scaling",
                "eidx",
                "interpolate",
                "randomize_data",
                "randomize_cos_phi",
            ],
            "attrs": ["cos_phi", "p_mw", "q_mvar"],
        },
    },
    "extra_methods": ["get_data_info"],
}
