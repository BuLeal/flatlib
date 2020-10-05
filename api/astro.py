from flatlib import const
from flatlib.chart import Chart
from flatlib.datetime import Datetime
from flatlib.geopos import GeoPos
from datetime import datetime

from http.server import BaseHTTPRequestHandler
import dateutil.parser
import urllib.parse

import pytz
	
import json
import numpy as np

import logging

from geopy.geocoders import Nominatim

def angle_dif(a,b):
	dif = (b-a+360)%360
	return(dif)


def get_location(Location_name):
	geolocator = Nominatim(user_agent="AstroMBTI")
	print(geolocator)
	#print(person,people[person]["Location"])
	try:
		location = geolocator.geocode(Location_name)
		#print(location.raw)
	except:
		print("Error in",Location_name)
		return()
	url = "https://www.google.com.br/maps/@"+str(location.latitude)+","+str(location.longitude)+",13z"
	return([location.latitude,location.longitude,url,location.raw])
	# elif "lat" in location and 'lon' in location:
	# 	return([location.lat,location.lon,location.raw])
	# else:
	# 	return(location.raw)

def strfdelta(td, fmt):
	# Get the timedelta’s sign and absolute number of seconds.
	sign = "-" if td.days < 0 else "+"
	secs = abs(td).total_seconds()

	# Break the seconds into more readable quantities.
	days, rem = divmod(secs, 86400)  # seconds per day: 24 * 60 * 60
	hours, rem = divmod(rem, 3600)  # seconds per hour: 60 * 60
	mins, secs = divmod(rem, 60)

	# Format (as per above answers) and return the result string.
	return(sign+"{:02d}".format(int(hours))+":"+"{:02d}".format(int(mins)))

"""def timezone_offset(lat,lon,dt = None):
	import pytz
	from tzwhere import tzwhere
	# if dt:
	# 	dt = dt.utcnow()
	# 	dt.replace(tzinfo=None)
	print(str(dt))
	tzwhere = tzwhere.tzwhere()
	timezone_str = tzwhere.tzNameAt(lat,lon) # Seville coordinates
	print(timezone_str)
	# local = pytz.timezone(timezone_str)#pytz.timezone ("America/Los_Angeles")
	# print(local)

	tz = pytz.timezone(timezone_str)
	print(tz)
	# tz = pytz.timezone(timezone_str).localize(dt)
	# print(tz)
	utc_offset = dt(tz).utcoffset()
	print(utc_offset)
	return(utc_offset)

	##########################

	offset_seconds = tz.utcoffset(dt).seconds

	offset_hours = offset_seconds / 3600.0

	offset_formated = "{:+d}:{:02d}".format(int(offset_hours), int((offset_hours % 1) * 60))
	return(offset_formated)

	print(tz)
	return(tz)
	naive = dt.replace(tzinfo=tz)
	local_dt = local.localize(naive, is_dst=None)
	#local = pytz.timezone ("America/Los_Angeles")
	#naive = datetime.strptime ("2001-7-3 10:11:12", "%Y-%m-%d %H:%M:%S")
	#local_dt = local.localize(naive, is_dst=None)
	print(pytz.utc.normalize(local_dt))
	#print(pytz.utc.normalize(dt))
	utc_dt = local_dt.astimezone(pytz.utc)
	
	#timezone = pytz.timezone(timezone_str)
	#print(timezone)
	print(utc_dt)
	return(strfdelta(local.utcoffset(dt),"%s%H:%M:%S"))
	#> datetime.timedelta(0, 7200)
"""

def timezone_offset(lat,lng,date_time):
	from timezonefinder import TimezoneFinder
	tf = TimezoneFinder()
	"""
	returns a location's time zone offset from UTC in minutes.
	"""
	tz_target = pytz.timezone(tf.certain_timezone_at(lng=lng, lat=lat))
	if tz_target is None:
		print("No timezone found in",str((lat,lng)))
		return()
	# ATTENTION: tz_target could be None! handle error case
	#date_time = date_time.tzinfo=None#tzinfo=tz_target)#.utcoffset()
	#print("tzinfo = ",str(date_time.tzinfo))
	dt = date_time
	if dt.tzinfo is None:
		dated_target = tz_target.localize(dt)
		utc = pytz.utc
		dated_utc = utc.localize(dt)
		#return (dated_utc - dated_target).total_seconds() / 60 / 60
		return(strfdelta(dated_utc - dated_target,"%s%H:%M:%S"))
	else:
		print(dt.tzinfo)
		return()


def get_astrological(date_time,coordinates,timezone):
	if isinstance(coordinates, (list,)):
		if len(coordinates) == 1:
			coordinates = coordinates[0]
		else:
			coord = coordinates[:2]
	else:
		return()
	if isinstance(coordinates, (str,)):
		if "," in coordinates:
			coord = coordinates.split(',')
			coord[0]=coord[0].lstrip()
			coord[1]=coord[1].lstrip()
			# if len(coord[1])>2:
			#	coord[1] = coord[1][:1]+":" +coord[1][2:]
		#		print(coord[1])
	
	flatlib_pos = GeoPos(coord[0],coord[1])
	flatlib_date_time = Datetime(date_time.strftime("%Y/%m/%d"), date_time.strftime('%H:%M'), timezone)
	chart = Chart(flatlib_date_time, flatlib_pos)

	astro = {}
	for obj in [chart.get(const.ASC)]:
	#	#print(obj)
		astro[obj.id] = {'sign':obj.sign,'lon':obj.lon}
	
	# for obj in chart.houses:
	# 	astro[obj.id] = {'sign':obj.sign,'lon':obj.lon,'signlon':obj.signlon,'size':30-obj.size}

	for obj in chart.objects: #Planets
		#print(obj.id,obj.sign,obj.lon,obj.signlon,obj.lonspeed)
		astro[obj.id] = {'sign':obj.sign,'lon':obj.lon,'speed':obj.lonspeed}
		try:
			gender = obj.gender()
			astro[obj.id].update({'gender':gender})
		except:
			pass
		try: 
			mean_motion = obj.meanMotion()
			if mean_motion:
				astro[obj.id].update({'speed':obj.lonspeed/mean_motion})
		except: pass
		try: astro[obj.id].update({'fast':str(obj.isFast())})
		except: pass
		for house in chart.houses:
			if house.hasObject(obj):
				astro[obj.id].update({'house':house.id})
	moon_phase = angle_dif(astro['Moon']['lon'],astro['Sun']['lon'])
	astro['Moon'].update({
		'phase':moon_phase,
	})
	ASC_LON = chart.get(const.ASC).lon
	for obj in astro.keys():
		if 'lon' in astro[obj].keys():
			angle = angle_dif(ASC_LON,astro[obj]['lon'])
			astro[obj].update({'lon':angle,'position':[np.sin(angle* np.pi / 180.),np.cos(angle* np.pi / 180.)]})
	return(astro)



def planets_aspects(astrological_data):
	#https://en.wikipedia.org/wiki/Orb_(astrology)
	# ASPECT, ANGLE, Max ORB
	aspects = [
		('Conjunction',0,10),
		('Sextile',60,4),
		('Square',90,10),
		('Trine',120,10),
		('Opposition',180,10),
		('Quincunx',150,3.5),
		('Semi-sextile',30,1.2),
		('Quintile',72,1.2),
		('Semi-Square',45,2),
		
	]
	result = []
	planets = ['Sun','Moon','Mercury','Venus','Mars','Jupiter','Saturn','North Node']#,'South Node']
	p_list = planets
	for planet in planets:
		#print(planet,astrological_data[planet]['lon'])
		if len(p_list):
			p_list = p_list[1:]
		else: continue
		for p in p_list:
			angle = abs(astrological_data[planet]['lon']-astrological_data[p]['lon'])
			if angle > 180: angle = 360 - angle
			#result.update({"aspect "+planet+" X "+p:angle})
			
			if any (aspect_ang-max_orb <= angle <= aspect_ang+max_orb for (aspect, aspect_ang, max_orb) in aspects):
				for (aspect, aspect_ang, max_orb) in aspects:
					if aspect_ang-max_orb <= angle <= aspect_ang+max_orb:
						
						orb = abs(angle-aspect_ang)
						
						#Adicionando um fator de imprecisão:
						plan_speed = astrological_data[planet]['speed'] if 'speed' in astrological_data[planet].keys() else 1
						p_speed = astrological_data[p]['speed'] if 'speed' in astrological_data[p].keys() else 1
						orb += abs(plan_speed - p_speed)*360/24/60*5
						if orb == 0: orb=0.1
						orb = 1/orb
						#Considerando peso de cada fator:
						orb*=max_orb

						result.append( ( [planet,p], aspect, round(orb,4)) )
			else:
						pass
						#result.update({"aspect "+planet+" X "+p:(None,0)})
	
	return(result)


class handler(BaseHTTPRequestHandler):
	def __init__(self, *args, **kwargs):
		super(handler, self).__init__(*args, **kwargs)	
	def do_GET(self):
		parsed_path = urllib.parse.urlparse(self.path)
		query = urllib.parse.parse_qs(parsed_path.query)
		print(query)
		# print(parsed_path)

		#Standard
		datetime_raw = '1991-May-01 08:35AM'
		date_time = None
		latlong_raw = [-23.6713029,-46.5690634]
		timezone = None

		if "datetime" in query:
			datetime_raw = query['datetime'][0]
			print(datetime_raw)
			try:
				date_time = datetime.strptime(datetime_raw, "%Y-%m-%d %H:%M")
			except:
				date_time = dateutil.parser.parse(datetime_raw)
				print(date_time)
		elif ('date' in query) and ('time' in query):
			try:
				date = datetime.strptime(query['date'][0], "%Y-%m-%d")
				time = datetime.strptime(query['time'][0], "%H:%M")
				date_time = date+time
			except:
				date_time = dateutil.parser.parse(query['date'][0] +" "+ query['time'][0])
		else:
			print('datetime not found')
			date_time = None
		#if date_time: date_time=date_time.replace(tzinfo=None)

		if 'latlong' in query:
			print(query['latlong'])
			try:
				latlong_raw = query['latlong'][0].split(',')
			except:
				print("Oooops, latlong format do not match!")
			latlong = [float(latlong_raw[0]),float(latlong_raw[1])]
		elif ('lat' in query) and ('lng' in query):
			lat = query['lat'][0]
			lng = query['lng'][0]
			try:
				latlong = [float(lat),float(lng)]
			except:
				print("Oooops, latlong format do not match!")
		elif 'placename' in query:
			print()
			placename = query['placename'][0]
			print(placename)
			latlong = get_location(placename)
			print(str(latlong))
			if isinstance(latlong, (list,)) and len(latlong) >= 2:
				latlong = list(latlong)
				print("https://www.google.com.br/maps/@"+str(latlong[0])+","+str(latlong[1])+",13z")
			else:
				print("Error on getting location.")
		else:
			print('lat long not found')
			print("Using",latlong_raw,"as Standard")
			latlong = [float(latlong_raw[0]),float(latlong_raw[1])]

		if "timezone" in query:
			timezone = query['timezone'][0]
			print(timezone)
		elif isinstance(latlong, (list,)) and len(latlong) >= 2 and date_time:
			timezone = timezone_offset(latlong[0],latlong[1],date_time)
		else:
			timezone = None
			print("No timezone could be found")

		print("Getting astrological data for:",date_time,latlong,timezone)
		if date_time and latlong and timezone:
			astro = get_astrological(date_time,latlong,timezone)
		else:
			astro = None
		if astro:
			aspect_list = planets_aspects(astro)
			print(aspect_list)
		else: aspect_list = None
		answer = {
			"query":query,
			"planets":astro,
			"aspects":aspect_list,
			"parameters":{"datetime":str(date_time),"latlong":latlong,"timezone":timezone}
			}
		self.send_response(200)
		self.send_header('Content-type', 'application/json')
		self.send_header("Access-Control-Allow-Origin", "*")
		self.end_headers()
		self.wfile.write(json.dumps(answer,ensure_ascii=False).encode('utf8'))
		return


if __name__ == '__main__':
	from http.server import BaseHTTPRequestHandler, HTTPServer
	server = HTTPServer(('localhost', 8080), handler)
	print('Serving on http://localhost:8080')
	print('Example: http://localhost:8080/?datetime=1990-May-21%2008:00PM&timezone=-2:00&latlong=-50.00,30.01')
	print('Starting server, use <Ctrl-C> to stop')
	server.serve_forever()