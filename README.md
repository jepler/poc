# poc: Python OCE Composer

[![Documentation Status](https://readthedocs.org/projects/python-poc/badge/?version=latest)](http://python-poc.readthedocs.io/en/latest/?badge=latest)

*poc* is a tool in the vein of *OpenSCAD* for creating 3D models in a high
level language with a minimum of boilerplate.

*poc* programs are Python2 programs, executed in an environment that
provides convenient shorthand for performing geometric operations.

Python2 is used instead of Python3 because a python3 compatible version of
vtk is not availble in debian stretch.  However, the python3-like features of
`print_function` and `division` are automatically enabled.

*poc* uses OpenCASCADE (via pythonocc-core) to implement its geometric
operations.  This means it has different strengths and weaknesses compared to
*OpenSCAD*, which uses CGAL.  For instance, OpenCASCADE has `fillet` as a
first-class operation, while it lacks `minkowski` and `hull` which are quite
frequently used in *OpenSCAD*.

![pocview showing selective fillet of CSG object](/images/selective_fillet.png)

# Setup
* Install dependencies
* Run setup, e.g., `sudo python setup.py install`
* Invoke `pocview somefile.poc` to lanuch a viewer.  It autoupdates if you modify the input file.
* Invoke `poc somefile.poc` to create `somefile.stl`
* or use `#!/usr/bin/env poc` so that `./somefile.poc` is executable

# Dependencies

* [OpenCASCADE Community Edition (OCE)](https://github.com/tpaviot/oce/pulls)
* pythonocc-core
* python-vtk6

# Stability

The the design of the *poc* standard library is very much in flux, and
there are likely to be compatibility-breaking changes as it develops.
