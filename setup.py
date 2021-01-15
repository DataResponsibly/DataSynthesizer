#!/usr/bin/env python

"""The setup script."""

import pathlib

from setuptools import setup, find_packages

# The directory containing this file
HERE = pathlib.Path(__file__).parent.absolute()

with open(HERE / 'README.md') as readme_file:
    readme = readme_file.read()

with open(HERE / 'HISTORY.md') as history_file:
    history = history_file.read()

requirements = [
    "numpy>=1.18.5",
    "pandas>=1.0.5",
    "scikit-learn>=0.23.1",
    "matplotlib>=3.2.2",
    "seaborn>=0.10.1",
    "python-dateutil>=2.8.1"
]

setup_requirements = ['pytest-runner', ]

test_requirements = ['pytest>=5', ]

setup(
    author="Data, Responsibly",
    author_email='dataresponsibly@gmail.com',
    python_requires='>=3.8',
    classifiers=[
        'Development Status :: 2 - Pre-Alpha',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Natural Language :: English',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.8'
    ],
    description="Generate synthetic data that simulate a given dataset.",
    install_requires=requirements,
    license="MIT license",
    long_description=readme + '\n\n' + history,
    long_description_content_type='text/markdown',
    include_package_data=True,
    keywords='DataSynthesizer',
    name='DataSynthesizer',
    packages=find_packages(include=['DataSynthesizer', 'DataSynthesizer.*']),
    setup_requires=setup_requirements,
    test_suite='tests',
    tests_require=test_requirements,
    url='https://github.com/DataResponsibly/DataSynthesizer',
    version='0.1.4',
    zip_safe=False,
)
