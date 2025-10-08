from setuptools import setup, find_packages

setup(
    name="life_simulator_server",
    version="1.0.0",
    packages=find_packages(),
    install_requires=[
        'fastapi',
        'pydantic'
    ],
    package_dir={'': '..'}
)