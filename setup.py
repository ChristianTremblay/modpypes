#!/usr/bin/env python
# -*- coding: utf-8 -*-


try:
    from setuptools import setup
except ImportError:
    from distutils.core import setup


requirements = [
    'bacpypes'
]

test_requirements = [
    # TODO: put package test requirements here
]

setup(
    name='modpypes',
    version='0.4',
    description="Python library for MODBUS based on BACpypes",
    long_description="See GitHub for more information",
    author="Joel Bender",
    author_email='joel@carrickbender.com',
    url='https://github.com/JoelBender/modpypes',
    packages=[
        'modpypes',
    ],
    package_dir={'modpypes':
                 'modpypes'},
    include_package_data=True,
    install_requires=requirements,
    license="MIT",
    zip_safe=False,
    keywords='modpypes',
    classifiers=[
        'Development Status :: 2 - Pre-Alpha',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: BSD License',
        'Natural Language :: English',
        'Programming Language :: Python :: 2',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.4',
        'Topic :: Software Development :: Libraries :: Python Modules',
        'Topic :: System :: Networking',
        'Topic :: Utilities',
    ],
    test_suite='tests',
    tests_require=test_requirements
)
