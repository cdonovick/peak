from setuptools import setup, find_namespace_packages
import sys

setup(
    name='peak',
    version='0.0.1',
    url='https://github.com/cdonovick/peak',
    license='MIT',
    maintainer='Caleb Donovick',
    maintainer_email='donovick@cs.stanford.edu',
    description='A DSL for Specifying Processors',
    packages=find_namespace_packages(include=['peak', 'peak.*']),
    install_requires=[
        "hwtypes >= 1.4.1",
        "astor",
        "pysmt",
        "magma-lang >= 2.1.28",
        "coreir",
        "ast-tools >= 0.1.3",
    ],
    python_requires='>=3.7'
)
