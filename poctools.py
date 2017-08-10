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
import math
import os
import six
import struct
import sys
import traceback

import OCC.BRepAlgo
import OCC.BRepAlgoAPI
import OCC.BRepBuilderAPI
import OCC.BRepBndLib
import OCC.BRepFilletAPI
import OCC.BRepGProp
import OCC.BRepLib
import OCC.BRepOffsetAPI
import OCC.BRepPrimAPI
import OCC.BRepTools
import OCC.Bnd
import OCC.GC
import OCC.GCE2d
import OCC.Geom
import OCC.Geom2d
import OCC.gp
import OCC.GProp
import OCC.StlAPI
import OCC.TopAbs
import OCC.TopExp
import OCC.TopTools
import OCC.TopoDS

def _dir(x):
    if isinstance(x, (tuple, list)):
        return OCC.gp.gp_Dir(*x)
    return x

def _vec(x):
    if isinstance(x, (tuple, list)):
        return OCC.gp.gp_Vec(*x)
    return x

def _pt(x):
    if isinstance(x, (tuple, list)):
        return OCC.gp.gp_Pnt(*x)
    return x

def _axpt(p1, p2):
    p1 = _pt(p1)
    p2 = _pt(p2)
    dx = p2.X() - p1.X()
    dy = p2.Y() - p1.Y()
    dz = p2.Z() - p1.Z()
    length = (dx*dx + dy*dy + dz*dz) ** .5
    return OCC.gp.gp_Ax2(p1, OCC.gp.gp_Dir(dx/length, dy/length, dz/length))

def _axcn(p, n):
    p = _pt(p)
    n = _pt(n)
    dx = n.X()
    dy = n.Y()
    dz = n.Z()
    length = (dx*dx + dy*dy + dz*dz) ** .5
    return OCC.gp.gp_Ax2(p, OCC.gp.gp_Dir(dx/length, dy/length, dz/length))

__all__ = [
    'Box', 'Cylinder', 'Cone', 'Sphere', 'Text', 'Torus',
    'Extrude', 'Revolve', 'Loft', 'Pipe',
    'Chamfer', 'Fillet', 'Rotate', 'Translate', 'Transform',
    'Chamfered', 'Filleted', 'Rotated', 'Translated', 'Transformed',
    'Intersection', 'Difference', 'Union', 'Op',
    'Object', 'Bbox', 'CenterOfMass', 'CentreOfMass',
    'Edges', 'Faces', 'Vertices', 'Wires',
    'Matrix', 'Vertex', 'Edge', 'Wire', 'Face',
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
        from poctools import *
        """,  ns)
    return ns

compile_flags = (__future__.division.compiler_flag
    | __future__.print_function.compiler_flag)

def getsource(filename):
    with open(filename, "rU") as f:
        return f.read()

def execpoc(args, **kw):
    """Execute the named .poc file from disk

Returns the resulting top level object"""

    oldargv = sys.argv[:]
    try:
        filename = args[0]
        code = compile(getsource(filename), filename, 'exec', compile_flags)
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
    if b is None:
        raise ValueError
    n = next(op)
    n(obj, b)

def _assign(a, b):
    global obj
    obj = b

def _fuse(a, b):
    global obj
    obj = OCC.BRepAlgoAPI.BRepAlgoAPI_Fuse(a, b).Shape()

def _common(a, b):
    global obj
    obj = OCC.BRepAlgoAPI.BRepAlgoAPI_Common(a, b).Shape()

def _cut(a, b):
    global obj
    obj = OCC.BRepAlgoAPI.BRepAlgoAPI_Cut(a, b).Shape()

def op1(x):
    return iter(itertools.chain([_assign], itertools.repeat(x)))

def start():
    global obj, op
    obj = OCC.TopoDS.TopoDS_Shape()
    op = op1(_fuse)

def output(fn):
    occ_to_stl(obj, fn)

def occ_to_stl(obj, filename, prec=.05):
    """Convert a solid to stl"""
    w = OCC.StlAPI.StlAPI_Writer()
    w.SetASCIIMode(False)
    w.SetDeflection(prec)
    w.SetRelativeMode(False)
    w.Write(obj, filename + ".tmp", True)
    os.rename(filename + ".tmp", filename)

@contextlib.contextmanager
def withhelper(newop, newobj=None, finalop=None):
    global obj, op
    holdobj = obj
    holdop = op
    obj = newobj = newobj or OCC.TopoDS.TopoDS_Shape()
    op = iter(newop)
    try:
        yield
    finally:
        if finalop: finalop()
        newobj = obj
        obj = holdobj
        op = holdop
        do_op(newobj)

### Primitives

def Box(p1, p2):
    """Create a box primitive"""
    do_op(OCC.BRepPrimAPI.BRepPrimAPI_MakeBox(_pt(p1), _pt(p2)).Shape())

def Cylinder(p1, p2, radius):
    """Create a cylinder primitive"""
    p1 = _pt(p1)
    p2 = _pt(p2)
    dx = p2.X() - p1.X()
    dy = p2.Y() - p1.Y()
    dz = p2.Z() - p1.Z()
    length = (dx*dx + dy*dy + dz*dz) ** .5
    ax = OCC.gp.gp_Ax2(p1, OCC.gp.gp_Dir(dx/length, dy/length, dz/length))
    do_op(OCC.BRepPrimAPI.BRepPrimAPI_MakeCylinder(ax, radius, length).Shape())

def Cone(p1, p2, radius1, radius2):
    """Create a cone primitive"""
    p1 = _pt(p1)
    p2 = _pt(p2)
    dx = p2.X() - p1.X()
    dy = p2.Y() - p1.Y()
    dz = p2.Z() - p1.Z()
    length = (dx*dx + dy*dy + dz*dz) ** .5
    ax = OCC.gp.gp_Ax2(p1, OCC.gp.gp_Dir(dx/length, dy/length, dz/length))
    builder = OCC.BRepPrimAPI.BRepPrimAPI_MakeCone(
            ax, radius1, radius2, length)
    shape = builder.Shape()
    do_op(shape)

def Sphere(center, radius):
    """Create a sphere primitive"""
    do_op(OCC.BRepPrimAPI.BRepPrimAPI_MakeSphere(_pt(center), radius).Shape())

def Text(height, depth, text, fontpath=None):
    """TODO Create extruded text

Note that the text may not contain whitespace!
(this appears to be a bug in occmodel, failing with occmodel.OCCError:
b'failed to create edges')"""
    return Box((0,0,0), (1,1,1))

def Torus(p1, p2, ringRadius, radius):
    """Create a torus"""
    axis = _axpt(p1, p2)
    builder = OCC.BRepPrimAPI.BRepPrimAPI_MakeTorus(axis, ringRadius, radius)
    do_op(builder.Shape())

def Extrude(obj, p1, p2):
    """Create a solid by extruding edge, wire, or face from p1 to p2"""
    p1 = _pt(p1)
    p2 = _pt(p2)
    direction = OCC.gp.gp_Vec(p1, p2)
    do_op(OCC.BRepPrimAPI.BRepPrimAPI_MakePrism(obj, direction).Shape())

def Revolve(face, p1, p2, angle):
    """Create a solid by revolving the face around the given axis"""
    p1 = _pt(p1)
    p2 = _pt(p2)
    dx = p2.X() - p1.X()
    dy = p2.Y() - p1.Y()
    dz = p2.Z() - p1.Z()
    axis = OCC.gp.gp_Ax1(p1, _dir((dx, dy, dz)))
    angle = math.radians(angle)
    do_op(OCC.BRepPrimAPI.BRepPrimAPI_MakeRevol(face, axis, angle, False).Shape())

def Loft(profiles, ruled=True, tolerance=1e-6):
    """Create a solid by lofting through a sequence of wires or closed edges"""
    builder = OCC.BRepOffsetAPI.BRepOffsetAPI_ThruSections(True, ruled,
                tolerance)
    for i in profiles:
        if isinstance(i, OCC.TopoDS.TopoDS_Wire):
            builder.AddWire(i)
        elif isinstance(i, OCC.TopoDS.TopoDS_Vertex):
            builder.AddVertex(i)
        else:
            builder.AddWire(Wire.createWire(i))
    do_op(builder.Shape())

def Pipe(face, path):
    if isinstance(path, OCC.TopoDS.TopoDS_Edge):
        wire = Wire.createWire((path,))
    else:
        wire = path
    builder = OCC.BRepOffsetAPI.BRepOffsetAPI_MakePipe(wire, face)
    do_op(builder.Shape())

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
    return withhelper(op1(_fuse), finalop=lambda: fn(*args, **kw))

def Rotated(angle, axis, center=(0,0,0)):
    """Perform a rotate operation"""
    return Op(Rotate, angle, axis, center)

def Translated(delta):
    """Perform a translate operation"""
    return Op(Translate, delta)

def Transformed(mat):
    """Perform a transformation.

Note that `geotools.Transform` is imported as `Xform` within poc files."""
    return Op(Transform, mat)

def Filleted(radius, edges=None):
    """Perform a fillet operation"""
    return Op(Fillet, radius, edges)

def Chamfered(distance, edges=None):
    """Perform a fillet operation"""
    return Op(Chamfer, distance, edges)

### Postfix operations

def _transform(obj, t):
    _assign(obj,
        OCC.BRepBuilderAPI.BRepBuilderAPI_Transform(obj, t, True).Shape())

def Rotate(angle, axis, center=(0,0,0)):
    """Rotate the active object"""
    angle = math.radians(angle)
    a = OCC.gp.gp_Ax1()
    a.SetLocation(_pt(center))
    a.SetDirection(_dir(axis))
    t = OCC.gp.gp_Trsf()
    t.SetRotation(a, angle)
    _transform(obj, t)

def Translate(delta):
    """Translate the active object"""
    t = OCC.gp.gp_Trsf()
    t.SetTranslation(_vec(delta))
    _transform(obj, t)

def Matrix(*args):
    result = OCC.gp.gp_Trsf()
    if len(args) == 0:
        return result
    if len(args) == 3:
        if len(args[0]) == 4:
            result.SetValues(*(args[0] + args[1] + args[2]))
            return result
        elif len(args[0]) == 3:
            result.SetValues(*(args[0] + (0,) + args[1] + (0,) + args[2] + (0,)))
            return result
    elif len(args) == 9:
        result.SetValues(
            args[0], args[1], args[2], 0,
            args[3], args[4], args[5], 0,
            args[6], args[7], args[8], 0)
        return result
    result.SetValues(*args)
    return result

def Transform(mat):
    """Transform the active object

Note that `geotools.Transform` is imported as `Xform` within poc files."""
    _transform(obj, mat)

def Fillet(radius, edges=None):
    """Fillet the active object

If `edges` is None, then all edges are filletted.

If `edges` is callable, it is treated as a predicate which returns
True for each edge that should be filleted.

Otherwise, `edges` must be a sequence of edges to fillet.
"""
    if callable(edges):
        edges = [e for e in Edges() if edges(e)]
    elif edges is None:
        edges = [e for e in Edges()]
    fillet = OCC.BRepFilletAPI.BRepFilletAPI_MakeFillet(obj)
    for e in edges:
        fillet.Add(radius, e)
    _assign(obj, fillet.Shape())

def Chamfer(distance, edges=None):
    """Chamfer the active object

If `edges` is None, then all edges are filletted.

If `edges` is callable, it is treated as a predicate which returns
True for each edge that should be filleted.

Otherwise, `edges` must be a sequence of edges to fillet.
"""
    if callable(edges):
        edges = [e for e in Edges() if edges(e)]
    elif edges is None:
        edges = [e for e in Edges()]
    chamfer = OCC.BRepFilletAPI.BRepFilletAPI_MakeChamfer(obj)
    m = OCC.TopTools.TopTools_IndexedDataMapOfShapeListOfShape();
    OCC.TopExp.topexp.MapShapesAndAncestors(obj, OCC.TopAbs.TopAbs_EDGE,
        OCC.TopAbs.TopAbs_FACE, m)

    for e in edges:
        f = m.FindFromKey(e).First()
        f = OCC.TopoDS.topods.Face(f)
        chamfer.Add(distance, e, f)
    _assign(obj, chamfer.Shape())

### Inquiries

def visit(shape, topologyType, factory):
    explorer = OCC.TopExp.TopExp_Explorer()
    explorer.Init(shape, topologyType)
    while explorer.More():
        it = explorer.Current()
        # XXX pythonocc-core examples _loop_topo avoids yielding
        # items with equal _hash__ more than once but this seems bogus
        yield factory(it)
        explorer.Next()

def Object():
    return obj

def CenterOfMass():
    """Return the bounding box of the current item"""
    prop = OCC.GProp.GProp_GProps()
    OCC.BRepGProp.brepgprop_VolumeProperties(obj, prop)
    return prop.CentreOfMass()
CentreOfMass = CenterOfMass

def Bbox(o=None):
    """Return the bounding box of given object or the current item a a 6-tuple

(minx, miny, minz, maxx, maxy, maxz)"""
    box = OCC.Bnd.Bnd_Box()
    OCC.BRepBndLib.brepbndlib.Add(o or obj, box)
    lo = box.CornerMin()
    hi = box.CornerMax()
    return ((lo.X(), lo.Y(), lo.Z(), hi.X(), hi.Y(), hi.Z()))

def Edges():
    """Return the edge iterator of the current item"""
    return visit(Object(), OCC.TopAbs.TopAbs_EDGE, OCC.TopoDS.topods.Edge)

def Faces():
    """Return the face iterator of the current item"""
    return visit(Object(), OCC.TopAbs.TopAbs_FACE, OCC.TopoDS.topods.Face)

def Vertices():
    """Return the vertex iterator of the current item"""
    return visit(Object(), OCC.TopAbs.TopAbs_VERTEX, OCC.TopoDS.topods.Vertex)

def Wires():
    """Return the wire iterator of the current item"""
    return visit(Object(), OCC.TopAbs.TopAbs_WIRE, OCC.TopoDS.topods.Wire)

class Edge:
    @classmethod
    def createLine(cls, p1, p2):
        p1 = _pt(p1)
        p2 = _pt(p2)
        return OCC.BRepBuilderAPI.BRepBuilderAPI_MakeEdge(p1, p2).Edge()

    @classmethod
    def createArc3P(cls, start, end, mid):
        p1 = _pt(start)
        p2 = _pt(mid)
        p3 = _pt(end)
        arc = OCC.GC.GC_MakeArcOfCircle(p1, p2, p3).Value()
        return OCC.BRepBuilderAPI.BRepBuilderAPI_MakeEdge(arc).Edge()

    @classmethod
    def createCircle(cls, center, normal, radius):
        ax = _axcn(center, normal)
        arc = OCC.GC.GC_MakeCircle(ax, radius).Value()
        return OCC.BRepBuilderAPI.BRepBuilderAPI_MakeEdge(arc).Edge()
        
    @classmethod
    def createHelix(cls, pitch, height, radius, angle, leftHanded=False):
        axis = OCC.gp.gp_Ax2(_pt((0,0,0)), OCC.gp.gp.DZ())
        axis = OCC.gp.gp_Ax3(axis)
        if angle <= 0:
            surf = OCC.Geom.Geom_CylindricalSurface(axis, radius)
        else:        
            angle = math.radians(angle)
            surf = OCC.Geom.Geom_ConicalSurface(axis, angle, radius)
        if leftHanded:
            p = OCC.gp.gp_Pnt2d(2*math.pi,0)
            d = OCC.gp.gp_Dir2d(-2 * math.pi, pitch)
        else:
            p = OCC.gp.gp_Pnt2d(0,0)
            d = OCC.gp.gp_Dir2d(2 * math.pi, pitch)

        axis2 = OCC.gp.gp_Ax2d(p, d)
        line = OCC.Geom2d.Geom2d_Line(axis2)
        end_u = (4*math.pi*math.pi+pitch*pitch)**.5*(height/pitch)
        begin = line.Value(0)
        end = line.Value(end_u)

        seg = OCC.GCE2d.GCE2d_MakeSegment(begin, end).Value()
        edge = OCC.BRepBuilderAPI.BRepBuilderAPI_MakeEdge(seg,
            OCC.Geom.Handle_Geom_Surface(surf)).Edge()
        OCC.BRepLib.breplib.BuildCurves3d(edge)
        return edge

    @classmethod
    def createEllipse(cls, center, normal, rMajor, rMinor):
        ax = _axcn(center, normal)
        arc = OCC.GC.GC_MakeEllipse(ax, rMajor, rMinor).Value()
        return OCC.BRepBuilderAPI.BRepBuilderAPI_MakeEdge(arc).Edge()
        
class Wire:
    @classmethod
    def createWire(cls, arg):
        if isinstance(arg, (list, tuple)): pass
        else: arg = (arg,)
        builder = OCC.BRepBuilderAPI.BRepBuilderAPI_MakeWire()
        for i in arg:
            builder.Add(i)
        return builder.Wire()

def Vertex(x,y,z):
    builder = OCC.BRepBuilderAPI.BRepBuilderAPI_MakeVertex(_pt((x,y,z)))
    return builder.Vertex()

def _dump(obj):
    import OCC.BRepTools
    OCC.BRepTools.breptools.Write(obj, "/dev/stdout")

class Face:
    @classmethod
    def createFace(cls, arg):
        def f(x):
            if isinstance(x, OCC.TopoDS.TopoDS_Edge):
                return Wire.createWire(x)
            else:
                return x
        if isinstance(arg, (list, tuple)):
            pass
        else:
            arg = (arg,)
        outer = arg[0]
        rest = arg[1:]
        outer = f(outer)
        builder = OCC.BRepBuilderAPI.BRepBuilderAPI_MakeFace(outer)
        for i in rest:
            i = f(i)
            builder.Add(i)
        return builder.Face()
