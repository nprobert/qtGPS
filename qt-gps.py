#! /usr/bin/python3

import os
import sys
import yaml

from math import radians
from datetime import datetime
from time import strftime, time
from pprint import pprint

from gps import *
import gpxpy

from PySide6.QtGui import *
from PySide6.QtWidgets import QApplication, QMainWindow, QGraphicsEllipseItem, QFileDialog, QGraphicsScene, QGraphicsProxyWidget
from PySide6.QtCore import QObject, Slot, Signal, QThread, QDir, QRect

import matplotlib as mp
import matplotlib.pyplot as plot
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
from matplotlib.backends.qt_compat import QtCore, QtWidgets
from matplotlib import cm

from MainWindow import Ui_MainWindow

import maidenhead as mh

from utils.configs import *

##############################################################################
# log
##############################################################################

#if not os.path.isdir("logs"):
#  os.mkdir("logs")

fix_status = [
  'Normal', 'DGPS', 'RTK FixPt', 'RTK Float', 'DR Fix', 'GNSSDR', 'Surveyed', 'Simulated', 'P(Y) Fix'
  ];

fix_mode = [
  '0=None', '1=No', '2=2D', '3=3D'
  ];

gpsd_host="127.0.0.1"
gpsd_report = ()

##############################################################################
# thread
##############################################################################

class DataSignal(QObject):
  sig = Signal(int)

class DataThread(QThread):
  def __init__(self, parent=None):
    super(DataThread, self).__init__(parent)
    self.new_data = DataSignal()
  
  def run(self):
    global gpsd_host, gpsd_report
    gpsd = gps(host=gpsd_host, mode=WATCH_ENABLE|WATCH_NEWSTYLE) 

    while not self.isInterruptionRequested():
      gpsd_report = gpsd.next()  # wait for next packet
      self.new_data.sig.emit(1)
  
  def stop(self):
    self.requestInterruption()
    self.wait()

##############################################################################
# plot
##############################################################################
  
##############################################################################
# main
##############################################################################

class MainWindow(QMainWindow, Ui_MainWindow):
  def __init__(self, *args, obj=None, **kwargs):
    super(MainWindow, self).__init__(*args, **kwargs)
    self.setupUi(self)

class QtGPSWindow(MainWindow):
  def __init__(self, *args, obj=None, **kwargs):
    super(QtGPSWindow, self).__init__(*args, **kwargs)

    self.exitButton.clicked.connect(self.exit_button)
    self.toggleLogging.clicked.connect(self.toggle_logging)

    # GPS log
    self.gpx = gpxpy.gpx.GPX()
    # Create first track in our GPX:
    self.gpx_track = gpxpy.gpx.GPXTrack()
    self.gpx.tracks.append(self.gpx_track)
    # Create first segment in our GPX track:
    self.gpx_segment = gpxpy.gpx.GPXTrackSegment()
    self.gpx_track.segments.append(self.gpx_segment)

    self.log_enabled = 0
    self.dirname = "."
    self.num_count = 0
    self.num_points = 0

    self.my_thread = DataThread()

    self.txtSatellites.setReadOnly(True)
    self.black = QColor(0,0,0)
    self.gray = QColor(128,128,128)
    self.red = QColor(255,0,0)
    self.orange = QColor(255,80,0)
    self.yellow = QColor(255,211,0)
    self.green = QColor(0,255,0)
    self.blue = QColor(0,0,255)
    self.white = QColor(255,255,255)
        
    self.scene = QtWidgets.QGraphicsScene()
    self.viewSatellites.setScene(self.scene)
    self.viewSatellites.scale(0.65, 0.65)

  @Slot(list)
  def update_data(self, x):
    global gpsd_report
    report = gpsd_report

    # make sure is good report
    try:
      if not 'class' in report:
        return
    except:
      return
    
    # GPS messages
    if report['class'] == 'TPV': 
      status = getattr(report, 'status', 0)
      mode = getattr(report, 'mode', 0)
      time = getattr(report, 'time', 0)
      lat = getattr(report, 'lat', 0.0)
      lon = getattr(report, 'lon', 0.0)
      elev = getattr(report, 'altHAE', 0.0)   # meters
      heading = getattr(report, 'track', 0.0)
      speed = getattr(report, 'speed', 0.0)   # m/sec
      
      self.txtStatus.setText(fix_status[status])
      self.txtMode.setText(fix_mode[mode])
      self.txtTime.setText(time)
      self.txtLatitude.setText("%10.7f" %(lat))
      self.txtLongitude.setText("%10.7f" % (lon))
      self.txtAltitude.setText("%7.2f" % (elev))
      self.txtHeading.setText("%7.2f" % (heading))
      self.txtSpeed.setText("%7.2f" % (speed))

      self.txtGrid.setText(mh.to_maiden(lat, lon))

      if self.log_enabled:
        point = gpxpy.gpx.GPXTrackPoint(lat, lon, elevation=elev)
        point.time = datetime.now()
        self.gpx_segment.points.append(point)
        self.num_points += 1
      self.num_count += 1
      self.txtCount.setText(str(self.num_count))
        
    elif report['class'] == 'SKY':
      self.txtHDOP.setText(str(getattr(report, 'hdop', 0.0)))
      self.txtVDOP.setText(str(getattr(report, 'vdop', 0.0)))

      try:
        satellites = report['satellites']

        txt = "%4s %4s %4s %3s %1s" % ('PRN', 'Azim', 'Elev', 'SNR', 'Used')
        self.txtSatellites.setStyleSheet("background-color: rgb(0, 0, 0)")
        self.txtSatellites.setTextColor(self.white)
        self.txtSatellites.setFontWeight(QFont.Bold)
        self.txtSatellites.setText(txt)
      
        prns = []
        radius = []
        theta = []
        colors = []
        markers = []

        for satellite in satellites:
          prn = int(satellite['PRN'])
          azim = int(satellite['az'])
          elev = int(satellite['el'])
          snr = int(satellite['ss'])
          used = int(satellite['used'])
#          health = satellite['health']

          # don't show if not visible
          if azim >= 360 or elev < -10 or elev > 90:
            continue;
        
          cname = '#000000'
          color = self.black
          if snr < 12:
            cname = '#808080'
            color = self.gray
          elif snr < 30:
            cname = '#ff0000'
            color = self.red
          elif snr < 36:
            cname = '#ffd300'
            color = self.yellow
          elif snr < 42:
            cname = '#00ff00'
            color = self.green
          else:
            cname = '#0000ff'
            color = self.blue
        
          txt = "%4u %4u %4u %3u %1u" % (prn, azim, elev, snr, used)
          self.txtSatellites.setTextColor(color)
          if used:
            self.txtSatellites.setFontWeight(QFont.Bold)
          else:
            self.txtSatellites.setFontWeight(QFont.Normal)
          self.txtSatellites.append(txt)
        
          prns.append(prn)
          theta.append(radians(float(azim)))
          radius.append(float(elev))
          colors.append(cname)
          if used:
            markers.append(ord('P'))
          else:
            markers.append(ord('+'))

        area = 100
        figure = Figure()
        polar = figure.add_subplot(111, projection='polar')
        polar.scatter(theta, radius, c=colors, s=area, cmap=None, alpha=0.75)
        polar.set_rorigin(90.0)
        polar.set_xticklabels([])
        polar.set_yticklabels([])
        for i, prn in enumerate(prns):
          polar.annotate(str(prn), (theta[i], radius[i]))
    
        polar.set_theta_direction(-1)
        polar.set_theta_zero_location('N', offset=0)

        canvas = FigureCanvas(figure)
        self.scene.clear()
        self.scene.addWidget(canvas)
        h = float(self.scene.height()) / 2.0
        w = float(self.scene.width()) / 2.0
        self.viewSatellites.centerOn(w,h)
        self.viewSatellites.show()

      except:
        pass

    self.show()
  
  def toggle_logging(self):
    if self.log_enabled:
      self.log_enabled = 0
#      self.dir_dialog()
      self.save_log()
      self.toggleLogging.setText("Start")
    else:
      self.log_enabled = 1
      self.toggleLogging.setText("Stop")
      
  def dir_dialog(self):
    dirdialog = QFileDialog(self)
    dirdialog.setDirectory(QDir.currentPath())
    dirdialog.setDefaultSuffix("gpx")
    dirdialog.setFileMode(QFileDialog.Directory)
    dirdialog.setOption(QFileDialog.ShowDirsOnly, True)
    selected = dirdialog.exec()
    if selected:
      dirname = dirdialog.selectedFiles()[0]
#      self.outputDir.setText(dirname)
      self.dirname = dirname
    
  def save_log(self):
    if self.num_points:
      self.num_points = 0
      log = open(strftime(self.dirname + "/track-%Y%m%d-%H%M.gpx"), 'w')
      log.write(self.gpx.to_xml())
      log.close()
      self.gpx_segment = gpxpy.gpx.GPXTrackSegment()

  def start_thread(self):
    if not self.my_thread.isRunning():
      self.my_thread.new_data.sig.connect(self.update_data)
      self.my_thread.start()
      self.my_thread.setTerminationEnabled(True)
      
  def stop_thread(self):
    self.my_thread.stop()
    self.my_thread.wait(3)
    self.save_log()
    
  def closeEvent(self, event):
    self.stop_thread()
    event.accept()
    sys.exit(0)
  
  def exit_button(self):
    self.stop_thread()
    if self.log_enabled:
      self.toggle_logging()
      self.log_enabled = 0
    sys.exit(0)

cfg = ConfigurationFile(__file__)
config = cfg.read_config()
if 'gpsd_host' in config:
  gpsd_host = config['gpsd_host']

if __name__ == '__main__':
  app = QApplication(sys.argv)

  window = QtGPSWindow()
  window.show()
  window.start_thread()
  ret = app.exec()
  sys.exit(ret)
