#!python3

import sys

# READ THE PARAMS AND INIT
#

if not (len(sys.argv) in [2,5]):
  print('usage: python3 pgm2obj.py <filename> [<dx> <dy> <dz>]')
  sys.exit(0)

if sys.argv[1][-4:] != '.pgm':
  print(sys.argv[1][-4:])
  print('Filename should have .pgm extension.')
  sys.exit(0)

MAGIC = 0
WIDTH = 1
HEIGHT = 2
MAX = 3
DATA = 4

w  = None
h = None
m = None
vs = []
state = MAGIC
scale_x = 1.0
scale_y = 1.0
scale_h = 1.0

if len(sys.argv) == 5:
  scale_x = float(sys.argv[2])
  scale_y = float(sys.argv[3])
  scale_h = float(sys.argv[4])

# READ THE .PGM FILE INTO vs
#
f = open(sys.argv[1])
for line in f:
  if line[0] == '#': continue
  entries = line.split(' ')
  if entries[0] != '' and entries[0][0] == 'P':
    if state != MAGIC:
      print('ERROR: Magic designator appeared twice.')
    else:
      state = WIDTH
  else:
    entries = line.split(' ')
    for word in entries:
      if word != '':
        if state == WIDTH:
           w = int(word)
           print('# width:',w)
           state = HEIGHT
        elif state == HEIGHT:
           h = int(word)
           print('# height:',h)
           state = MAX
        elif state == MAX:
           m = int(word)
           print('# max:',m)
           state = DATA
        elif state == DATA:
           vs.append(scale_h*float(word)/m)
        else:
           print('ERROR: confused.')

if len(vs) < w * h:
  print('WARNING: There were too few data values. Padding...')
  vs = vs + ([0.0]*(w*h))
elif len(vs) > w*h:
  print('WARNING: There were too many data values. Trimming...')

# OUTPUT THE .OBJ
#
which = 0
for j in range(h):
  for i in range(w):
    x = -scale_x/2.0 + i*scale_x/(w-1)
    y = -scale_y/2.0 + scale_y - j * scale_y / (h-1)
    height = vs[which]
    print('v', x, y, height)
    which = which + 1

def vi(i,j):
  return j*w+i + 1

for j in range(h-1):
  for i in range(w-1):
    print('f', vi(i,j), vi(i+1,j+1), vi(i+1,j))
    print('f', vi(i,j), vi(i,j+1), vi(i+1,j+1))

