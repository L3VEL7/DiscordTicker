from setuptools import setup, find_packages

setup(
    name="price_tracking_agency",
    version="0.1",
    packages=find_packages(),
    install_requires=[
        'agency-swarm',
        'discord.py',
        'web3',
        'requests',
        'python-dotenv'
    ],
) 