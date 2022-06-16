#!/usr/bin/env python3
""" =============================== |
| PlainDiscuss                      |
|                                   |
| Licensed under the AGPLv3 license |
| Copyright (C) 2022, OctoSpacc     |
| =============================== """

import json
import sqlite3
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

def GetConfig():
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

def InitDB():
	for i in ReadFile('Source/Comments.sql').split(';'):
		DB.cursor().execute(i)
	DB.commit()

def GetDB():
	return sqlite3.connect('Comments.db')

def GetComments():
	return [0,0,0]

def PatchHTML(Data):
	Base = ReadFile('Source/Main.html')
	FormMain = ReadFile('Source/Form.Main.html')
	FormComment = ReadFile('Source/Form.Comment.html')

	Comments = ''
	for i in GetComments():
		Comments += "\n<br><hr>\n" + FormComment.format(
			User="User",
			Date="Date",
			ID="ID")

	return Base.format(FormMain + Comments)

def Get(Req):
	Data = {}
	for i in ['Site','Page','User','CAPTCHA','Comment','SecretKey','Select','Action','Reply','Report']:
		Data.update({i:Req.args.get(i)})
		print(Req.args.get(i))
	return PatchHTML(Data)

def Post(Req):
	Data = Req.get_json()
	print(Data)

@App.route('/Main.css')
def SendCSS():
	return send_file('Main.css')

@App.route('/Comments', methods=['GET', 'POST'])
def Comments():
	Req = request
	if Req.method == 'GET':
		return Get(Req)
	if Req.method == 'POST':
		return Post(Req)

if __name__ == '__main__':
	Config = GetConfig()
	DB = GetDB()
	InitDB()

	if Config['Development']:
		App.run(host='0.0.0.0', port=Config['Port'], debug=True)
	else:
		from waitress import serve
		serve(App, host='0.0.0.0', port=Config['Port'])
