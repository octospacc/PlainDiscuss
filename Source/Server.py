#!/usr/bin/env python3
""" =============================== |
| PlainDiscuss                      |
|                                   |
| Licensed under the AGPLv3 license |
| Copyright (C) 2022, OctoSpacc     |
| =============================== """

import json
import secrets
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

def SelectLocale(Data):
	if Data['Lang'] and Data['Lang'] in Locales:
		return Locales[Data['Lang']]
	else:
		return Locales[Config['Default Locale']]

def GetConfig():
	Config = {
		'Development': False,
		'Port': 8080,
		'Default Locale': 'en',
		'Antispam Time': 0}
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
	DB = sqlite3.connect('Comments.db')
	return DB

def GetComments(Site, Page):
	DB = GetDB()

	SiteID = DB.cursor().execute('SELECT "ID" from "Sites" WHERE "PubKey" == "{}"'.format(Site))
	PageID = DB.cursor().execute('SELECT "ID" FROM "Pages" WHERE "Site" == "{}" AND "Path" == "{}"'.format(SiteID, Page))
	Comments = DB.cursor().execute('SELECT * FROM "Comments" WHERE "Page" == "{}"'.format(PageID))

	DB.commit()
	return Comments

def PatchCommentsHTML(Data):
	FormBase = ReadFile('Source/Form.Base.html')
	FormMain = ReadFile('Source/Form.Main.html')
	FormComment = ReadFile('Source/Form.Comment.html')

	Locale = SelectLocale(Data)

	for String in Locale:
		FormBase = FormBase.replace('[Locale:{}]'.format(String), Locale[String])
		FormMain = FormMain.replace('[Locale:{}]'.format(String), Locale[String])
		FormComment = FormComment.replace('[Locale:{}]'.format(String), Locale[String])

	FormMain = FormMain.format(
		SecKey=Data['SecKey'] if Data['SecKey'] else '',
		User=Data['User'] if Data['User'] else '',
		Comment=Data['Comment'] if Data['Comment'] else '')

	Comments = ''
	for Comment in GetComments(Data['Site'], Data['Page']):
		Comments += "\n<hr>\n" + FormComment.format(
			User="User",
			Date="Date",
			ID="ID",
			Comment="Comment")

	return FormBase.format(
		Lang=Data['Lang'] if Data['Lang'] else '',
		Style='',
		Site=Data['Site'] if Data['Site'] else '',
		Page=Data['Page'] if Data['Page'] else '',
		Form=FormMain+Comments,
		StatusGood='',
		StatusError='')

def CommentsGet(Req):
	Data = {}
	for i in ['Lang','StyleFile','Site','Page']:
		Data.update({i:Req.args.get(i)})
	return PatchCommentsHTML(Data)

def CommentsPost(Req):
	Data = {}
	for i in ['Lang','StyleFile','Site','Page','User','CAPTCHA','Comment','SecKey','Action','Reply','Report','Delete']:
		Data.update({i:Req.form.get(i)})
	return PatchCommentsHTML(Data)

@App.route('/Comments', methods=['GET', 'POST'])
def Comments():
	Req = request
	if Req.method == 'GET':
		return CommentsGet(Req)
	if Req.method == 'POST':
		return CommentsPost(Req)

@App.route('/Main.css')
def SendCSS():
	return send_file('Main.css')

def AddSite():
	PubKey = secrets.token_urlsafe(32)
	SecKey = secrets.token_urlsafe(64)
	Good, Error = "", ""
	try:
		DB = GetDB()
		DB.cursor().execute('INSERT INTO "Sites"("PubKey", "SecKey") VALUES("{}", "{}")'.format(PubKey, SecKey))
		DB.commit()
		Good = """\
<p>
	Created your new site API keys. Please store these safely, they can't be recovered.
	<br><br>
	Public Key (for showing comments on your site): <pre>{}</pre>
	Secret Key (for managing comments, KEEP IT SECRET): <pre>{}</pre>
</p>""".format(PubKey, SecKey)
	except Exception:
		Error = "<p>Server error. Please try again later.</p>"
	return Good, Error

def DelSite():
	pass

def PatchManageHTML(Data):
	HTML = ReadFile('Source/Manage.html')

	Locale = SelectLocale(Data)

	for String in Locale:
		HTML = HTML.replace('[Locale:{}]'.format(String), Locale[String])

	if 'Action' in Data and Data['Action']:
		if Data['Action'] == 'AddSite':
			Good, Error = AddSite()
		elif Data['Action'] == 'DelSite':
			Good, Error = DelSite()
	else:
		Good, Error = '', ''

	return HTML.format(
		Lang=Data['Lang'] if Data['Lang'] else '',
		StatusGood=Good,
		StatusError=Error)

"""
def ManageGet(Req):
	Data = {}
	for i in ['Lang']:
		Data.update({i:Req.args.get(i)})
	return PatchManageHTML(Data)

def ManagePost(Req):
	Data = {}
	for i in ['Lang', 'Action']:
		Data.update({i:Req.form.get(i)})
	return PatchManageHTML(Data)
"""

@App.route('/Manage', methods=['GET', 'POST'])
def SendManage():
	Req = request
	Data = {}
	if Req.method == 'GET':
		#return ManageGet(Req)
		for i in ['Lang']:
			Data.update({i:Req.args.get(i)})
	elif Req.method == 'POST':
		#return ManagePost(Req)
		for i in ['Lang', 'Action']:
			Data.update({i:Req.form.get(i)})
	return PatchManageHTML(Data)

if __name__ == '__main__':
	Locales = GetLocales()
	Config = GetConfig()

	#DB = sqlite3.connect('Comments.db')
	DB = GetDB()
	InitDB()
	#DB.close()

	if Config['Development']:
		App.run(host='0.0.0.0', port=Config['Port'], debug=True)
	else:
		from waitress import serve
		serve(App, host='0.0.0.0', port=Config['Port'])
