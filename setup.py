import io
from codecs import open as codecs_open
from setuptools import setup, find_packages


# Get the long description from the relevant file
# with codecs_open('README.md', encoding='utf-8') as f:
#     long_description = f.read()
with io.open("README.rst") as readme_file:
    long_description = readme_file.read()

def test_suite():
    import doctest
    try:
        import unittest2 as unittest
    except:
        import unittest

    suite = unittest.TestLoader().discover("tests")
    # suite.addTest(doctest.DocFileSuite("README.rst"))
    return suite

setup(name='mapbox-vector-tile',
      version='0.0.8',
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
