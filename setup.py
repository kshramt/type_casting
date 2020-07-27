import os

from setuptools import setup


def getversion():
    head = '__version__ = "'
    tail = '"\n'
    with open(os.path.join("type_casting", "__init__.py")) as fp:
        for l in fp:
            if l.startswith(head) and l.endswith(tail):
                return l[len(head) : -len(tail)]
    raise Exception("__version__ not found")


setup(
    name="type_casting",
    version=getversion(),
    description="Type Casting",
    url="https://github.com/kshramt/type_casting",
    author="kshramt",
    packages=["type_casting", "type_casting.py37", "type_casting.latest"],
    install_requires=[],
    extras_require=dict(dev=["pylint", "twine", "black"]),
    classifiers=["License :: OSI Approved :: GNU General Public License v3 (GPLv3)"],
    data_files=[(".", ["LICENSE.txt"])],
    zip_safe=True,
)
