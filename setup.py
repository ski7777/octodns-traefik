#!/usr/bin/env python

import setuptools

setuptools.setup(
    name='octodns-traefik',
    version='1.0.0',
    description='Octodns provider for traefik',
    url='http://github.com/ski7777/octodns-traefik',
    author='Raphael Jacob',
    author_email='r.jacob2002@gmail.com',
    license='GPLv3',
    py_modules=["octodns_traefik"],
    install_requires=[
        'octodns>=0.9.21',
        'traefik>=1.10.0'
    ]
)