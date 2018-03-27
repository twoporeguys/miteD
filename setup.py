from distutils.core import setup
setup(name='miteD',
      version='1.0.0',
      packages=['miteD'],
      install_requires=[
          'sanic==0.7.0',
          'asyncio-nats-streaming==0.1.2'
      ])
