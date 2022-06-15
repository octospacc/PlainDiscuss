#!/usr/bin/env python3
""" =============================== |
| PlainDiscuss                      |
|                                   |
| Licensed under the AGPLv3 license |
| Copyright (C) 2022, OctoSpacc     |
| =============================== """

import json
from ast import literal_eval
from flask import Flask, request, send_file
#from APIConfig import *

App = Flask(__name__)

def ReadFile(p):
	try:
		with open(p, 'r') as f:
			return f.read()
	except Exception:
		print("Error reading file {}".format(p))
		return None

def WriteFile(p, c):
	try:
		with open(p, 'w') as f:
			f.write(c)
		return True
	except Exception:
		print("Error writing file {}".format(p))
		return False

def SetConfig():
	Config = {
		'Development': False,
		'Port': 8080}
	File = ReadFile('Config.json') 
	if File:
		File = json.loads(File)
		for i in File:
			if i in File and File[i]:
				Config[i] = File[i]
	return Config

def HandlePost(Req):
	Data = Req.get_json()

@App.route('/Test.html')
def Test():
	return send_file('Test.html')

@App.route('/Comments', methods=['GET' 'POST'])
def Comments():
	if request.method == 'GET':
		pass
	if request.method == 'POST':
		return HandlePost(request)

if __name__ == '__main__':
	Config = SetConfig()

	if Config['Development']:
		App.run(host='0.0.0.0', port=Config['Port'], debug=True)
	else:
		from waitress import serve
		serve(App, host='0.0.0.0', port=Config['Port'])
