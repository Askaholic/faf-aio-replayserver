from setuptools import find_packages, setup

with open('requirements/main.txt') as f:
    install_reqs = f.read().splitlines()

long_desc = """
This is a prototype for the new FAF replay server. It uses asyncio a lot and
hopefully is better designed than the old replay server.
"""


setup(
    name="faf_replay_server",
    version=open('VERSION').read().strip(),
    description="FAF replay server using asyncio",
    long_description=long_desc,
    classifiers=[
        "Programming Language :: Python",
        "Programming Language :: Python :: 3.6",
    ],
    author="Igor Kotrasiński, Konstantin Kalinovsky",
    author_email="i.kotrasinsk@gmail.com",
    url="https://github.com/FAForever/faf-aio-replayserver",
    keywords="FAForever replay server",
    license="GPL3",
    packages=find_packages(exclude=["tests", "tests.*"]),
    entry_points={
        "console_scripts": [
            "faf_replay_server = replayserver.main:main",
        ],
    },
    install_requires=install_reqs
)
