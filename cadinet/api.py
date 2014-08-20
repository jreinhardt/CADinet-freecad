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
from os.path import basename, dirname, join
from uuid import UUID
import os

def get_3d_data(doc,obj):
	result = {
		'facets' : [],
		'vertices' : []
	}

	if FreeCADGui:
		pos = FreeCADGui.getDocument(doc.Name).ActiveView.viewPosition().Base
		result["camera"] = {'x' : pos.x, 'y' : pos.y, 'z' : pos.z}
	else:
		result["camera"] = {'x' : 0., 'y' : 0., 'z' : 1000.}

	if obj.isDerivedFrom("Part::Feature"):
		fcmesh = obj.Shape.tessellate(0.1)
		for v in fcmesh[0]:
			result["vertices"].append((v.x,v.y,v.z))
		for f in fcmesh[1]:
			result["facets"].append(f)
	elif obj.isDerivedFrom("Mesh::Feature"):
		for p in sorted(obj.Mesh.Points,key=lambda x: x.Index):
			result["vertices"].append((p.x,p.y,p.z))
		for f in obj.Mesh.Facets:
			result["facets"].append(f.PointIndices)

	return result

