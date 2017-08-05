# poc: Python OCE Composer

*poc* is a tool in the vein of *OpenSCAD* for creating 3D models in a high
level language with a minimum of boilerplate.

## Comparison of poc and OpenSCAD

*poc* uses OpenCASCADE (via occmodel) to implement its geometric operations.
This means it has different strengths and weaknesses compared to *OpenSCAD*,
which uses CGAL.  For instance, OpenCASCADE has `fillet` as a first-class
operation, while it lacks `minkowski` and `hull` which are quite frequently
used in *OpenSCAD*.

*poc* does not presently support a live interactive preview like *OpenSCAD*,
and its design means that quick display of the result of CSG operations via
`libopencsg` will not be possible.

# Setup
* Install dependencies
* Run setup, e.g., `sudo python setup.py install`
* Invoke `poc somefile.poc` to create `somefile.stl`
* or use `#!/usr/bin/env poc` so that `./somefile.poc` is executable

# Dependencies

* OpenCASCADE Community Edition (OCE)
* occmodel
* geotools

# poc syntax

*poc* programs are Python (2.x) programs.  Primitives, postfix operations,
and group operations are generally shorthand ways for invoking methods on
occmodel *Solid* objects.

## Primitives

Primitives include `Box()` and `Cylinder()`.  For example, to create a
100x100x100 box centered around the origin,

~~~~
Box((-50,-50,-50), (50,50,50))
~~~~

## Group operations

Group operations include `with Intersection():`, `with Difference():`,
and `with Union():`.

For example, to cut a cylinder out of a cube,

~~~~
with Difference():
    Box((-50,-50,-50), (50,50,50))
    Cylinder((0,0,0), (0,0,100), 35))
~~~~

## Postfix operations

Postfix operations include `Fillet()` and `Rotate()`.  They operate on
the whole group operation performed up to now.  For example, to fillet a
cylinder,

~~~~
Cylinder((0,0,0), (0,0,100), 35))
Fillet(8)
~~~~

Some postfix operations are available as group operations (e.g.,
postfix `Fillet` is group operation `Filleted`); other postfix
operations can be converted to group operations with group operation
`Op()`.
