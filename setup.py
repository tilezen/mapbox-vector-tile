from setuptools import find_packages, setup

with open("README.md") as readme_file:
    long_description = readme_file.read()


def test_suite():
    try:
        import unittest2 as unittest
    except Exception:
        import unittest

    suite = unittest.TestLoader().discover("tests")
    return suite


setup(
    name="mapbox-vector-tile",
    version="1.2.1",
    description="Mapbox Vector Tile",
    long_description=long_description,
    classifiers=[
        "Programming Language :: Python :: 3.5",
    ],
    keywords="",
    author="Rob Marianski",
    long_description_content_type="text/markdown",
    author_email="hello@mapzen.com",
    url="https://github.com/tilezen/mapbox-vector-tile",
    license="MIT",
    packages=find_packages(),
    include_package_data=True,
    zip_safe=False,
    test_suite="setup.test_suite",
    install_requires=[
        "setuptools",
        "protobuf<4.20",
        "shapely<2; python_version<'3.8'",
        "shapely; python_version>='3.8'",
        "future",
        "pyclipper",
    ],
)
