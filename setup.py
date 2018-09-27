from setuptools import setup, find_packages

import moonwalk

import os
import sys
from distutils.sysconfig import get_python_lib

NAME = 'moonwalk'

relative_site_packages = get_python_lib().split(sys.prefix+os.sep)[1]
rel_path = os.path.join(relative_site_packages, NAME)


def read(name):
    filename = os.path.join(os.path.dirname(__file__), name)
    with open(filename) as fp:
        return fp.read()


def requirements(name):
    install_requires = []
    dependency_links = []

    for line in read(name).split('\n'):
        if line.startswith('-e '):
            link = line[3:].strip()
            if link == '.':
                continue
            dependency_links.append(link)
            line = link.split('=')[1]
        line = line.strip()
        if line:
            install_requires.append(line)

    return install_requires, dependency_links


meta = dict(
    version=moonwalk.__version__,
    description=moonwalk.__doc__,
    name=NAME,
    packages=find_packages(exclude=['tests', 'tests.*']),
    install_requires=requirements('dev/requirements.txt')[0],
    data_files=[(rel_path, ['moonwalk/LendingBlockToken.json'])]
)


if __name__ == '__main__':
    setup(**meta)
