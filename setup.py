from setuptools import setup, find_packages

with open("README.md", encoding="utf-8") as f:
    LONG_DESCRIPTION = f.read()

setup(
    name="parton",
    version="0.2",
    author="David M. Straub",
    author_email="david.straub@tum.de",
    description="Python package for parton distributions and parton luminosities",
    long_description=LONG_DESCRIPTION,
    long_description_content_type="text/markdown",
    license="MIT",
    packages=find_packages(),
    install_requires=["numpy", "scipy", "setuptools", "pyyaml", "appdirs"],
)
