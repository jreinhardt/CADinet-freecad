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

from PySide import QtCore, QtGui
from FreeCADGui import PySideUic as uic
import FreeCAD, FreeCADGui
from ConfigParser import ConfigParser
from os.path import basename, dirname, join
from uuid import UUID
from hashlib import sha1

import json
import requests
from requests.auth import HTTPBasicAuth

try:
	root_dir = dirname(__file__)
	Ui_CadinetDialog,QCadinetDialog = uic.loadUiType(join(root_dir,'cadinet.ui'))
except ImportError:
	FreeCAD.Console.PrintError("uic import failed. Make sure that the pyside tools are installed")
	raise

LICENSES = {
    "CC0 1.0" : "http://creativecommons.org/publicdomain/zero/1.0/",
    "CC-BY 3.0" : "http://creativecommons.org/licenses/by/3.0/",
    "CC-BY 4.0" : "http://creativecommons.org/licenses/by/4.0/",
    "CC-BY-SA 4.0" : "http://creativecommons.org/licenses/by-sa/4.0/",
    "CC-BY-ND 4.0" : "http://creativecommons.org/licenses/by-nd/4.0/",
    "CC-BY-NC 4.0" : "http://creativecommons.org/licenses/by-nc/4.0/",
    "CC-BY-NC-SA 4.0" : "http://creativecommons.org/licenses/by-nc-sa/4.0/",
    "CC-BY-NC-ND 4.0" : "http://creativecommons.org/licenses/by-nc-nd/4.0/",
    "MIT" : "http://opensource.org/licenses/MIT", #see https://fedoraproject.org/wiki/Licensing:MIT?rd=Licensing/MIT
    "BSD 3-clause" : "http://opensource.org/licenses/BSD-3-Clause",
    "Apache 2.0" : "http://www.apache.org/licenses/LICENSE-2.0",
    "LGPL 2.1" : "http://www.gnu.org/licenses/lgpl-2.1",
    "LGPL 2.1+" : "http://www.gnu.org/licenses/lgpl-2.1",
    "LGPL 3.0" : "http://www.gnu.org/licenses/lgpl-3.0",
    "LGPL 3.0+" : "http://www.gnu.org/licenses/lgpl-3.0",
    "GPL 2.0+" : "http://www.gnu.org/licenses/gpl-2.0",
    "GPL 3.0" : "http://www.gnu.org/licenses/gpl-3.0",
    "GPL 3.0+" : "http://www.gnu.org/licenses/gpl-3.0",
}

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


licenses = sorted(LICENSES.keys())

def unpack_response(r,parent):
	if r.status_code != requests.codes.ok:
		try:
			res = r.json()
		except:
			QtGui.QErrorMessage(parent).showMessage("Request failed with %d" % r.status_code)
			return None
		else:
			QtGui.QErrorMessage(parent).showMessage(res['reason'])
			return None
	else:
		return r.json()

class CadinetDialog(QCadinetDialog):
	def __init__(self,doc,root_path):
		QCadinetDialog.__init__(self)
		self.ui = Ui_CadinetDialog()
		self.ui.setupUi(self)

		self.root_path = root_path
		self.doc = doc

		self.ui.licenseComboBox.addItems(licenses)
		self.features = []
		for obj in doc.findObjects():
			if obj.TypeId.startswith('Sketcher'):
				continue
			self.features.append(obj.Name)
		self.ui.featureToPreviewComboBox.addItems(self.features)

		urlValidator = QtGui.QRegExpValidator()
		urlValidator.setRegExp(QtCore.QRegExp('https?://[-A-Za-z0-9+&@#/%?=~_|!:,.;]+[-A-Za-z0-9+&@#/%=~_|]'))

		self.ui.cadinetUrlLineEdit.setValidator(urlValidator)
		self.ui.userUrlLineEdit.setValidator(urlValidator)
		self.ui.derivativeOfLineEdit.setValidator(urlValidator)

		#set default values
		config = ConfigParser()
		config.read(join(self.root_path,'cadinet.cfg'))
		if config.has_section('user'):
			if config.has_option('user','name'): self.ui.fullNameLineEdit.setText(config.get('user','name'))
			if config.has_option('user','email'): self.ui.emailAddressLineEdit.setText(config.get('user','email'))
			if config.has_option('user','url'): self.ui.userUrlLineEdit.setText(config.get('user','url'))

		if config.has_section('cadinet'):
			if config.has_option('cadinet','url'): self.ui.cadinetUrlLineEdit.setText(config.get('cadinet','url'))
			if config.has_option('cadinet','username'): self.ui.usernameLineEdit.setText(config.get('cadinet','username'))
			if config.has_option('cadinet','password'): self.ui.passwordLineEdit.setText(config.get('cadinet','password'))

		self.ui.thingTitleLineEdit.setText(doc.Name)
		self.ui.descriptionPlainTextEdit.setPlainText(doc.Comment)
		self.ui.licenseComboBox.setCurrentIndex(licenses.index(doc.License))
		if not doc.ActiveObject is None:
			self.ui.featureToPreviewComboBox.setCurrentIndex(self.features.index(doc.ActiveObject.Name))
		else:
			self.ui.featureToPreviewComboBox.setCurrentIndex(len(self.features)-1)

		self.accepted.connect(self.on_accepted)


	@QtCore.Slot(bool)
	def on_userSaveButton_clicked(self,checked):
		config = ConfigParser()
		config.read(join(self.root_path,'cadinet.cfg'))

		if not config.has_section('user'):
        		config.add_section('user')
		config.set('user','name',self.ui.fullNameLineEdit.text())
		config.set('user','email',self.ui.emailAddressLineEdit.text())
		config.set('user','url',self.ui.userUrlLineEdit.text())
		with open(join(self.root_path,'cadinet.cfg'),'w') as fid:
			config.write(fid)

	@QtCore.Slot(bool)
	def on_cadinetSaveButton_clicked(self,checked):
		config = ConfigParser()
		config.read(join(self.root_path,'cadinet.cfg'))

		if not config.has_section('cadinet'):
        		config.add_section('cadinet')
		config.set('cadinet','url',self.ui.cadinetUrlLineEdit.text())
		config.set('cadinet','username',self.ui.usernameLineEdit.text())
		config.set('cadinet','password',self.ui.passwordLineEdit.text())
		with open(join(self.root_path,'cadinet.cfg'),'w') as fid:
			config.write(fid)

	def on_accepted(self):
		#upload the thing
		thing = {
			'id' : unicode(UUID(hex=sha1(self.doc.Content).hexdigest()[:32])),
			'title' : self.ui.thingTitleLineEdit.text(),
			'description' : self.ui.descriptionPlainTextEdit.toPlainText(),
			'license' : licenses[self.ui.licenseComboBox.currentIndex()],
		}
		thing['license_url'] = LICENSES[thing["license"]]

		if self.ui.updateDocumentPropertiesCheckBox.isChecked():
			self.doc.Comment = thing["description"]
			self.doc.License = thing["license"]
			self.doc.LicenseURL = thing["license_url"]
			self.doc.save()

		auth = HTTPBasicAuth(self.ui.usernameLineEdit.text(),self.ui.passwordLineEdit.text())

		headers = {'content-type': 'application/json'}

		url = self.ui.cadinetUrlLineEdit.text() + '/thing'

		if not url.startswith('https'):
			mBox = QtGui.QMessageBox()
			mBox.setIcon(mBox.Critical)
			mBox.setText('Insecure connection to cadinet')
			mBox.setInformativeText('Your username and password are transmitted to the cadinet over an unencryption connection. This is only acceptable for local development, if the cadinet is accessible from the internet, make sure it can supports https and adjust the URL. Do you want to proceed over a unencrypted connection?')
			mBox.setStandardButtons(mBox.Yes| mBox.No)
			mBox.setDefaultButton(mBox.No)
			if mBox.exec_() == mBox.No:
				return

		r = requests.post(url,data=json.dumps({'thing' : thing}),headers=headers,auth=auth)

		res = unpack_response(r,self)
		if res is None: return

		res = r.json()
		#upload fcstd file
		if self.doc.FileName:
			files = {'file' : (basename(self.doc.FileName),open(self.doc.FileName,'rb'))}
			r_fcstd = requests.post(res['fcstd_url'],files=files,auth=auth)

			res_fcstd = unpack_response(r_fcstd,self)
			if res_fcstd is None: return


		if self.ui.upload3DPreviewCheckBox.isChecked():
			data = json.dumps(get_3d_data(self.doc,self.doc.getObject(self.ui.featureToPreviewComboBox.currentText())))
			r_3dview = requests.post(res['3dview_url'],data=data,headers=headers,auth=auth)

			res_fcstd = unpack_response(r_fcstd,self)
			if res_fcstd is None: return
