#!/usr/bin/env python
# -*- coding: utf-8 -*-

from setuptools import setup
from setuptools.command.test import test as TestCommand
import os
import sys


name = 'betty-cropper'
package = 'betty'
description = "A django-powered image server"
url = "https://github.com/theonion/betty-cropper"
author = "Chris Sinchok"
author_email = 'csinchok@theonion.com'
license = 'MIT'

setup_requires = []

if 'test' in sys.argv:
    setup_requires.append('pytest')


tests_require = [
    "flake8>=2.0,<2.1",
    "pytest",
    "pytest-django",
    "pytest-cov>=1.4",
    "python-coveralls"
]


install_requires = [
    "Django>=1.5",
    "slimit==0.8.1",
    "wand==0.3.5",
    "South==0.8.4",
    "logan==0.5.9.1"
]


def get_packages(package):
    """
    Return root package and all sub-packages.
    """
    return [dirpath
            for dirpath, dirnames, filenames in os.walk(package)
            if os.path.exists(os.path.join(dirpath, '__init__.py'))]


def get_package_data(package):
    """
    Return all files under the root package, that are not in a
    package themselves.
    """
    walk = [(dirpath.replace(package + os.sep, '', 1), filenames)
            for dirpath, dirnames, filenames in os.walk(package)
            if not os.path.exists(os.path.join(dirpath, '__init__.py'))]

    filepaths = []
    for base, filenames in walk:
        filepaths.extend([os.path.join(base, filename)
                          for filename in filenames])
    return {package: filepaths}


class PyTest(TestCommand):
    def finalize_options(self):
        TestCommand.finalize_options(self)
        self.test_args = ['tests']
        self.test_suite = True

    def run_tests(self):
        #import here, cause outside the eggs aren't loaded
        import pytest
        errno = pytest.main(self.test_args)
        sys.exit(errno)


setup(
    name=name,
    version="0.1",
    url=url,
    license=license,
    description=description,
    author=author,
    author_email=author_email,
    packages=get_packages(package),
    package_data={
        "betty/templates": ["betty/templates/image.js.j2"]
    },
    install_requires=install_requires,
    tests_require=tests_require,
    extras_require={
        'tests': tests_require,
    },
    entry_points={
        "console_scripts": [
            "betty-cropper = betty.server.utils.runner:main",
        ],
    },
    cmdclass={'test': PyTest}
)
