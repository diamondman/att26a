#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
    setup.py
    ~~~~~~~~

    AT&T 26A Direct Extension Selector Console Graphical Simulator.

    :copyright: (c) 2019 by Jessy Diamond Exum.
    :license: see LICENSE for more details.
"""

import codecs
import os
import re

from setuptools import find_packages
from setuptools import setup

here = os.path.abspath(os.path.dirname(__file__))


def read(*parts):
    """Taken from pypa pip setup.py:
    intentionally *not* adding an encoding option to open, See:
       https://github.com/pypa/virtualenv/issues/201#issuecomment-3145690
    """
    return codecs.open(os.path.join(here, *parts), 'r').read()


def find_version(*file_paths):
    version_file = read(*file_paths)
    version_match = re.search(r"^__version__ = ['\"]([^'\"]*)['\"]",
                              version_file, re.M)
    if version_match:
        return version_match.group(1)
    raise RuntimeError("Unable to find version string.")

setup(
    name='att26aguisim',
    version=find_version("src", "att26aguisim", "__init__.py"),
    description='AT&T 26A Direct Extension Selector Console Graphical Simulator.',
    long_description=read('README.rst'),
    classifiers=[
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python :: 3 :: Only',
    ],
    author='Jessy Diamond Exum',
    author_email='jessy.diamondman@gmail.com',
    url='https://github.com/diamondman/att26a',
    packages=find_packages("src"),
    package_dir={"":"src"},
    include_package_data=True,
    entry_points = {
        'console_scripts': ['att26aguisim=att26aguisim:main'],
    },
    platforms='any',
    license='MIT',
    install_requires=[
        'virtualenv>=1.11.6',
        'pep8>=1.5.7',
        'pyflakes>=0.8.1',
        'att26a',
        'PyQt5>=5.12.3',
    ],
)
