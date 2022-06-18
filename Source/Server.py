#!/usr/bin/env python3
""" =============================== |
| PlainDiscuss                      |
|                                   |
| Licensed under the AGPLv3 license |
| Copyright (C) 2022, OctoSpacc     |
| =============================== """

import json
import os
import random
import secrets
import sqlite3
import time
from ast import literal_eval
from base64 import b64encode
from flask import Flask, request, send_file
from pathlib import Path
from captcha.audio import AudioCaptcha
from captcha.image import ImageCaptcha

App = Flask(__name__)

def ReadFile(p, m='r'):
	try:
		with open(p, m) as f:
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
		'CAPTCHA': True}
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

def RandomWord():
	Words = ReadFile('CAPTCHA/it.txt')
	Word = '#'
	while Word.startswith('#'):
		Word = random.choice(Words.splitlines())
	return Word.lower()

def MakeCAPTCHA(ID):
	#ID = time.time()
	String = RandomWord()
	Audio = AudioCaptcha(voicedir='CAPTCHA/it')
	Image = ImageCaptcha(fonts=['CAPTCHA/OpenDyslexic3-Regular.ttf'],width=len(String)*40, height=90)
	CAPTCHA = Audio.generate(String)
	Audio.write(String, 'CAPTCHA.{}.wav'.format(ID))
	CAPTCHA = Image.generate(String)
	Image.write(String, 'CAPTCHA.{}.png'.format(ID))
	#return ID

def CAPTCHAHTML(ID):
	#ID = MakeCAPTCHA()
	MakeCAPTCHA(ID)
	Audio = b64encode(ReadFile('CAPTCHA.{}.wav'.format(ID), 'rb'))
	Image = b64encode(ReadFile('CAPTCHA.{}.png'.format(ID), 'rb'))
	os.remove('CAPTCHA.{}.wav'.format(ID))
	os.remove('CAPTCHA.{}.png'.format(ID))
	return """\
<label>CAPTCHA:</label>
<br>
<img src="data:image/png;base64,{}">
<audio src="data:audio/wav;base64,{}"controls="controls"></audio>
<br>
<span><input type="text" name="CAPTCHA"></span>
	""".format(Image.decode('UTF-8'), Audio.decode('UTF-8'))

def GetComments(Site, Page):
	DB = GetDB()
	Comments = []

	SiteID = DB.cursor().execute('SELECT "ID" FROM "Sites" WHERE "PubKey" == "{}"'.format(Site)).fetchall()[0][0]
	PageID = DB.cursor().execute('SELECT "ID" FROM "Pages" WHERE "Site" == "{}" AND "Path" == "{}"'.format(SiteID, Page)).fetchall()
	if PageID:
		PageID = PageID[0][0]
		Comments = DB.cursor().execute('SELECT * FROM "Comments" WHERE "Page" == "{}"'.format(PageID)).fetchall()

	DB.commit()
	return Comments

def PostComment(Site, Page, Comment, User, SecKey, Reply):
	DB = GetDB()

	SiteID = DB.cursor().execute('SELECT "ID" FROM "Sites" WHERE "PubKey" == "{}"'.format(Site)).fetchall()[0][0]
	PageID = DB.cursor().execute('SELECT "ID" FROM "Pages" WHERE "Site" == "{}" AND "Path" == "{}"'.format(SiteID, Page)).fetchall()
	if PageID:
		PageID = PageID[0][0]
	else:
		DB.cursor().execute('INSERT INTO "Pages"("Site", "Path") VALUES("{}", "{}")'.format(SiteID, Page))
		PageID = DB.cursor().execute('SELECT "ID" FROM "Pages" WHERE "Site" == "{}" AND "Path" == "{}"'.format(SiteID, Page)).fetchall()[0][0]
	UserID = DB.cursor().execute('SELECT "ID" FROM "Users" WHERE "Name" == "{}" AND "SecKey" == "{}"'.format(User, SecKey)).fetchall()
	if UserID:
		UserID = UserID[0][0]
	else:
		DB.cursor().execute('INSERT INTO "Users"("Name", "SecKey") VALUES("{}", "{}")'.format(User, SecKey))
		UserID = DB.cursor().execute('SELECT "ID" FROM "Users" WHERE "Name" == "{}" AND "SecKey" == "{}"'.format(User, SecKey)).fetchall()[0][0]

	DB.cursor().execute('INSERT INTO "Comments"("User", "Page", "Reply", "Date", "Comment") VALUES("{}", "{}", "{}", "{}", "{}")'.format(UserID, PageID, Reply, time.time(), Comment))
	DB.commit()

	print(UserID, PageID, Reply, time.time(), Comment)

def PostCommentData(Data):
	Good, Error = "", ""
	Missing = []
	for i in ['User', 'Comment']:
		if not (i in Data and Data[i]):
			Missing += [i]
	if len(Missing) > 0:
		Error = """\
<p>
	Some fields are missing:
	<br>
	{}
</p>""".format(Missing)
	else:
		#try:
		PostComment(
			Data['Site'], Data['Page'], Data['Comment'], Data['User'],
			Data['SecKey'] if 'SecKey' in Data and Data['SecKey'] else secrets.token_urlsafe(64),
			Data['Reply'] if 'Reply' in Data and Data['Reply'] else None)
		Good = """\
<p>
	Your comment has been posted!
</p>"""
		#except Exception:
		#	Error = "<p>Server error. Please try again later.</p>"
	return Good, Error

def PatchCommentsHTML(Data):
	ReqID = time.time()
	FormBase = ReadFile('Source/Form.Base.html')
	FormMain = ReadFile('Source/Form.Main.html')
	FormComment = ReadFile('Source/Form.Comment.html')

	Locale = SelectLocale(Data)

	for String in Locale:
		FormBase = FormBase.replace('[Locale:{}]'.format(String), Locale[String])
		FormMain = FormMain.replace('[Locale:{}]'.format(String), Locale[String])
		FormComment = FormComment.replace('[Locale:{}]'.format(String), Locale[String])

	if 'ReadOnly' in Data and Data['ReadOnly'] == 'True':
		FormMain, Good, Error = '', '', ''
	else:
		FormMain = FormMain.format(
			CAPTCHAHTML=CAPTCHAHTML(ReqID) if Config['CAPTCHA'] else '',
			SecKey=Data['SecKey'] if 'SecKey' in Data and Data['SecKey'] else '',
			User=Data['User'] if 'User' in Data and Data['User'] else '',
			Comment=Data['Comment'] if 'Comment' in Data and Data['Comment'] else '')

		if 'Action' in Data and Data['Action']:
			if Data['Action'] == 'Login':
				Good, Error = '', ''
			elif Data['Action'] == 'Post':
				Good, Error = PostCommentData(Data)
		elif 'Reply' in Data and Data['Reply']:
			Good, Error = PostCommentData(Data)
		elif 'Delete' in Data and Data['Delete']:
			Good, Error = '', ''
		else:
			Good, Error = '', ''

	Comments = ''
	for ID,User,Page,Reply,Date,Comment in GetComments(Data['Site'], Data['Page']):
		print(Comment)
		Comments += "\n<hr>\n" + FormComment.format(
			User=User,
			Date=Date,
			ID=ID,
			Comment=Comment)

	return FormBase.format(
		Lang=Data['Lang'] if Data['Lang'] else '',
		Style='',
		Site=Data['Site'] if Data['Site'] else '',
		Page=Data['Page'] if Data['Page'] else '',
		Form=FormMain+Comments,
		StatusGood=Good,
		StatusError=Error)

@App.route('/Comments', methods=['GET', 'POST'])
def Comments():
	Req = request
	Data = {}
	if Req.method == 'GET':
		for i in ['Lang','StyleFile','Site','Page','ReadOnly']:
			Data.update({i:Req.args.get(i)})
	if Req.method == 'POST':
		for i in ['Lang','StyleFile','Site','Page','User','CAPTCHA','Comment','SecKey','Action','Reply','Report','Delete']:
			Data.update({i:Req.form.get(i)})
	return PatchCommentsHTML(Data)

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
		Lang=Data['Lang'] if 'Lang' in Data and Data['Lang'] else '',
		StatusGood=Good,
		StatusError=Error)

@App.route('/Manage', methods=['GET', 'POST'])
def SendManage():
	Req = request
	Data = {}
	if Req.method == 'GET':
		for i in ['Lang']:
			Data.update({i:Req.args.get(i)})
	elif Req.method == 'POST':
		for i in ['Lang', 'Action']:
			Data.update({i:Req.form.get(i)})
	return PatchManageHTML(Data)

if __name__ == '__main__':
	Locales = GetLocales()
	Config = GetConfig()
	DB = GetDB()
	InitDB()

	if Config['Development']:
		App.run(host='0.0.0.0', port=Config['Port'], debug=True)
	else:
		from waitress import serve
		serve(App, host='0.0.0.0', port=Config['Port'])
