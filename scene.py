#
# scene.py
#
# Defines a "global object", a class called "scene" that contains
# a method for reading a (collection of) Alias/Wavefront .obj files
# and storing them into a winged twinned half-edge data structure.
# Thus, a scene is constituted by three object classes:
#
#   vertex: a corner of a faceted surface.  It has a 3D position 
#           and a set of directed half-edges emanating from it.
#           They serve as the "umbrella spine" of a fan of faces
#           that meet at these corner vertex.
#
#   edge: a directed half-edge that serves as the boundary of 
#         some oriented face of a surface. It may have an 
#         opposite-oriented twin half-edge should they each
#         serve as a crease between two faces.
#
#   face: a triangular face on a surface of some object in the 
#         scene.  It has three border half-edges.  

from constants import *
from geometry import vector, point, ORIGIN
from math import sqrt
import sys

#
# class fan
# 
# This is an iterator object that can be used to
# loop through all the edges that emanate from a
# vertex.
# 
class fan:

    #
    # The fan instance attributes:
    #
    # * vertex: the vertex that serves as the center of this fan
    # * which: the current edge being examined during the loop's iteration
    #

    # __init__
    #
    # Creates a fan object for the given vertex,
    #
    def __init__(self,vertex):
        self.vertex = vertex
        self.which = None

    # __iter__
    #
    # (Re)sets this as an iterator for the start of a loop.
    #
    def __iter__(self):
        self.which = self.vertex.edge     # First edge on the fan.
        print('start:',self.vertex.edge)
        return self

    # __next__
    #
    # Advances the iterator to the next edge on the fan.
    #
    def __next__(self):

        print('next: ends: ',self.which, self.vertex.edge)
        
        if self.which == None:
            # If we've exhausted the edges that form the fan, stop.
            raise StopIteration
        else:
            # Otherwise, note where we are in the fan...
            current = self.which

            # ...and advance to the next edge.


            # To advance, make sure that we're not the whole way around...
            if current.next.next.twin != None and \
               current.next.next.twin != self.vertex.edge:   

                # ...and, if not, advance to the next fan edge.
                self.which = current.next.next.twin

            # Otherwise, signal that we've exhausted our edges.  This
            # "None" signal will be noticed by a subsequent call to 
            # __next__.
            else:
                self.which = None

            # Regardless, give back the current edge.
            return current

#
#  class vertex: 
#
#  Its instances are corners of a faceted surface. 
#  The class also houses a list of all its instances.
#
class vertex:

    # vertex class attributes:
    #
    # * instances: a list of all instances of class vertex
    #
    instances = []

    @classmethod
    #
    # vertex.with_id(id):
    #
    # Returns the instance with the given integer id.
    #
    def with_id(cls,id):
        return cls.instances[id]

    @classmethod
    #
    # vertex.all_instances():
    #
    # Returns all the instances of class vertex as a list.
    #
    def all_instances(cls):
        return cls.instances

    @classmethod
    # vertex.add(p):
    #
    # Creates and returns a new vertex instance at position p.
    #
    def add(cls,position):
        return vertex(position)

    @classmethod
    # vertex.set_first_edge():
    #
    # Makes sure that the recorded out edge of each vertex
    # is one that is clockwise from all the others.
    #
    def set_first_edges(cls):
        for V in cls.all_instances():
            V.set_first_edge()

            
    @classmethod
    # vertex.smooth_normals():
    #
    # Computes a new vertex normal for all the vertices.  Each computes a
    # a weighted average of its normal with the normal of its neighboring
    # vertices.
    #
    def smooth_normals(cls):
        #
        # Compute 
        #
        #     n' := d n + sum n_i
        #
        # for each neighbor normal n_i.  Here d is the number of neighbors
        # (the degree) of the vertex.
        #
        for V in cls.instances:
            n = vector(0.0,0.0,0.0)
            for e in V.around():
                n = n + V.normal() + e.vertex(1).normal()
            V.new_vn = n.unit()

        #
        # Replace each normal with the one computed above.
        #
        for V in cls.instances:
            V.set_normal(V.new_vn)
        
    
    # vertex(P):
    #
    # (Creates and) initializes a new vertex object at position P.
    #
    def __init__(self,P):
        self.position = P
        self.edge = None
        self.id = len(vertex.instances)
        vertex.instances.append(self)
        self.vn = None

    #
    # self.set_normal(vn):
    #
    # Sets or changes the normal attached to this vertex.
    #
    def set_normal(self, vn):
        self.vn = vn

    #
    # self.normal():
    #
    # Returns the surface normal at this vertex.  Computes 
    # a normal from the fan of faces around the vertex, were
    # no normal computed yet.
    #
    def normal(self):
        # If there's no normal, compute one.
        if not self.vn:
            # Sum the incident face normals.
            ns = vector(0.0,0.0,0.0)
            for e in self.around():
                ns = ns + e.face.normal()
            # Normalize that sum.
            self.set_normal(ns.unit())

        # Return the normal attribute.
        return self.vn

    #
    # self.color()
    #
    # Returns the material color of this vertex.  For now,
    # we'll just hardwire the color to a medium slate blue.
    def color(self):
        return vector(0.5,0.45,0.57)

    # self.around()
    #
    # This produces an iterator for looping over all the edges
    # that form the fan around a vertex.
    #
    #   for e in V.around():
    #      ... do something with e ...
    #
    # See class "fan" for details, and method "normal" for a 
    # concrete example of its use.
    #
    def around(self):
        return fan(self)

    # self.set_first_edge()
    #
    # Works clockwise around the edge fan of a vertex, setting 
    # its out edge to be the start of that fan.  This is only
    # necessary for "open-fanned" vertices, not those vertices 
    # that are at the tip of a closed fan cone.
    #
    def set_first_edge(self):
        e = self.edge
        while e != None \
              and e.twin != None \
              and e != self.edge:
        
            # If not, then we work backwards to the prior edge.
            e = e.twin.next

        # Otherwise, let's have this be the first out edge.
        self.edge = e


#
# class edge: 
#
# An edge connects two vertices.  It is oriented, and it has a twin
# connected the same two vertices, but in the opposite direction. 
# Each edge has a face to its left, one of the three edges forming
# the counterclockwise border around that face.
#
# The two directed edge twins serve as the meeting crease between 
# two faces.
#
class edge:

    # vertex class attributes:
    #
    # * dictionary: a mapping from vertex id pairs to edge instances
    #
    dictionary = { }

    @classmethod
    #
    # edge.between_ids(iv1,iv2):
    # 
    # Return whether or not an edge between V1 and V2 had been 
    # constructed, where V1.id = iv1 and V2.id = iv2.  Returns
    # that edge if so, and None if not.
    #
    def between_ids(cls,iv1,iv2):
        if (iv1,iv2) in cls.dictionary:
            return cls.dictionary[(iv1,iv2)]
        else:
            return None

    @classmethod
    #
    # register(e,iv1,iv2):
    #
    # Associate edge e with the vertex id pair (iv1,iv2).
    #
    def register(cls,e,iv1,iv2):
        cls.dictionary[(iv1,iv2)] = e


    #
    # edge(V1,V2,f):
    #
    # Create an edge from V1 to V2 bordering face f.
    #
    # vertex instance attributes:
    #
    #  * source: first vertex of the vertex pair
    #  * face: left face bordered by this edge
    #  * next: next edge bordering the same face
    #  * twin: the twin edge to this edge
    #
    def __init__(self,V1,V2,f):

        self.source = V1  # Set the source vertex.
        V1.edge = self    # Register edge with the source vertex.
        self.face = f     # Set the face.

        self.next = None  # Will be set later.

        # Register this edge.
        iv1 = V1.id
        iv2 = V2.id
        if edge.between_ids(iv1,iv2):
            print('Bad orientation for face ',f)
        edge.register(self,iv1,iv2)

        # Check if this edge has a twin yet.
        self.twin = edge.between_ids(iv2,iv1)
        if self.twin:
            # Update the twin info of its twin.
            self.twin.twin = self
    
    # 
    # self.vertex(i):
    #
    # Get either the source (i=0) or the target vertex (i=1) of
    # this directed edge.
    #
    def vertex(self,i):
        if i == 0:
            return self.source
        elif i == 1:
            return self.next.source
        else:
            return None

    # 
    # self.vector():
    #
    # Returns the offset between the two vertices.
    #
    def vector(self):
        return self.vertex(1).position - self.vertex(0).position

    # 
    # self.direction():
    #
    # Returns the direction of the offset between the 
    # two vertices.
    #
    def direction(self):
        return self.vector().unit()


    def __str__(self):
        return str(self.vertex(0).id)+':'+str(self.vertex(1).id)
#
# class face: 
#
# Its instances are triangular facets on the surface.  It has three
# vertices as its corners and three edges that serve as its boundary.
#
class face:

    # Class attributes:
    #
    #  * instances: list of all face instances
    #
    instances = []

    @classmethod
    # face.of_id(id):
    #
    # Get the face with the given integer id.
    #
    def of_id(cls,id):
        return cls.instances[id]

    @classmethod
    # face.all_instances():
    #
    # Returns the list of all face instances.
    #
    def all_instances(cls):
        return cls.instances

    @classmethod
    # face.add(V1,V2,V3):
    #
    # Creates and returns a new face instance with vertex corners
    # V1, V2, and V3.
    #
    def add(self,V1,V2,V3):
        return face(V1,V2,V3)

    #
    # face(V1,V2,V3):
    #
    # Create and initialize a new face instance.
    #
    # Instance attributes:
    #
    #   * side: one of the three directed edges
    #   * fn: face normal
    #   * id: integer id identifying this vertex
    #
    def __init__(self,V1,V2,V3):

        e1 = edge(V1,V2,self)
        e2 = edge(V2,V3,self)
        e3 = edge(V3,V1,self)

        e1.next = e2
        e2.next = e3
        e3.next = e1
        
        self.side = e1
        self.id = len(face.instances)
        face.instances.append(self)
        self.fn = None

    #
    # self.normal():
    #
    # Returns the surface normal at this vertex.  Computes 
    # a normal if it hasn't been computed yet.
    #
    def normal(self):
        if not self.fn:
            e0 = self.edge(0).direction()
            e1 = self.edge(1).direction()
            self.fn = e0.cross(e1)

        return self.fn

    #
    # self.vertex(i):
    # 
    # Returns either the 0th, the 1st, or the 2nd vertex.
    #
    def vertex(self,i):
        if i > 2:
            return None
        else:
            return self.edge(i).source

    #
    # self.edge(i):
    # 
    # Returns either the 0th, the 1st, or the 2nd boundary edge.
    #
    def edge(self,i):
        if i == 0:
            return self.side
        elif i == 1:
            return self.side.next
        elif i == 2:
            return self.side.next.next
        else:
            return None

    def intersect_ray(self,R,d):
        Q1 = self.vertex(0).position
        Q2 = self.vertex(1).position
        Q3 = self.vertex(2).position

        # compute normals to the plane of the facet
        Q = Q1
        v2 = Q2 - Q1
        v3 = Q3 - Q1
        o = v2.cross(v3)
        if abs(o) < EPSILON:
            # the facet is a sliver or a point
            return None
        
        ell = v2.unit()
        emm = v3.unit()
        enn = ell.cross(emm).unit()
        dist = enn.dot(R - Q)
        if abs(dist) < EPSILON:
            # the ray source R is in the plane of this facet
            return None

        # flip the orientation of the surface normal to the back face
        if dist < 0:
            enn = -enn
        ratio = -(enn.dot(d))
        if ratio <= 0:
            # the ray shoots along or away from the facet's plane
            return None

        # compute where the ray intersects the plane
        scale = abs(dist) / ratio
        P = R + (scale * d)

        # check if P lives within the facet
        w = P-Q
        o3 = v2.cross(w)
        o2 = w.cross(v3)
        if o2.dot(o) < 0 or o3.dot(o) < 0:
            # the point P is not in the cone <Q1,v2,v3>
            return None

        a2 = abs(o2)/abs(o)
        a3 = abs(o3)/abs(o)
        a1 = 1.0-a2-a3
        if a1 < 0.0 or a2 < 0.0 or a3 < 0.0:
            # the point P is beyond line <Q2,Q3> in that cone
            return None

        return [[a1,a2,a3],scale,dist]

#
# class scene:
#
# Singleton object that houses all the methods that govern reading 
# scene (.obj) files and incorporating them into the vertex and 
# face collections above.
#
class scene:

    @classmethod
    def read(cls,filename):

        obj_file = open(filename,'r')

        # Record the offset for vertex ID conversion.
        vertexi = len(vertex.all_instances())   

        # Count the number of vertex normals read.
        normali = 0                             

        for line in obj_file:

            parts = line[:-1].split()
            if len(parts) > 0:

                # Read a vertex description line.
                if parts[0] == 'v': 
                    x = float(parts[1])
                    y = float(parts[2])
                    z = float(parts[3])
                    P = point(x,y,z)
                    vertex.add(P)

                # Read a vertex normal description line.
                elif parts[0] == 'vn': 
                    dx = float(parts[1])
                    dy = float(parts[2])
                    dz = float(parts[3])
                    vn = vector(dx,dy,dz).unit()
                    vertex.with_id(vertexi + normali).set_normal(vn)
                    normali += 1

                # Read a face/fan description line.
                elif parts[0] == 'f': 

                    #### ADDS AN OFFSET vertexi FROM THE .OBJ INDEX!!! (.OBJ starts at 1) ####
                    vi_fan = [int(p.split('/')[0]) + vertexi - 1 for p in parts[1:]]

                    vi1 = vi_fan[0]
                    # add the faces of the fan
                    for i in range(1,len(vi_fan)-1):
                        vi2 = vi_fan[i]
                        vi3 = vi_fan[i+1]
                        V1 = vertex.with_id(vi1)
                        V2 = vertex.with_id(vi2)
                        V3 = vertex.with_id(vi3)
                        face.add(V1,V2,V3)

        # set the vertex fan ordering
        vertex.set_first_edges()

        # compute the vertex normals, then smooth then out
        vertex.smooth_normals()

        # rescale and center the points
        scene.rebox()

    @classmethod
    def rebox(cls):
        max_dims = point(sys.float_info.min,
                         sys.float_info.min,
                         sys.float_info.min)
        min_dims = point(sys.float_info.max,
                         sys.float_info.max,
                         sys.float_info.max)
        for V in vertex.all_instances():
            max_dims = max_dims.max(V.position)
            min_dims = min_dims.min(V.position)

        center = min_dims.combo(0.5,max_dims)
        span = max_dims - min_dims
        scale = 1.8*sqrt(2.0)/abs(span)

        for V in vertex.all_instances():
            V.position = ORIGIN + scale * (V.position-center)

    @classmethod
    def compile(cls):
        varray = []
        narray = []
        carray = []
        for f in face.all_instances():
            for i in [0,1,2]:
                varray.extend(f.vertex(i).position.components())
                narray.extend(f.vertex(i).normal().components())
                carray.extend(f.vertex(i).color().components())
        return (varray,narray,carray)

    @classmethod
    def intersect_ray(self,R,d):
        selected = None
        dist = sys.float_info.min
        for f in face.all_instances():
            sect = f.intersect_ray(R,d)
            if sect:
                if sect[2] > dist:
                    dist = sect[2]
                    selected = f
        return selected
