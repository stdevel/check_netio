#!/usr/bin/env python
# -*- coding: utf-8 -*-

# check_netio.py - a script for checking Koukaan NETIO devices
#
# 2016 By Christian Stankowic
# <info at stankowic hyphen development dot net>
# https://github.com/stdevel
#

from optparse import OptionParser, OptionGroup
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
login_error = False
hash = ""



def get_tgi_result(command):
#get result of TGI request
	
	#setup headers and URL
	myHeaders = {'User-Agent': 'check_netio plugin (https://github.com/stdevel/check_netio)'}
	#TODO: hashing URL?
	if options.debug: print "Accessing: '{0}?login=p:{1}:xxx&{2}'".format(NETIO_URL, s_username, command)
	try:
		r = requests.get(NETIO_URL + "?login=p:" + s_username + ":" + s_password + "&" + command, headers=myHeaders)
		#remove crap
		return r.content.replace("<html>", "").replace("</html>", "").replace(" ", "")
	except:
		print "CRITICAL: unable to check device with hostname '{0}' - please check values!".format(options.hostname)
		exit(2)



def get_kshell_result(command):
#get result of KShell request
	
	global login_error
	global hash
	if options.debug: print "DEBUG: Executing KShell command '{0}'".format(command)
	try:
		#open telnet session
		tn = telnetlib.Telnet(options.hostname, options.kshell_port)
		hash = tn.read_until("\n").replace("\n", "").replace("\r", "").replace("100 HELLO ", "")[:8]
		if options.debug: print "DEBUG: system hash is '{0}'".format(hash)
		#login
		if options.debug: print "DEBUG: logging in"
		tn.write("login " + s_username + " " + s_password + "\n")
		result = tn.read_until("\n").replace("\n", "")
		if options.debug: print "DEBUG: login result: {0}".format(result)
		if "250 OK" not in result:
			login_error = True
			if options.debug: print "DEBUG: unable to login with credentials '{0}:xxx'".format(s_username)
		#get command state
		tn.write(command + "\n")
		result = tn.read_until("\n").replace("\n", "").replace("\r", "")[4:]
		if options.debug: print "DEBUG: command result: '{0}'".format(result)
		#return result
		if len(result) > 0: return result
		else: return False
	except:
		print "CRITICAL: unable to login to KShell on '{0}:{1}'".format(options.hostname, options.kshell_port)
		exit(2)



if __name__ == "__main__":
	#define description, version and load parser
	desc='''%prog is used to check Koukaam NETIO devices. You can check their power states and NTP synchronization states. Login credentials are assigned using the following shell variables:
	NETIO_LOGIN username
	NETIO_PASSWORD password or hash
	It is also possible to create an authfile (permissions 0600) for usage with this script. The first line needs to contain the username, the second line should consist of the appropriate password or hash.
	If you're not defining variables or an authfile you will be prompted to enter your login information.
	Checkout the GitHub page for updates: https://github.com/stdevel/check_netio'''
	
	parser = OptionParser(description=desc,version="%prog version 0.3")
	
 	#-d / --debug
	parser.add_option("-d", "--debug", dest="debug", default=False, action="store_true", help="enable debugging outputs (default: no)")
	
	#add groups
	connGroup = OptionGroup(parser, "Connection Options", "Options for connection settings")
	checkGroup = OptionGroup(parser, "Check Options", "Options for checking the device")
	hashGroup = OptionGroup(parser, "Hashing Options", "Options for hashing login")
	
	#-s / --hostname
	connGroup.add_option("-s", "--hostname", dest="hostname", metavar="HOSTNAME", default="", help="defines the device hostname")
	
 	#-k / --use-kshell
	connGroup.add_option("-k", "--use-kshell", dest="use_kshell", default=False, action="store_true", help="use KShell instead of CGI (default: no)")
	
	#-a / --authfile
	connGroup.add_option("-a", "--authfile", dest="authfile", metavar="FILE", default="", help="defines an auth file to use instead of shell variables")
	
	#-p / --kshell-port
	connGroup.add_option("-p", "--kshell-port", dest="kshell_port", metavar="PORT", default="1234", help="defines the KShell port (default: 1234)")
	
	#-u / --username
	connGroup.add_option("-u", "--username", dest="username", metavar="USERNAME", default="", help="defines the username")
	
	#-w / --password
	connGroup.add_option("-w", "--password", dest="password", metavar="PASSWORD", default="", help="defines the password")
	
	#-n / --ntp
	checkGroup.add_option("-n", "--check-ntp", dest="check_ntp", action="store_true",  default=False, help="checks NTP synchronization state - requires KShell (default: no)")
	
	#-x / --port-state
	checkGroup.add_option("-x", "--port-state", dest="port_states", metavar="STATE", help="defines expected port states [0=off, 1=on, ?=whatever]")
	
	#-P / --enable-perfdata
	checkGroup.add_option("-P", "--enable-perfdata", dest="show_perfdata", default=False, action="store_true", help="enables performance data (default: no)")
	
	#-y / --use-hash
	hashGroup.add_option("-y", "--use-hash", dest="use_hash", action="store_true", default=False, help="uses password hash instead of plain password (default: no)")
	
	#-g / --generate-hash
	hashGroup.add_option("-g", "--generate-hash", dest="generate_hash", action="store_true", default=False, help="generates a password hash and quits (default: no)")
	
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
	
	if options.use_hash:
		print "CRITICAL - using hash logins is currently unsupported. Check out https://github.com/stdevel/check_netio for more information!"
		exit(2)
	
	#check required parameters
	if options.hostname == "":
		print "CRITICAL - no hostname given"
		exit(3)
	if options.check_ntp == False and options.port_states == None and options.generate_hash == False:
		print "CRITICAL - no valid checks defined"
		exit(3)
	if options.port_states:
		valid=True
		for char in options.port_states:
			if char not in ["0","1","?"]: valid=False
		if valid == False:
			print "CRITICAL - invalid port state expection defined ('" + options.port_states + "')"
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
		if options.use_hash: s_password = getpass.getpass("Password hash: ")
		else: s_password = getpass.getpass("Password: ")
	
	#generate hash
	if options.generate_hash:
		hashsec = get_kshell_result("version").lower()
		print "NETIO hash is: " + hashsec
		print "Still need to do stuff here..."
		exit(0)
	
	#check NETIO device
	ports = []
	
	#read ports
	try:
		if len(options.port_states) > 0:
			if options.use_kshell:
				#use KShell
				result = get_kshell_result("port list").lower()
			else:
				#use TGI
				result = get_tgi_result("port=list")
			
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
			portsExpected = list(options.port_states)
			if options.debug: print "DEBUG: port_states - portsExpected: " + str(ports) + " ==> " + str(portsExpected)
	except:
		#reading ports not requested
		if options.debug: print "DEBUG: reading ports not requested"
	
	#check NTP state
	if options.check_ntp:
		if "synchronized" not in get_kshell_result("system sntp").lower(): synchronized = False
		else: synchronized = True
	
	#return result
	result_string=""
	result_code=0
	try:
		if len(options.port_states) == 4:
			#calculate diff
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
				if len(hrPortsDiff) > 1: result_string="port differences detected: " + hrPortsDiff
				else: result_string="port difference detected: " + hrPortsDiff
				result_code=1
			else:
				result_string="ports (" + "".join(ports) + ") matching expectations (" + "".join(portsExpected) + ")"
			
			if options.check_ntp:
				#check NTP
				if synchronized: result_string = result_string + " - NTP synchronized"
				else:
					result_string = result_string + " - NTP NOT synchronized"
					result_code=2
			
			#add performance data
			if options.show_perfdata:
				perfdata="| "
				#append ports data
				for x, y in enumerate(ports): perfdata = "{0}'port{1}_state'={2} ".format(perfdata, x+1, y)
				if options.debug:  print "DEBUG: Perfdata is: {0}".format(perfdata)
	except:
		if options.debug: traceback.print_exc(file=sys.stdout)
		#check NTP only
		if synchronized:
			result_string="NTP state is synchronized"
			result_code=0
		else:
			result_string="NTP is NOT synchronized"
			result_code=2
	#invalid login?
	if login_error:
		result_string="Unable to login with given credentials"
		result_code=2
	
	#print result and exit
	if options.show_perfdata: result_string = "{0} {1}".format(result_string, perfdata)
	if result_code == 0: print "OK - {0}".format(result_string)
	elif result_code == 1: print "WARNING - {0}".format(result_string)
	elif result_code == 2: print "CRITICAL - {0}".format(result_string)
	else: print "UNKNOWN - {0}".format(result_string)
	exit(result_code)
