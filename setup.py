import io
from setuptools import setup, find_packages


with io.open("README.rst") as readme_file:
    long_description = readme_file.read()


def test_suite():
    try:
        import unittest2 as unittest
    except:
        import unittest

    suite = unittest.TestLoader().discover("tests")
    return suite

setup(name='mapbox-vector-tile',
      version='0.1.0',
      description=u"Mapbox Vector Tile",
      long_description=long_description,
      classifiers=[],
      keywords='',
      author=u"Harish Krishna",
      author_email='harish.krsn@gmail.com',
      url='https://github.com/mapzen/mapbox-vector-tile',
      license='MIT',
      packages=find_packages(),
      include_package_data=True,
      zip_safe=False,
      test_suite="setup.test_suite",
      install_requires=["setuptools", "protobuf", "shapely"]
      )
