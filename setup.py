import os
from setuptools import setup, find_packages

import moonwalk

NAME = 'moonwalk'


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
    include_package_data=True
)


if __name__ == '__main__':
    setup(**meta)
