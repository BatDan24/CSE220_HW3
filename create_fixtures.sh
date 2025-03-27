#!/bin/bash
rm -f fixtures.zip
zip -r fixtures.zip include/*soln.h src/*soln.c tests/include tests/src images/originals CMakeLists.txt deadline.py 
