#Copyright (c) 2014 Johannes Reinhardt <jreinhardt@ist-dein-freund.de>
#
#Permission is hereby granted, free of charge, to any person obtaining a copy
#of this software and associated documentation files (the "Software"), to deal
#in the Software without restriction, including without limitation the rights
#to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
#copies of the Software, and to permit persons to whom the Software is
#furnished to do so, subject to the following conditions:
#
#The above copyright notice and this permission notice shall be included in
#all copies or substantial portions of the Software.
#
#THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
#IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
#FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
#AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
#LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
#OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
#THE SOFTWARE.

import requests
from requests.auth import HTTPBasicAuth
import FreeCAD
import FreeCADGui
import json
from hashlib import sha1
from os.path import basename
from ConfigParser import ConfigParser

#Configuration

#to use this macro, you need to register with an instance of cadinet
#(https://github.com/jreinhardt/CADinet) to obtain a username and password. Then
#you have to create a configuration file called cadinet.cfg and enter the
#credentials you got from the cadinet, as well as the url of the cadinet.

config = ConfigParser()
config.read('cadinet.cfg')


USERNAME = config.get('user','username')
PASSWORD =  config.get('user','password')
CADINET_HOST = config.get('cadinet','url')

headers = {'content-type': 'application/json'}
auth = HTTPBasicAuth(USERNAME,PASSWORD)

doc = FreeCAD.ActiveDocument

if not doc is None:
		#upload the thing
		thing = {
			'id' : unicode(UUID(hex=sha1(doc.Content).hexdigest[:32])),
			'title' : doc.Name,
			'description' : doc.Comment,
			'license' : doc.License,
			'license_url' : doc.LicenseURL
		}

		content = {
			'thing' : thing
		}

		r = requests.post(CADINET_HOST + '/thing',data=json.dumps(content),headers=headers,auth=auth)

		if r.status_code != requests.codes.ok:
			try:
				res = r.json()
			except:
				raise RuntimeError("Request failed with status code %d" % r.status_code)
			else:
				raise RuntimeError(res)

		res = r.json()

		#upload fcstd file
		if doc.FileName:
			files = {'file' : (basename(doc.FileName),open(doc.FileName,'rb'))}
			r_fcstd = requests.post(res['fcstd_url'],files=files,auth=auth)

			res_fcstd = r_fcstd.json()

			if r_fcstd.status_code != requests.codes.ok:
				raise RuntimeError(res_fcstd)

		#upload 3D preview
		if FreeCADGui:
			pos = FreeCADGui.ActiveDocument.ActiveView.viewPosition().Base
			camera = {'x' : pos.x, 'y' : pos.y, 'z' : pos.z}
		else:
			camera = {'x' : 0., 'y' : 0., 'z' : 1000.}

		obj = doc.ActiveObject

		facets = []
		vertices = []
		if doc.ActiveObject.isDerivedFrom("Part::Feature"):
			fcmesh = obj.Shape.tessellate(0.1)
			for v in fcmesh[0]:
				vertices.append((v.x,v.y,v.z))
			for f in fcmesh[1]:
				facets.append(f)
		elif obj.isDerivedFrom("Mesh::Feature"):
			for p in sorted(obj.Mesh.Points,key=lambda x: x.Index):
				vertices.append((p.x,p.y,p.z))
			for f in obj.Mesh.Facets:
				facets.append(f.PointIndices)

		content = {
			'camera' : camera,
			'facets' : facets,
			'vertices' : vertices
		}

		r_3dview = requests.post(res['3dview_url'],data=json.dumps(content),headers=headers,auth=auth)

		res_3dview = r_3dview.json()

		if r_3dview.status_code != requests.codes.ok:
			raise RuntimeError(res_3dview)