#!/usr/bin/env python3
""" =============================== |
| PlainDiscuss                      |
|                                   |
| Licensed under the AGPLv3 license |
| Copyright (C) 2022, OctoSpacc     |
| =============================== """

import json
import sqlite3
import time
from ast import literal_eval
from flask import Flask, request, send_file
from pathlib import Path

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

def GetLocales():
	Locales = {}
	for File in Path('Locale').rglob('*.json'):
		File = str(File)
		Lang = File[len('Locale/'):-len('.json')]
		Locale = json.loads(ReadFile(File))
		Locales.update({Lang:Locale})
	return Locales

def GetConfig():
	Config = {
		'Development': False,
		'Port': 8080,
		'Default Locale': 'en'}
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

def GetComments(Site, Page):
	DB = GetDB()

	SiteID = DB.cursor().execute('SELECT "ID" from "Sites" WHERE "PubKey" == "{}"'.format(Site))
	PageID = DB.cursor().execute('SELECT "ID" FROM "Pages" WHERE "Site" == "{}" AND "Path" == "{}"'.format(SiteID, Page))
	Comments = DB.cursor().execute('SELECT * FROM "Comments" WHERE "Page" == "{}"'.format(PageID))

	DB.close()
	return Comments

def PatchHTML(Data):
	FormBase = ReadFile('Source/Form.Base.html')
	FormMain = ReadFile('Source/Form.Main.html')
	FormComment = ReadFile('Source/Form.Comment.html')

	if Data['Lang'] and Data['Lang'] in Locales:
		Locale = Locales[Data['Lang']]
	else:
		Locale = Locales[Config['Default Locale']]

	for String in Locale:
		FormBase = FormBase.replace('[Locale:{}]'.format(String), Locale[String])
		FormMain = FormMain.replace('[Locale:{}]'.format(String), Locale[String])
		FormComment = FormComment.replace('[Locale:{}]'.format(String), Locale[String])

	Comments = ''
	for Comment in GetComments(Data['Site'], Data['Page']):
		Comments += "\n<hr>\n" + FormComment.format(
			User="User",
			Date="Date",
			ID="ID",
			Comment="Comment")

	return FormBase.format(Style='',Form=FormMain+Comments)

def Get(Req):
	Data = {}
	for i in ['Lang','StyleFile','Site','Page']:
		Data.update({i:Req.args.get(i)})
	return PatchHTML(Data)

def Post(Req):
	Data = {}
	for i in ['Lang','StyleFile','Site','Page','User','CAPTCHA','Comment','SecretKey','Action','Reply','Report','Delete']:
		Data.update({i:Req.args.get(i)})
	return PatchHTML(Data)

@App.route('/Manage.html')
def SendManage():
	return send_file('Manage.html')

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
	Locales = GetLocales()
	Config = GetConfig()

	DB = GetDB()
	InitDB()
	DB.close()

	if Config['Development']:
		App.run(host='0.0.0.0', port=Config['Port'], debug=True)
	else:
		from waitress import serve
		serve(App, host='0.0.0.0', port=Config['Port'])
