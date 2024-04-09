#!/usr/bin/env python3
"""Setup file for the midas package."""
import os
import setuptools


with open("VERSION") as freader:
    VERSION = freader.readline().strip()


with open("README.md") as freader:
    README = freader.read()


setuptools.setup(
    name="midas-mosaik",
    version=VERSION,
    author="Stephan Balduin",
    author_email="stephan.balduin@offis.de",
    description="MultI-DomAin test Scenario for smart grid co-simulation.",
    long_description=README,
    long_description_content_type="text/markdown",
    url="https://gitlab.com/midas-mosaik/midas",
    packages=setuptools.find_packages(where="src"),
    package_dir={"": "src"},
    include_package_data=True,
    install_requires=[
        "click",
        "matplotlib",  # required by pandapower
        "mosaik==3.0.2",
        "mosaik-hdf5",
        "numpy>=1.22.0",  # 1.19.4 has a windows bug
        "pandapower==2.9.0",
        "pysimmods",
        "ruamel.yaml",
        "simbench",
        "sortedcontainers",
        "tables",
        "wget",
        "natsort",
    ],
    entry_points="""
        [console_scripts]
        midascli=midas.cli.cli:cli
        midasctl=midas.cli.cli2:cli
    """,
    license="LGPL",
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Science/Research",
        "License :: OSI Approved :: "
        "GNU Lesser General Public License v2 (LGPLv2)",
        "Natural Language :: English",
        "Operating System :: OS Independent",
        "Programming Language :: Python",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Topic :: Scientific/Engineering",
        "Topic :: Software Development :: Libraries :: Python Modules",
    ],
    python_requires=">=3.8",
)
