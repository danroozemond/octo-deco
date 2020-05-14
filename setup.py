from Cython.Build import cythonize
from setuptools import setup, find_packages, Extension

#
# Note - can manually build like so:
# PycharmProjects\octo-deco>python setup.py build_ext --inplace
#

extensions = [ Extension("octodeco.deco.TissueStateCython", ["octodeco/deco/TissueStateCython.pyx"]) ];

setup(
    name="Octo-Deco",
    version="0.8.0",
    packages=find_packages(),
    author="Dan Roozemond",
    author_email="dan.roozemond@gmail.com",
    description="Package to do scuba diving decompression profile calculations, including web app",
    url="https://octo-deco.nl/",
    project_urls={
        "Source Code": "https://github.com/danroozemond/octo-deco/",
    },
    ext_modules = cythonize(extensions)
)
