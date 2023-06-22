from pathlib import Path

from setuptools import find_packages, setup  # type: ignore

setup(
    name="chatgpt",
    version="0.0.1",
    packages=find_packages(),
    python_requires=">=3.10",
)

