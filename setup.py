#!/usr/bin/env python3
import os
from setuptools import setup, find_packages

requirements = []
with open('requirements.txt') as f:
    requirements = f.read().splitlines()

setup(
    name='miteD',
    version='2.1.1',
    packages=find_packages(exclude=['examples']),
    description='Api and service infrastructure library for X1 (based on sanic and nats)',
    url='https://github.com/twoporeguys/miteD/',
    keywords='miteD',
    python_requires='>=3.6',
    author='Harry Winters',
    author_email='harry.winters@twoporeguys.com',
    install_requires=requirements
)
