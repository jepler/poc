#!/usr/bin/env python3

from distutils.core import setup


setup(name='poc',
      version='0.1',
      description='Python OpenCASCADE Composer',
      author='Jeff Epler',
      author_email='jepler@gmail.com',
      url='https://github.com/jepler/poc',
      py_modules=['poctools'],
      scripts=['poc', 'pocview'],
     )
