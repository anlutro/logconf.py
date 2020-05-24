#!/usr/bin/env python

import os
import setuptools

# allow setup.py to be ran from anywhere
os.chdir(os.path.dirname(os.path.abspath(__file__)))

setuptools.setup(
    name="logconf",
    version="0.2.2",
    license="MIT",
    description="convenient python stdlib logging configuration",
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",
    author="Andreas Lutro",
    author_email="anlutro@gmail.com",
    url="https://github.com/anlutro/logconf.py",
    packages=setuptools.find_packages(include=("logconf", "logconf.*")),
)
