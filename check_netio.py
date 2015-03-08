#!/usr/bin/python
# check_netio.py - a script for checking Koukaan NETIO devices
#
# 2015 By Christian Stankowic
# <info at stankowic hyphen development dot net>
# https://github.com/stdevel
#

from optparse import OptionParser
from optparse import OptionGroup
import os
import stat
import getpass
import requests
import telnetlib
import sys
import traceback

#TODO:
#- add hashing generation and login functionality

#global variables
synchronized = False
loginError = False
hash = ""



def getTGIResult(command):
#get result of TGI request
	#setup headers and URL
	myHeaders = {'User-Agent': 'check_netio plugin (https://github.com/stdevel/check_netio)'}
	#TODO: hashing URL?
	if options.debug: print "Accessing: '" + NETIO_URL + "?login=p:" + s_username + ":xxx&" + command + "'"
	try:
		r = requests.get(NETIO_URL + "?login=p:" + s_username + ":" + s_password + "&" + command, headers=myHeaders)
		#remove crap
		return r.content.replace("<html>", "").replace("</html>", "").replace(" ", "")
	except:
		print "CRITICAL: unable to check device with hostname '" + options.hostname + "' - please check values!"
		exit(2)



def getKShellResult(command):
#get result of KShell request
	global loginError
	global hash
	if options.debug: print "DEBUG: Checking NTP sync state"
	#open telnet session
	try:
		tn = telnetlib.Telnet(options.hostname, options.kshellPort)
		hash = tn.read_until("\n").replace("\n", "").replace("\r", "").replace("100 HELLO ", "")[:8]
		if options.debug: print "DEBUG: system hash is " + hash
		#login
		if options.debug: print "DEBUG: logging in"
		tn.write("login " + s_username + " " + s_password + "\n")
		result = tn.read_until("\n").replace("\n", "")
		if options.debug: print "DEBUG: login result: " + result
		if "250 OK" not in result:
			loginError = True
			if options.debug: print "DEBUG: unable to login with credentials '" + s_username + ":xxx'"
		#get command state
		tn.write(command + "\n")
		result = tn.read_until("\n").replace("\n", "").replace("\r", "")[4:]
		if options.debug: print "DEBUG: command result: '" + result + "'"
		#return result
		if len(result) > 0: return result
		else: return False
	except:
		print "CRITICAL: unable to login to KShell on '" + options.hostname + ":" + options.kshellPort + "'"
		exit(2)



if __name__ == "__main__":
	#define description, version and load parser
	desc='''%prog is used to check Koukaam NETIO devices. You can check their power states and NTP synchronization states. Login credentials are assigned using the following shell variables:
	NETIO_LOGIN username
	NETIO_PASSWORD password or hash
	It is also possible to create an authfile (permissions 0600) for usage with this script. The first line needs to contain the username, the second line should consist of the appropriate password or hash.
	If you're not defining variables or an authfile you will be prompted to enter your login information.
	Checkout the GitHub page for updates: https://github.com/stdevel/check_netio'''
	
	parser = OptionParser(description=desc,version="%prog version 0.2")
	
 	#-d / --debug
	parser.add_option("-d", "--debug", dest="debug", default=False, action="store_true", help="enable debugging outputs (default: no)")
	
	#add groups
	connGroup = OptionGroup(parser, "Connection Options", "Options for connection settings")
	checkGroup = OptionGroup(parser, "Check Options", "Options for checking the device")
	hashGroup = OptionGroup(parser, "Hashing Options", "Options for hashing login")
	
	#-s / --hostname
	connGroup.add_option("-s", "--hostname", dest="hostname", metavar="HOSTNAME", default="", help="defines the device hostname")
	
 	#-k / --use-kshell
	connGroup.add_option("-k", "--use-kshell", dest="useKShell", default=False, action="store_true", help="use KShell instead of CGI (default: no)")
	
	#-a / --authfile
	connGroup.add_option("-a", "--authfile", dest="authfile", metavar="FILE", default="", help="defines an auth file to use instead of shell variables")
	
	#-p / --kshell-port
	connGroup.add_option("-p", "--kshell-port", dest="kshellPort", metavar="PORT", default="1234", help="defines the KShell port (default: 1234)")
	
	#-u / --username
	connGroup.add_option("-u", "--username", dest="username", metavar="USERNAME", default="", help="defines the username")
	
	#-w / --password
	connGroup.add_option("-w", "--password", dest="password", metavar="PASSWORD", default="", help="defines the password")
	
	#-n / --ntp
	checkGroup.add_option("-n", "--check-ntp", dest="checkNTP", action="store_true",  default=False, help="checks NTP synchronization state - requires KShell (default: no)")
	
	#-x / --port-state
	checkGroup.add_option("-x", "--port-state", dest="portStates", metavar="STATE", help="defines expected port states [0=off, 1=on, ?=whatever]")
	
	#-y / --use-hash
	hashGroup.add_option("-y", "--use-hash", dest="useHash", action="store_true", default=False, help="uses password hash instead of plain password (default: no)")
	
	#-g / --generate-hash
	hashGroup.add_option("-g", "--generate-hash", dest="generateHash", action="store_true", default=False, help="generates a password hash and quits (default: no)")
	
	#add groups
	parser.add_option_group(connGroup)
	parser.add_option_group(hashGroup)
	parser.add_option_group(checkGroup)
	
	#parse arguments
	(options, args) = parser.parse_args()
	
	#define URL and login information
	NETIO_URL = "http://"+options.hostname+"/tgi/control.tgi"
	
	#debug outputs
	if options.debug: print "OPTIONS: {0}".format(options)
	if options.debug: print "ARGUMENTS: {0}".format(args)
	
	if options.useHash:
		print "CRITICAL - using hash logins is currently unsupported. Check out https://github.com/stdevel/check_netio for more information!"
		exit(2)
	
	#check required parameters
	if options.hostname == "":
		print "CRITICAL - no hostname given"
		exit(3)
	if options.checkNTP == False and options.portStates == None and options.generateHash == False:
		print "CRITICAL - no valid checks defined"
		exit(3)
	if options.portStates:
		valid=True
		for char in options.portStates:
			if char not in ["0","1","?"]: valid=False
		if valid == False:
			print "CRITICAL - invalid port state expection defined ('" + options.portStates + "')"
			exit(2)
	
	#get login credentials
	if options.authfile:
		#use authfile
		if options.debug: print "DEBUG: using authfile"
		try:
			#check filemode and read file
			filemode = oct(stat.S_IMODE(os.lstat(options.authfile).st_mode))
			if filemode == "0600":
				if options.debug: print "DEBUG: file permission ("+filemode+") matches 0600"
				fo = open(options.authfile, "r")
				s_username=fo.readline().replace("\n", "")
				s_password=fo.readline().replace("\n", "")
			else:
				print "CRITICAL - file permissions for authfile ("+filemode+") not matching 0600!"
				exit(2)
		except OSError:
			print "ERROR: file non-existent or permissions not 0600!"
			exit(1)
	elif "NETIO_LOGIN" in os.environ and "NETIO_PASSWORD" in os.environ:
		#shell variables
		if options.debug: print "DEBUG: checking shell variables"
		s_username = os.environ["NETIO_LOGIN"]
		s_password = os.environ["NETIO_PASSWORD"]
	elif options.username != "" and options.password != "":
		#parameters
		s_username = options.username
		s_password = options.password
	else:
		#prompt user
		if options.debug: print "DEBUG: prompting for login credentials"
		s_username = raw_input("Username: ")
		if options.useHash: s_password = getpass.getpass("Password hash: ")
		else: s_password = getpass.getpass("Password: ")
	
	#generate hash
	if options.generateHash:
		hashsec = getKShellResult("version").lower()
		print "NETIO hash is: " + hashsec
		print "Still need to do stuff here..."
		exit(0)
	
	#check NETIO device
	ports = []
	
	#read ports
	try:
		if len(options.portStates) > 0:
			if options.useKShell:
				#use KShell
				result = getKShellResult("port list").lower()
			else:
				#use TGI
				result = getTGIResult("port=list")
			
			#add ports if valid response
			if len(result) == 4:
				ports.append(result[:1])
				ports.append(result[1:2])
				ports.append(result[2:3])
				ports.append(result[3:4])
			else:
				#unexpected result
				print "UNKNOWN: ports not readable"
				exit(3)
			
			#check ports
			portsExpected = list(options.portStates)
			if options.debug: print "DEBUG: portStates - portsExpected: " + str(ports) + " ==> " + str(portsExpected)
	except:
		#reading ports not requested
		if options.debug: print "DEBUG: reading ports not requested"
	
	#check NTP state
	if options.checkNTP:
		if "synchronized" not in getKShellResult("system sntp").lower(): synchronized = False
		else: synchronized = True
	
	#return result
	STRING=""
	CODE=0
	try:
		if len(options.portStates) == 4:
			#calculate diff
			#portsDiff = []
			portsDiff = list()
			for i in range(0,len(ports)):
				if ports[i] != portsExpected[i] and portsExpected[i] != "?": portsDiff.append(i)
			if options.debug: print "DEBUG: differences => " + str(portsDiff)
			
			#check power states and NTP
			if len(portsDiff) > 0:
				#create human-readable list of port differences
				for i in range(0,len(portsDiff)): portsDiff[i] = str(portsDiff[i]+1)
				hrPortsDiff = ",".join(portsDiff)
				#output diff
				if len(hrPortsDiff) > 1: STRING="port differences detected: " + hrPortsDiff
				else: STRING="port difference detected: " + hrPortsDiff
				CODE=1
			else:
				STRING="ports (" + "".join(ports) + ") matching expectations (" + "".join(portsExpected) + ")"
			
			if options.checkNTP:
				#check NTP
				if synchronized: STRING = STRING + " - NTP synchronized"
				else:
					STRING = STRING + " - NTP NOT synchronized"
					CODE=2
	except:
		if options.debug: traceback.print_exc(file=sys.stdout)
		#check NTP only
		if synchronized:
			STRING="NTP state is synchronized"
			CODE=0
		else:
			STRING="NTP is NOT synchronized"
			CODE=2
	#invalid login?
	if loginError:
		STRING="Unable to login with given credentials"
		CODE=2
	
	#print result and exit
	if CODE == 0: print "OK - " + STRING
	elif CODE == 1: print "WARNING - " + STRING
	elif CODE == 2: print "CRITICAL - " + STRING
	else: print "UNKNOWN - " + STRING
	exit(CODE)
