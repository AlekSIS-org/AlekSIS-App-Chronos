#!/usr/bin/env python3

from setuptools import setup

setup(
    name='BiscuIT-App-Chronos',
    version='1.0dev0',
    url='https://edugit.org/Teckids/BiscuIT/BiscuIT-App-Chronos',
    author="Teckids e.V.",
    author_email="verein@teckids.org",
    packages=[
        'biscuit.apps.chronos'
    ],
    namespace_packages=[
        'biscuit',
        'biscuit.apps'
    ],
    include_package_data=True,
    install_requires=[
        'BiscuIT-ng'
    ],
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Environment :: Web Environment",
        "Intended Audience :: Education",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Topic :: Education",
    ],
)
