#!/usr/bin/env python
##########################################################################
##                                                                      ##
## cga-gen.py - Generate a CGA and associated parameters using Scapy6.  ##
##                                                                      ##
## Copyright (C) 2013  Marc Buijsman                                    ##
##                                                                      ##
## This program is free software: you can redistribute it and/or modify ##
## it under the terms of the GNU General Public License as published by ##
## the Free Software Foundation, either version 3 of the License, or    ##
## (at your option) any later version.                                  ##
##                                                                      ##
## This program is distributed in the hope that it will be useful,      ##
## but WITHOUT ANY WARRANTY; without even the implied warranty of       ##
## MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the        ##
## GNU General Public License for more details.                         ##
##                                                                      ##
##########################################################################

from netaddr.ip import IPNetwork, IPAddress
import netifaces as ni
import binascii as ba
import errno
import argparse
from scapy6send.scapy6 import CGAgen


def main(pfx, pub_key, sec, ext, dad, mf, col):
	try:
		pk = open(pub_key, 'rb').read()
	except IOError:
		print("Could not open file '" + pub_key + "'.")
		exit()

	mod = None

	if mf != None:
		try:
			mod = ba.a2b_base64(open(mf, 'rb').read())

			if len(mod) != 16:
				print("Modifier length is not equal to 16 octets.")
				exit()
		except IOError:
			mf = None
			mod = None
			print("Could not open file '" + mf + "', generating new modifier instead.")
		except ba.Error:
			print("Invalid modifier encoding.")
			exit()

	if pfx == None:
		try:
			a = ni.ifaddresses('eth0')[10][0]['addr']
		except KeyError:
			print("Could not get prefix: no IPv6 address found at 'eth0'; alternatively pass a prefix in command line argument.")
			exit()
		try:
			m = ni.ifaddresses('eth0')[10][0]['netmask']
		except KeyError:
			print("Could not get prefix: no subnet mask found at 'eth0'; alternatively pass a prefix in command line argument.")
			exit()

		pfx = str(IPAddress(int(IPNetwork(a).network) & int(IPNetwork(m).network)))
	else:
		if pfx[-1] != ':':
			pfx = pfx + ':'
		if len(pfx) < 2 or pfx[-2] != ':':
			pfx = pfx + ':'

	try:
		pk = PubKey(pk)
	except:
		print("Could not import public key. Wrong format?")
		exit()

	# generate CGA
	try:
		(addr, params) = CGAgen(pfx, pk, sec, ext, dad, mod, col)
	except socket.error, v:
		if v[0] == errno.EPERM:
			print("Need to be root to perform duplicate address detection.")
			exit()
		else:
			print("Invalid prefix.")
			exit()

	if addr == None or params == None:
		print("Unexpected error.")
		exit()

	mod = ba.b2a_base64(params.modifier)

	print("            CGA: " + addr)
	sys.stdout.write("       modifier: " + mod.rstrip())

	if mf == None:
		try:
			md = open('mod.out', 'w')
			md.write(mod)
			print(" (written to file 'mod.out')")
		except IOError:
			print(" (could not write to file 'mod.out')")
	else:
		print("")

	sys.stdout.write("collision count: " + str(params.ccount))

	if not dad:
		print(" (did NOT perform duplicate address detection)")
	else:
		print("")


if __name__ == "__main__":
	parser = argparse.ArgumentParser(description='Generate a CGA and associated parameters using Scapy6.')
	parser.add_argument('pk', metavar='K', help='file containing the public key in PEM PKCS8 format')
	parser.add_argument('-s', dest='sec', type=int, choices=range(8), default=0, help='the sec parameter (defaults to 0)')
	parser.add_argument('-d', dest='dad', default=False, action='store_true', help='perform duplicate address detection if set (disabled by default)')
	parser.add_argument('-m', dest='mod', default=None, help='file containing a 16-byte modifier in base64 format (generated by default)')
	parser.add_argument('-p', dest='pfx', default=None, help='the IPv6 prefix to concatenate the generated IPv6 identifier with (extracts from eth0 by default)')
	parser.add_argument('-c', dest='col', type=int, choices=range(3), default=None, help='collision count (generated by default)')
	parser.add_argument('-e', dest='ext', default=[], nargs='+', help='optional extension fields (none by default)')
	args = parser.parse_args()

	main(args.pfx, args.pk, args.sec, args.ext, args.dad, args.mod, args.col)

