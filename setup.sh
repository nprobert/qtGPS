#!/bin/bash

# Python 3
echo "Python 3 Software:"
sudo apt-get -y --ignore-missing install python3-all python3-dev python3-tk idle3 python3-pip python3-pyqt5 python3-serial python3-can python3-protobuf python3-numpy python3-pil.imagetk python3-gi
sudo apt-get -y --ignore-missing install spyder3 python3-pyside2.*
sudo apt-get -y --ignore-missing install gpsd gpsd-clients gpsbabel libgps-dev

# Python addons
echo "Python 3 Packages:"
python3 -m pip install --upgrade pip
python3 -m pip install --upgrade pyserial matplotlib numpy scipy gps gpxpy maidenhead virtualenv virtualenvwrapper
