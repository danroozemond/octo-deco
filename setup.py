from Cython.Build import cythonize
from setuptools import setup, find_packages, Extension

#
# Note - can manually build like so:
# PycharmProjects\octo-deco>python setup.py build_ext --inplace
#

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

extensions = [ Extension(name="octodeco.deco.TissueStateCython",
                         sources=["octodeco/deco/TissueStateCython.pyx"]) ];

setup(
    name="octo-deco",
    version="2.0.3",
    packages=find_packages(),
    author="Dan Roozemond",
    author_email="dan.roozemond@gmail.com",
    description="Package to do scuba diving decompression profile calculations, including web app",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://octo-deco.nl/",
    project_urls={
        "Source Code": "https://github.com/danroozemond/octo-deco/",
    },
    ext_modules = cythonize(extensions, language_level = "3")
)
