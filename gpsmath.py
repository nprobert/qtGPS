from math import sin, cos, asin, sqrt, radians, atan2

earth_flatening = 1.0/298.257223563
earth_radius = 6378137.0

#############################################################################
# GPS stuff
#############################################################################

PI = 4 * atan2(1, 1)
MPERDEG = (111.13285 * 1000.0)
RADIUS = earth_radius  # meters

def deg2rad(deg):
  global PI
  return ((deg)*PI/180.0)

def rad2deg(rad):
  global PI
  return ((rad)*180.0/PI)

def gps_bearing(lat1, lon1, lat2, lon2):
  lat1 = deg2rad(lat1)
  lon1 = deg2rad(lon1)
  lat2 = deg2rad(lat2)
  lon2 = deg2rad(lon2)
  y = sin(lon2-lon1) * cos(lat2)
  x = cos(lat1)*sin(lat2) - sin(lat1)*cos(lat2)*cos(lon2-lon1)
  bearing = rad2deg( atan2(y, x) )
  return (bearing + 360.0) % 360.0

def gps_distance(lat1, lon1, lat2, lon2):
  global RADIUS
  lat1 = deg2rad(lat1)
  lon1 = deg2rad(lon1)
  lat2 = deg2rad(lat2)
  lon2 = deg2rad(lon2)
  a = sin((lat2-lat1)/2)**2 + cos(lat1) * cos(lat2) * sin((lon2-lon1)/2)**2
  c = 2 * atan2(sqrt(a), sqrt(1 - a))
  return RADIUS * c

def gps_xy(lat1, lon1, lat2, lon2):
  global MPERDEG
  mperdeg = MPERDEG * cos(deg2rad(lat2+lat1)/2)
  x = (lon2 - lon1) * mperdeg
  y = (lat2 - lat1) * MPERDEG
  return (x, y)

def gps_xydistance(lat1, lon1, lat2, lon2):
  global MPERDEG
  mperdeg = MPERDEG * cos(deg2rad(lat2+lat1)/2)
  x = (lon2 - lon1) * mperdeg
  y = (lat2 - lat1) * MPERDEG
  dist = sqrt(x*x + y*y)
  return (x, y, dist)

#
#
#

def haversine(lat1, lon1, lat2, lon2):
  """
  Calculate the great circle distance between two points
  on the earth (specified in decimal degrees)
  """
  # convert decimal degrees to radians
  lon1, lat1, lon2, lat2 = map(radians, [lon1, lat1, lon2, lat2])

  # haversine formula
  dlon = lon2 - lon1
  dlat = lat2 - lat1
  a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
  c = 2 * asin(sqrt(a))

  # 6367 km is the radius of the Earth
  return earth_radius * c

def roydistance(lat1, lon1, lat2, lon2):
  """
  Calculate the great circle distance between two points
  on the earth (specified in decimal degrees)
  """
  # convert decimal degrees to radians
  lon1, lat1, lon2, lat2 = map(radians, [lon1, lat1, lon2, lat2])
    
  # Roy's method
  f1 = (1.0 - earth_flatening)

  top = (pow((lon2-lon1), 2) * pow(cos(lat1), 2)) + pow(lat2-lat1, 2)
  bot = pow(sin(lat1), 2) + (pow(f1, 2) * pow(cos(lat1), 2))

  return f1 * earth_radius * sqrt(top/bot)
