# MIDAS

The MultI-DomAin test Scenario (MIDAS) is a collection of mosaik simulators
(https://gitlab.com/mosaik) for smart grid co-simulation and contains a 
semi-automatic scenario configuration tool.

Version: 0.4.0

License: LGPL

## Installation

Midas requires Python >= 3.8 and is available on https://pypi.org. It can be
installed, preferably into a virtualenv,  with

    >>> pip install midas-mosaik

Alternatively, you can clone this repository with

    >>> git clone https://gitlab.com/midas-mosaik/midas.git 

then switch to the midas folder and type

    >>> pip install -e .

To start the final configration, type

    >>> midascli

which downloads the necessary datasets.


## Requirements


The main requirements for midas are the co-simulation framework mosaik
and pandapower. Optional requirements are listed in the requirements.txt file.


## Documentation

A more comprehensive documentation is growing in the docs folder. 
To build the docu, sphinx (*pip install sphinx*) is required. Simply navigate
into the docs folder and type 

    >>> make html

Afterwards, navigate inside the docs/_build/html folder and double-click on the 
index.html file.


## Datasets

TODO: Add license information

