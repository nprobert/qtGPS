# qtGPS
Python Qt6 GPS Tool, similar to xgps

  SETUP

python3 -m venv venv
source venv/bin/activate
python3 -m pip install --upgrade pip
python3 -m pip install gps simpleaudio gpxpy pyyaml PySide6
pip list > requirements.txt

  RUN

source venv/bin/activate
python gps_tool.py &
deactivate
