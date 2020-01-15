import sys
import select
from time import sleep

def something(line):
  print('read input:', line, end='')

def something_else():
  print('no input')
  sleep(3)

# If there's input ready, do something, else do something
# else. Note timeout is zero so select won't block at all.
while True:
    while sys.stdin in select.select([sys.stdin], [], [], 0)[0]:
        line = sys.stdin.readline()
        if line:
            something(line)
        else: # an empty line means stdin has been closed
            print('eof')
            exit(0)
    else:
        something_else()
