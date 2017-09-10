from os.path import join, dirname
from setuptools import setup

setup(
  name = 'pymago',
  packages = ['pymago'], # this must be the same as the name above
  version = '0.1a3',
  description = 'CLI Tool for optimizing folder of images',
  long_description = open(join(dirname(__file__), 'README.txt')).read(),
  install_requires=[],
  author = 'Gamaliel Espinoza M.',
  author_email = 'gamaliel.espinoza@gmail.com',
  url = 'https://github.com/gamikun/pymago',
  keywords = ['magick', 'optimizer', 'image'], # arbitrary keywords
  classifiers = [],
)
