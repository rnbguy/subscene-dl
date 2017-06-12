from setuptools import setup

import os

def requirements():
  if os.path.isfile('requirements.txt'):
    with open('requirements.txt') as f:
      return f.read().splitlines()
  else:
    return []

def readme():
  if os.path.isfile('README.md'):
    with open('README.md') as f:
      return f.read()
  else:
    return ''

setup(
  name='subscene-dl',
  version='0.1',
  description='Download subtitles from subscene.com',
  long_description=readme(),
  url='https://github.com/rnbdev/subscene-dl',
  author='Ranadeep Biswas',
  author_email='ranadip.bswas@gmail.com',
  packages=['subscene'],
  install_requires=requirements(),
  entry_points={
    'console_scripts': ['subscene=subscene:command_line']
  },
  include_package_data=True
)