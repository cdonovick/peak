from setuptools import setup, find_packages
import sys

setup(
    name='peak',
    version='0.0.1',
    url='https://github.com/phanrahan/peak',
    license='MIT',
    maintainer='Pat Hanrahan',
    maintainer_email='hanrahan@cs.stanford.edu',
    description='A DSL for Specifying Processors',
    packages=find_packages(),
    install_requires=[
        "hwtypes >= 1.4.0",
        "astor",
        "pysmt",
        "magma-lang",
        "coreir",
        "ast-tools",
    ],
    python_requires='>=3.7'
)
