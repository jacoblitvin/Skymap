#!/usr/bin/env python3

#  
# 
# skymap.py -- Produces map of solar system bodies
# 
# Jacob Litvin -- 2021-06-04
#

import requests
from astroquery.jplhorizons import Horizons
import sys, os
from datetime import datetime
import numpy as np
from astropy.time import Time
from datetime import datetime,timedelta
from geopy.geocoders import Nominatim

while True:
	app = Nominatim(user_agent='skymap')
	city = str(input("\nWelcome to skymap. Where would you like to see the solar system from?\nEnter a city, state, country, or street address.\n\n"))
	print()
	try:
		location = app.geocode(city)
	except NameError:
		print('The entered location was not recognized, or in the wrong format. Try again.',file=sys.stderr)
	if location == None:
		print('The entered location was not recognized. Try again.',file=sys.stderr)	
		continue
	else:
		instr = str(input('Was %s your desired location? Enter <y> if yes or any other key if no.\n\n' % (location)))
		if instr == 'y':
			break
		else:
			continue

print('\nInitializing location data for %s...\n' % (location))

#instantiating latitude and longitude
lat = location[1][0]
lon = location[1][1]
#instantiating current date,time
now = datetime.now()
#epochs -1yr and +1yr
start = str(now-timedelta(days=370))
end = str(now+timedelta(days=370))
#calculating local sidereal time
astronow = Time(datetime.utcnow(),scale='utc')
astronow.format = 'jd'
j2 = Time('2000-01-01 12:00:00',scale='utc')
j2.format = 'jd'
j2d = astronow-j2
ut = datetime.utcnow().time()
uth = ut.hour+(ut.minute/60)+(ut.second/3600)+(ut.microsecond/3600000000)
lst = float(str(100.46+0.985647*j2d+lon+15*uth)) % 360
if lst < 0:
	lst = lst+360

objectfile = open("objects.txt", "r")
objectlist = objectfile.readlines()

tbl_data = []
#reading object list and querying Horizons for ephems
for line in objectlist:
	id_, name = line.strip().split()
	print(f'Fetching data for {name}, starting on {start} and ending on {end}...')
	obj = Horizons(id=id_, location='geocentric', epochs={"start": start, "stop": end, 'step': '10d'})
	try:
		eph = obj.ephemerides()
		tbl_data.append({"id" : name, "proper" : eph['targetname'], "date": eph['datetime_str'], "ra" : eph['RA'], "dec" : eph["DEC"]})
	except ValueError:
		print(f"Unable to find Data for {name}",file=sys.stderr)
		
#parsing horizons data for RA and DEC
radecs = []
for i in tbl_data:
	radec = [np.deg2rad(i['ra']),np.deg2rad(i['dec'])]
	radecs.append(radec)

#defining hour angle 
def ra_to_ha(lst,ra):
	ha = lst-ra
	for j in ha:
		if j < 0:
			j = j+2*np.pi
	return ha

#defining altitude and azimuth
def radec_to_alt(ra,dec,lat,lst):
	ha = ra_to_ha(lst,ra)
	a = np.sin(dec)*np.sin(lat)+np.cos(dec)*np.cos(lat)*np.cos(ha)
	alt = np.arcsin(a)
	return alt	

def radec_to_az(ra,dec,lat,lst):
	ha = ra_to_ha(lst,ra)
	alt = radec_to_alt(ra,dec,lat,lst)
	b = (np.sin(dec)-np.sin(alt)*np.sin(lat))/(np.cos(alt)*np.cos(lat))
	A = np.arccos(b)
	az = dec
	for i,j in enumerate(ha):
		if np.sin(j) < 0:
			az[i] = A[i]
		else:
			az[i] = 2*np.pi-A[i]
	return az

altaz = []
#convert RA and DEC data to ALT and AZ arrays
for i in range(int(len(radecs))):
	altaz.append([np.zeros(int(len(radecs[0][0]))),np.zeros(int(len(radecs[0][0])))])

for i,j in enumerate(radecs):
	altaz[i][0] = radec_to_alt(j[0],j[1],np.deg2rad(lat),np.deg2rad(lst))
	altaz[i][1] = radec_to_az(j[0],j[1],np.deg2rad(lat),np.deg2rad(lst))

import matplotlib.pyplot as plt

objs = ['Mercury','Venus','Mars','Jupiter','Saturn','Uranus','Neptune','Pluto','Moon']

colors = ['olive','darkorange','red','salmon','sandybrown','purple','blue','skyblue','gray']

plt.style.use('dark_background')

fig = plt.figure()
ax = fig.add_subplot(111,polar=True)

ax.set_title('The sky above %s on %s\nNorth at $0^{0}$ Azimuth\nHorizon at $0^{0}$ Altitude' % (location,str(tbl_data[0]['date'][37]))) 
ax.set_theta_zero_location('N')
ax.set_theta_direction(-1)
ax.set_ylabel('Azimuth')
ax.yaxis.set_label_coords(-0.05,.5)
ax.set_xlabel("The dots represent each object's location at time above.\nThe lines they trace represent objects' locations at this time of day, every ten days, during the period of two years starting 370 days ago.") 
ax.set_yticks([np.pi/6,np.pi/3,np.pi/2])
ax.set_ylim(0,np.pi/2)
ax.set_yticklabels(['$60^{0}$','$30^{0}$','$0^{0}$'])

for i,j in enumerate(altaz):
	if j[0][37] > 0: #filters for objects currently above horizon
		ax.scatter(j[1][37],abs(np.pi/2-j[0][37]),color=colors[i],label=objs[i])
	
ax.legend()
	
for i,j in enumerate(altaz):
	if j[0][37] > 0: #filters for objects currently above horizon
		ax.plot(j[1],abs(np.pi/2-j[0]),color=colors[i],label=None)

plt.show()

print()
input('Press <Enter> to exit...')
print()
