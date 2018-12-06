#!/usr/bin/env python3
from setuptools import setup, find_packages

setup(
    name='miteD',
    version='2.1.4',
    packages=find_packages(exclude=['examples']),
    description='Api and service infrastructure library for X1 (based on sanic and nats)',
    url='https://github.com/twoporeguys/miteD/',
    keywords='miteD',
    python_requires='>=3.6',
    author='Harry Winters',
    author_email='harry.winters@twoporeguys.com',
    install_requires=[
        'requests==2.20.1',
        'sanic==0.8.3',
        'asyncio-nats-streaming==0.1.2'
    ]
)
