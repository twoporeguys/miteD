#!/usr/bin/env python3
from setuptools import setup, find_packages

setup(
    name='miteD',
    version='1.5.2',
    # packages=[
    #     'miteD',
    #     'miteD.middleware',
    #     'miteD.service',
    #     'validators'
    # ],
    packages=find_packages(exclude=['examples']),
    description='Api and service infrastructure library for X1 (based on sanic and nats)',
    url='https://github.com/twoporeguys/miteD/',
    keywords='miteD',
    python_requires='>=3.6',
    author='Harry Winters',
    author_email='harry.winters@twoporeguys.com',
    install_requires=[
        'requests==2.19.1',
        'sanic==0.7.0',
        'asyncio-nats-streaming==0.1.2',
        'schematics==2.0.1'
    ]
)
