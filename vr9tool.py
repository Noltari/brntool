#!/usr/bin/python
# -*- coding: utf-8 -*-
from __future__ import division
from optparse import OptionParser

import serial
import sys
import re
import time

lineregex = re.compile(r'0x(?:[0-9A-F]{8})((?: [0-9A-F]{2}){1,16})')

def printf(string):
	sys.stdout.write(string)
	sys.stdout.flush()

def skip_prompt(ser):
	while ser.read(1):
		pass

def wait_prompt(ser, delay, password):
	printf("Waiting for a prompt")
	t_prompt = time.time()
	while True:
		if(ser.inWaiting() > 0):
			ser.write("   ")
			ser.write(password)
			skip_prompt(ser)
			time.sleep(delay)
			ser.write("!")
			while ser.inWaiting() > 0:
				if(ser.read(1) == ']'):
					break
			if ser.read(1) == ':':
				ser.flushInput()
				printf(" Ok\n")
				return
		else:
			t_now = time.time()
			if(t_now >= (t_prompt + 1)):
				t_prompt = t_now
				printf(".")

def memreadblock(ser, addr, size):
	while ser.read(1):
		pass
	ser.write('R')
	while not (ser.read(1)=='0' and ser.read(1)=='x'):
		pass
	ser.write("%x"%addr)
	ser.write('\r')
	while not (ser.read(1)=='.' and ser.read(1)=='.' and ser.read(1)=='.'):
		pass
	ser.write('3')
	while not ser.read(1)==')':
		pass
	ser.write(str(size))
	ser.write('\r')
	buf=''
	m = False
	while not m:
		line = ser.readline().strip()
		m = lineregex.match(line)
	while m:
		bytes = [chr(int(x, 16)) for x in m.group(1)[1:].split(' ')]
		buf+=''.join(bytes)
		m = lineregex.match(ser.readline().strip())
	return buf

def memreadblock2file(ser, fd, addr, size):
	while True:
		buf = memreadblock(ser, addr, size)
		if len(buf) == size:
			break
		printf(' [!]\n')
	printf(' [.]\n')
	fd.write(buf)
	return

def memread(ser, path, addr, size, block, delay, password):
	wait_prompt(ser, delay, password)
	total_size = size
	fd = open(path, "wb")
	while size > 0:
		cur_size = (total_size - size)
		printf('%d%% (%d/%d)' %((cur_size / total_size) * 100, cur_size, total_size))
		if size > block:
			memreadblock2file(ser, fd, addr, block)
			size -= block
			addr += block
		else:
			memreadblock2file(ser, fd, addr, size)
			size = 0
	fd.close()
	return

def main():
	optparser = OptionParser("usage: %prog [options]",version="%prog 0.1")
	optparser.add_option("--block", dest="block", help="buffer block size", default="4096",metavar="block")
	optparser.add_option("--serial", dest="serial", help="specify serial port", default="/dev/ttyUSB0", metavar="dev")
	optparser.add_option("--read", dest="read", help="read mem to file", metavar="path")
	optparser.add_option("--addr", dest="addr",help="mem address", metavar="addr")
	optparser.add_option("--size", dest="size",help="size to copy", metavar="bytes")
	optparser.add_option("--delay", dest="delay",help="seconds to wait for cli", default="3", metavar="delay")
	optparser.add_option("--pass", dest="password",help="bootloader secret key", default="Oh!123Go", metavar="pass")
	(options, args) = optparser.parse_args()
	if len(args) != 0:
		optparser.error("incorrect number of arguments")
	ser = serial.Serial(options.serial, 115200, timeout=1)
	if options.read:
		memread(ser, options.read, int(options.addr, 0), int(options.size, 0), int(options.block, 0), int(options.delay, 0), options.password)
	return

if __name__ == '__main__':
	main()
