import setuptools

from distutils.core import setup

setup(name='miteD',
      version='1.3.2',
      packages=[
          'miteD',
          'miteD.middleware',
          'miteD.service',
          'validators'
      ],
      install_requires=[
          'sanic==0.7.0',
          'asyncio-nats-streaming==0.1.2',
          'schematics==2.0.1'
      ])
