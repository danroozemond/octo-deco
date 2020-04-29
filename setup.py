from Cython.Build import cythonize
from setuptools import setup, find_packages

setup(
    name="Octo-Deco",
    version="0.5.0",
    packages=find_packages(),
    author="Dan Roozemond",
    author_email="dan.roozemond@gmail.com",
    description="Package to do scuba diving decompression profile calculations, including web app",
    url="https://octo-deco.nl/",
    project_urls={
        "Source Code": "https://github.com/danroozemond/octo-deco/",
    },
    ext_modules=cythonize("octodeco/deco/TissueStateClassic.py")
)
