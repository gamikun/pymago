from __future__ import absolute_import
from os.path import join, dirname
from setuptools import setup
import pymago

basepath = dirname(__file__)
binpath = join(basepath, 'bin')

setup(
  name = 'pymago',
  packages = ['pymago', 'pymago.programs'],
  version = pymago.version,
  description = 'CLI Tool for optimizing folder of images',
  #long_description = open(join(basepath, 'README.txt')).read(),
  scripts = [join(binpath, 'pymago'), join(binpath, 'mago')],
  install_requires=[],
  author = 'Gamaliel Espinoza M.',
  author_email = 'gamaliel.espinoza@gmail.com',
  url = 'https://github.com/gamikun/pymago',
  keywords = ['magick', 'optimizer', 'image', 'pngquant'],
  classifiers = [],
)
