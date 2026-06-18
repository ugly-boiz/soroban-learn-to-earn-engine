from setuptools import setup, find_packages

setup(
    name="consparse",
    version="0.1.0",
    packages=find_packages(exclude=("tests",)),
    install_requires=[
        "torch>=1.12",
        "pyyaml",
        "numpy",
    ],
)
