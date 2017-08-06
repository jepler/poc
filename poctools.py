#! python -*- coding: utf-8 -*-
#   primitives for 'poc' modeling program

#   Copyright © 2017 Jeff Epler <jepler@gmail.com>
#
#   This program is free software: you can redistribute it and/or modify
#   it under the terms of the GNU General Public License as published by
#   the Free Software Foundation, either version 3 of the License, or
#   (at your option) any later version.
#
#   This program is distributed in the hope that it will be useful,
#   but WITHOUT ANY WARRANTY; without even the implied warranty of
#   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#   GNU General Public License for more details.
#
#   You should have received a copy of the GNU General Public License
#   along with this program.  If not, see <http://www.gnu.org/licenses/>.

import contextlib
import __future__
import itertools
import occmodel
import os
import six
import struct
import sys

__all__ = [
    'Box', 'Cylinder',
    'Fillet', 'Rotate',
    'Filleted', 'Rotated',
    'Intersection', 'Difference', 'Union', 'Op',
    'Object', 'Bbox', 'Edges', 'Faces', 'Vertices', 'Wires',
    'execpoc', 'occ_to_stl', 'do_op',
]

### Supporting routines
def initial_ns():
    ns = {
        '__builtins__': __builtins__,
        '__name__': '__main__',
        '__doc__': None,
        '__package__': None
    }
    six.exec_("""if 1:
        from math import *
        from geotools import *
        from occmodel import *
        from poctools import *
        import poctools as _poctools
        """,  ns)
    return ns

compile_flags = (__future__.division.compiler_flag
    | __future__.print_function.compiler_flag)

def getsource(filename):
    with open(filename, "rU") as f: return f.read()

def execpoc(args, **kw):
    """Execute the named .poc file from disk

Returns the resulting top level object"""

    filename = args[0]
    code = compile(getsource(filename), filename, 'exec', compile_flags)
    oldargv = sys.argv[:]
    try:
        sys.argv[:] = args
        ns = initial_ns()
        ns['__file__'] = filename
        ns.update(kw)
        start()
        six.exec_(code, ns)
        return ns
    finally: sys.argv[:] = oldargv
 
def do_op(b):
    """Adds the object 'b' to the current operation"""
    if b is None: raise ValueError
    n = next(op)
    n(obj, b)

def _assign(a, b):
    return a.copyFrom(b)

def _fuse(a, b):
    return a.fuse(b)

def _common(a, b):
    return a.common(b)

def _cut(a, b):
    return a.cut(b)

def op1(x):
    return iter(itertools.chain([_assign], itertools.repeat(x)))

def start():
    global obj, op
    obj = occmodel.Solid()
    op = op1(_fuse)

def output(fn):
    with open(fn + ".tmp", "wb") as f: occ_to_stl(obj, f)
    os.rename(fn + ".tmp", fn)

def mesh_to_stl(m, dest):
    dest.write(b"\0" * 80)
    dest.write(struct.pack("<i", m.ntriangles()))

    n0 = struct.pack("<fff", 0., 0., 0.)
    for i in range(0, m.ntriangles()*3, 3):
        dest.write(n0)
        dest.write(struct.pack("<fff", *m.vertex(m.triangles[i])))
        dest.write(struct.pack("<fff", *m.vertex(m.triangles[i+1])))
        dest.write(struct.pack("<fff", *m.vertex(m.triangles[i+2])))
        dest.write(b'\0\0')

def occ_to_stl(o, dest, prec=.001):
    """Convert a mesh or solid to stl

Writes to the open file object 'dest'

If a solid is passed it, it is converted to a mesh with the given
precision, defaulting to .001."""
    if isinstance(o, occmodel.Mesh): mesh_to_stl(o, dest)
    mesh_to_stl(o.createMesh(prec), dest)

@contextlib.contextmanager
def withhelper(newop, newobj=None, finalop=None):
    global obj, op
    holdobj = obj
    holdop = op
    obj = newobj = newobj or occmodel.Solid()
    op = iter(newop)
    try:
        yield
    finally:
        if finalop: finalop()
        obj = holdobj
        op = holdop
        do_op(newobj)

### Primitives

def Box(p1, p2):
    """Create a box primitive"""
    do_op(occmodel.Solid().createBox(p1, p2))

def Cylinder(p1, p2, radius):
    """Create a cylinder primitive"""
    do_op(occmodel.Solid().createCylinder(p1, p2, radius))

### Group operations

def Intersection():
    """Perform an intersection operation"""
    return withhelper(op1(_common))

def Union():
    """Perform a union operation"""
    return withhelper(op1(_fuse))

def Difference():
    """Perform a difference operation"""
    return withhelper(op1(_cut))

def Op(fn, *args, **kw):
    """Convert a postfix operation into a group operation

the following are roughly equivalent::

 with Union():
     Box(p1, p2)
     Box(p3, p4)
     Fillet(8)

and::

 with Op(Fillet, 8):
     Box(p1, p2)
     Box(p3, p4)
"""
    return withhelper(op1(_common), finalop=lambda: fn(*args, **kw))

def Rotated(angle, axis, center=(0,0,0)):
    """Perform a rotate operation"""
    return Op(Rotate, angle, axis, center)

def Filleted(radius, edges=None):
    """Perform a fillet operation"""
    return Op(Fillet, radius, edges)

### Postfix operations

def Rotate(angle, axis, center=(0,0,0)):
    """Rotate the active object"""
    obj.rotate(angle, axis, center)

def Fillet(radius, edges=None):
    """Fillte the active object

If `edges` is None, then all edges are filletted.

If `edges` is callable, it is treated as a predicate which returns
True for each edge that should be filleted.

Otherwise, `edges` must be a sequence of edges to fillet.
"""
    if callable(edges): edges = [e for e in Edges() if edges(e)]
    obj.fillet(radius, edges)

### Inquiries

def Object():
    return obj

def Bbox():
    return obj.boundingBox()

def Edges():
    return occmodel.EdgeIterator(Object())

def Faces():
    return occmodel.FaceIterator(Object())

def Vertices():
    return occmodel.VertexIterator(Object())

def Wires():
    return occmodel.WireIterator(Object())
