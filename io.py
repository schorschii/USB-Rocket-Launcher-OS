from http.server import BaseHTTPRequestHandler, HTTPServer
from cgi import parse_header, parse_multipart
from urllib.parse import parse_qs
import RPi.GPIO as GPIO
import time
import atexit
import argparse
import sys


# Web Server Config
LISTEN_ADDRESS = "0.0.0.0"
LISTEN_PORT    = 80

# Use Physical Pin Numbers
GPIO.setmode(GPIO.BOARD)
GPIO.setwarnings(False)

# Motor Pin Definition
AIA = 8
AIB = 10
BIA = 3
BIB = 5
CIA = 16
CIB = 18

# LED Pin Definition
LEDFIRE = 7
LEDSESS = 11

# Control Input Pin Definition
BTNFIRE = 15
SWTYBGN = 37
SWTYEND = 35
SWTXBGN = 31
SWTXEND = 33


# Pin Setup
GPIO.setup(AIA, GPIO.OUT)
GPIO.setup(AIB, GPIO.OUT)
GPIO.setup(BIA, GPIO.OUT)
GPIO.setup(BIB, GPIO.OUT)
GPIO.setup(CIA, GPIO.OUT)
GPIO.setup(CIB, GPIO.OUT)
GPIO.setup(LEDFIRE, GPIO.OUT)
GPIO.setup(LEDSESS, GPIO.OUT)
GPIO.setup(BTNFIRE, GPIO.IN)
GPIO.setup(SWTYBGN, GPIO.IN)
GPIO.setup(SWTYEND, GPIO.IN)
GPIO.setup(SWTXBGN, GPIO.IN)
GPIO.setup(SWTXEND, GPIO.IN)


# Control Functions
def stopY():
	#sys.stderr.write("stopY")
	GPIO.output(BIA, False)
	GPIO.output(BIB, False)
def stopX():
	#sys.stderr.write("stopX")
	GPIO.output(AIA, False)
	GPIO.output(AIB, False)
def stopFire():
	#sys.stderr.write("stopFire")
	GPIO.output(CIA, False)
	GPIO.output(CIB, False)
	GPIO.output(LEDFIRE, False)

class RocketLauncherServer(BaseHTTPRequestHandler):
	def do_GET(self):
		self.send_response(200)
		self.send_header("Content-type", "text/html; charset=utf-8")
		self.end_headers()
		f = open("web.html", "r")
		html = f.read().replace("SERVERNAME", self.request.getsockname()[0])
		self.wfile.write(bytes(html, "utf8"))
		f.close()

	def do_POST(self):
		ctype, pdict = parse_header(self.headers.get('content-type'))
		if ctype == "multipart/form-data":
			postvars = parse_multipart(self.rfile, pdict)
		elif ctype == "application/x-www-form-urlencoded":
			length = int(self.headers.get("content-length"))
			postvars = parse_qs(self.rfile.read(length).decode("utf8"), keep_blank_values=1)
		#print(postvars)

		if "statusctl" in postvars:
			if postvars.get("statusctl")[0] == "begin":
				GPIO.output(LEDSESS, True)
			elif postvars.get("statusctl")[0] == "end":
				GPIO.output(LEDSESS, False)

		if "motorctl" in postvars:
			if postvars.get("motorctl")[0] == "a+":
				if GPIO.input(SWTXBGN) or GPIO.input(SWTXEND): stopX()
				else:
					GPIO.output(AIA, True)
					GPIO.output(AIB, False)
			elif postvars.get("motorctl")[0] == "a-":
				if GPIO.input(SWTXBGN) or GPIO.input(SWTXEND): stopX()
				else:
					GPIO.output(AIA, False)
					GPIO.output(AIB, True)
			elif postvars.get("motorctl")[0] == "a.":
				stopX()

			elif postvars.get("motorctl")[0] == "b+":
				if GPIO.input(SWTYBGN) or GPIO.input(SWTYEND): stopY()
				else:
					GPIO.output(BIA, True)
					GPIO.output(BIB, False)
			elif postvars.get("motorctl")[0] == "b-":
				if GPIO.input(SWTYBGN) or GPIO.input(SWTYEND): stopY()
				else:
					GPIO.output(BIA, False)
					GPIO.output(BIB, True)
			elif postvars.get("motorctl")[0] == "b.":
				stopY()

			elif postvars.get("motorctl")[0] == "c+":
				GPIO.output(CIA, False)
				GPIO.output(CIB, True)
				GPIO.output(LEDFIRE, True)
			elif postvars.get("motorctl")[0] == "c-":
				GPIO.output(CIA, True)
				GPIO.output(CIB, False)
				GPIO.output(LEDFIRE, True)
			elif postvars.get("motorctl")[0] == "c.":
				stopFire()

		if "dbg" in postvars and postvars.get("dbg")[0] == "1":
			print(GPIO.input(SWTXBGN))
			print(GPIO.input(SWTXEND))
			print(GPIO.input(SWTYBGN))
			print(GPIO.input(SWTYEND))

def exitHandler():
	print("GPIO cleanup.")
	GPIO.output(AIA, False)
	GPIO.output(AIB, False)
	GPIO.output(BIA, False)
	GPIO.output(BIB, False)
	GPIO.output(CIA, False)
	GPIO.output(CIB, False)
	GPIO.cleanup()

if __name__ == "__main__":
	atexit.register(exitHandler)

	webServer = HTTPServer((LISTEN_ADDRESS, LISTEN_PORT), RocketLauncherServer)
	print("Server started http://%s:%s" % (LISTEN_ADDRESS, LISTEN_PORT))
	try: webServer.serve_forever()
	except KeyboardInterrupt: pass
	webServer.server_close()
	print("Server stopped.")
