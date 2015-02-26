#
# object-view.py
#
# Author: Jim Fix
# MATH 385, Reed College, Fall 2015
#
# Version: 02.23.15a
#
# This is my attempt to use GLSL 3.3 vertex/fragment shaders
# in PyOpenGL.  Unfortunately, I can't get these to compile
# on Mavericks with its version of GLUT.
#

import sys
from geometry import point, vector, EPSILON, ORIGIN
from quat import quat
from scene import vertex, edge, face, scene
from random import random
from math import sin, cos, acos, asin, pi, sqrt
from ctypes import *

from OpenGL.GL import *
from OpenGL.GLUT import *
from OpenGL.GLUT.freeglut import *

INFINITY = 10000000
trackball = None
flashlight = None

radius = 1.0
add_face = False
selected_face = None
last_selected_face = None

vertex_buffer = None
normal_buffer = None
color_buffer = None
colors = None
shaders = None

xStart = 0
yStart = 0
width = 512
height = 512
scale = 1.0/min(width,height)

def init_shaders():
    """Compile the vertex and fragment shaders from source."""
    global shaders

    vertex_shader = glCreateShader(GL_VERTEX_SHADER)
    glShaderSource(vertex_shader,open('shaders/vs-phong-interp.c','r').read())
    glCompileShader(vertex_shader)
    result = glGetShaderiv(vertex_shader, GL_COMPILE_STATUS)
    if result:
        print('Vertex shader compilation successful.')
    else:
        print('Vertex shader compilation FAILED:')
        print(glGetShaderInfoLog(vertex_shader))
        sys.exit(-1)

    fragment_shader = glCreateShader(GL_FRAGMENT_SHADER)
    glShaderSource(fragment_shader, open('shaders/fs-phong-interp.c','r').read())
    glCompileShader(fragment_shader)
    result = glGetShaderiv(fragment_shader, GL_COMPILE_STATUS)
    if result:
        print('Fragment shader compilation successful.')
    else:
        print('Fragment shader compilation FAILED:')
        print(glGetShaderInfoLog(fragment_shader))
        sys.exit(-1)

    shaders = glCreateProgram()
    glAttachShader(shaders,vertex_shader)
    glAttachShader(shaders,fragment_shader)
    glLinkProgram(shaders)


def draw():
    """ Issue GL calls to draw the scene. """
    global trackball, flashlight, \
           vertex_buffer, normal_buffer, \
           colors, color_buffer, selected_face, add_face, \
           shaders

    # Clear the rendering information.
    glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)

    # Clear the transformation stack.
    glMatrixMode(GL_MODELVIEW)
    glLoadIdentity()

    glPushMatrix()

    # Transform the objects drawn below by a rotation.
    trackball.glRotate()

    # * * * * * * * * * * * * * * * *
    # Draw all the triangular facets.
    glUseProgram(shaders)

    h_vertex = glGetAttribLocation(shaders,'vertex')
    h_normal = glGetAttribLocation(shaders,'normal')
    h_color = glGetAttribLocation(shaders,'color')
    h_eye =    glGetUniformLocation(shaders,'eye')
    h_light =  glGetUniformLocation(shaders,'light')

    # all the vertex positions
    glEnableVertexAttribArray(h_vertex)
    glBindBuffer (GL_ARRAY_BUFFER, vertex_buffer)
    glVertexAttribPointer(h_vertex, 3, GL_FLOAT, GL_FALSE, 0, None)
        
    # all the vertex normals
    glEnableVertexAttribArray(h_normal)
    glBindBuffer (GL_ARRAY_BUFFER, normal_buffer)
    glVertexAttribPointer(h_normal, 3, GL_FLOAT, GL_FALSE, 0, None)

    # all the face vertex colors
    glEnableVertexAttribArray(h_color)
    glBindBuffer (GL_ARRAY_BUFFER, color_buffer)

    if selected_face and add_face:
        # paint that face's vertices Green
        rgb_selected = [0.7,0.9,0.6] #GREEN
        for change in range(9):
            colors[selected_face.id * 9 + change] = rgb_selected[change % 3]
        # update the color buffer
        glBufferData (GL_ARRAY_BUFFER, len(colors)*4, 
                      (c_float*len(colors))(*colors), GL_STATIC_DRAW)
        add_face = False

    glVertexAttribPointer(h_color, 3, GL_FLOAT, GL_FALSE, 0, None)
        
    # position of the flashlight
    light = flashlight.rotate(vector(0.0,0.0,1.0));
    glUniform3fv(h_light, 1, (2.0*radius*light).components())

    # position of the viewer's eye
    eye = trackball.recip().rotate(vector(0.0,0.0,1.0))
    glUniform3fv(h_eye, 1, eye.components())

    glDrawArrays (GL_TRIANGLES, 0, len(face.instances) * 3)

    glDisableVertexAttribArray(h_vertex)
    glDisableVertexAttribArray(h_normal)
    glDisableVertexAttribArray(h_color)

    glPopMatrix()

    # Render the scene.
    glFlush()

    glutSwapBuffers()

def move_face(dir):
    global last_selected_face, selected_face, add_face

    D = {'LEFT':2, 'RIGHT':1}
    d = D[dir]

    # find which edge is the backwards hop edge
    last = 0
    for i in [0,1,2]:
        e = selected_face.edge(i)
        if e.twin and e.twin.face == last_selected_face:
            last = i
    e = selected_face.edge((last+d)%3)

    # highlight that next face
    if e.twin:
       last_selected_face = selected_face
       selected_face = e.twin.face
       add_face = True
       glutPostRedisplay()

def keyboard(key, x, y):
    """ Handle a "normal" keypress. """

    # Handle ESC key.
    if key == b'\033':	
	# "\033" is the Escape key
        sys.exit(1)
    
    if key == b',' and selected_face:
        move_face('LEFT')

    if key == b'.' and selected_face:
        move_face('RIGHT')


def arrow(key, x, y):
    """ Handle a "special" keypress. """
    global trackball,flashlight

    x_axis = trackball.recip().rotate(vector(1.0,0.0,0.0))
    y_axis = trackball.recip().rotate(vector(0.0,1.0,0.0))

    # Apply an adjustment to the overall rotation.
    if key == GLUT_KEY_DOWN:
        flashlight = quat.for_rotation( pi/12.0,x_axis) * flashlight
    if key == GLUT_KEY_UP:
        flashlight = quat.for_rotation(-pi/12.0,x_axis) * flashlight
    if key == GLUT_KEY_LEFT:
        flashlight = quat.for_rotation(-pi/12.0,y_axis) * flashlight
    if key == GLUT_KEY_RIGHT:
        flashlight = quat.for_rotation( pi/12.0,y_axis) * flashlight

    # Redraw.
    glutPostRedisplay()


def mouse(button, state, x, y):
    global xStart, yStart, trackball, selected_face, add_face
    xStart = (x - width/2) * scale
    yStart = (height/2 - y) * scale

    if glutGetModifiers() == GLUT_ACTIVE_SHIFT and state == GLUT_DOWN:
        minus_z = trackball.recip().rotate(vector(0.0,0.0,-1.0))
        click = trackball.recip().rotate(vector(xStart,yStart,2.0))
        selected_face = scene.intersect_ray(ORIGIN+click,minus_z)
        add_face = True
        
    glutPostRedisplay()

def motion(x, y):
    global trackball, xStart, yStart
    xNow = (x - width/2) * scale
    yNow = (height/2 - y) * scale
    change = point(xNow,yNow,0.0) - point(xStart,yStart,0.0)
    axis = vector(-change.dy,change.dx,0.0)
    sin_angle = change.norm()/radius
    sin_angle = max(min(sin_angle,1.0),-1.0) # clip
    angle = asin(sin_angle)
    trackball = quat.for_rotation(angle,axis) * trackball
    xStart,yStart = xNow, yNow

    glutPostRedisplay()

def init(filename):
    """ Initialize aspects of the GL scene rendering.  """
    global trackball, flashlight, vertex_buffer, normal_buffer, color_buffer, colors, vertices, normals

    # initialize quaternions for the light and trackball
    flashlight = quat.for_rotation(0.0,vector(1.0,0.0,0.0))
    trackball = quat.for_rotation(0.0,vector(1.0,0.0,0.0))

    # read the .OBJ file into VBOs
    scene.read(filename)
    vertices,normals,colors = scene.compile()
    
    vertex_buffer = glGenBuffers(1)
    glBindBuffer (GL_ARRAY_BUFFER, vertex_buffer)
    glBufferData (GL_ARRAY_BUFFER, len(vertices)*4, 
                  (c_float*len(vertices))(*vertices), GL_STATIC_DRAW)

    normal_buffer = glGenBuffers(1)
    glBindBuffer (GL_ARRAY_BUFFER, normal_buffer)
    glBufferData (GL_ARRAY_BUFFER, len(normals)*4, 
                  (c_float*len(normals))(*normals), GL_STATIC_DRAW)

    color_buffer = glGenBuffers(1)
    glBindBuffer (GL_ARRAY_BUFFER, color_buffer)
    glBufferData (GL_ARRAY_BUFFER, len(colors)*4, 
                  (c_float*len(colors))(*colors), GL_STATIC_DRAW)


    # set up the object shaders
    init_shaders()

    glEnable (GL_DEPTH_TEST)


def resize(w, h):
    """ Register a window resize by changing the viewport.  """
    global width, height, scale

    r = radius
    glViewport(0, 0, w, h)
    width = w
    height = h

    glMatrixMode(GL_PROJECTION)
    glLoadIdentity()
    if w > h:
        glOrtho(-w/h*r, w/h*r, -r, r, -r, r)
        scale = 2.0 * r / h 
    else:
        glOrtho(-r, r, -h/w * r, h/w * r, -r, r)
        scale = 2.0 * r / w 


def main(argc, argv):
    """ The main procedure, sets up GL and GLUT. """

    glutInit(argv)
    glutInitDisplayMode(GLUT_DOUBLE | GLUT_RGB | GLUT_DEPTH)
    glutInitWindowPosition(0, 20)
    glutInitWindowSize(width, height)
    glutCreateWindow( 'object-view.py - Press ESC to quit' )
    init(argv[1])

    # Register interaction callbacks.
    glutKeyboardFunc(keyboard)
    glutSpecialFunc(arrow)
    glutReshapeFunc(resize)
    glutDisplayFunc(draw)
    glutMouseFunc(mouse)
    glutMotionFunc(motion)

    print()
    print('Press the arrow keys move the flashlight.')
    print('Press ESC to quit.\n')
    print()

    glutMainLoop()

    return 0

if __name__ == '__main__': main(len(sys.argv),sys.argv)
