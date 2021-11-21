from Cython.Build import cythonize
from setuptools import setup, find_packages, Extension

# Note: the packaged version only contains the octo-deco.deco library.
# The flaskr/db are excluded; recommended use is to get the source
# code and use docker to run those.
# This is reflected in this file, and in MANIFEST.in.
# In particular, install_requires contains only what's needed for
# octodeco.deco, not flaskr etc


with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

extensions = [ Extension(name="octodeco.deco.TissueStateCython",
                         sources=["octodeco/deco/TissueStateCython.pyx"]) ];

setup(
    name="octo-deco",
    version="2.0.4",
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
    install_requires=['pandas', ' numpy', 'cython'],
    ext_modules = cythonize(extensions, language_level = "3")
)
