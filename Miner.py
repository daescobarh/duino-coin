#!/usr/bin/env python

###########################################
#     Duino-Coin PC miner version 0.6     #
# https://github.com/revoxhere/duino-coin #
#  copyright by MrKris7100 & revox 2019   #
###########################################

import socket, threading, time, random, hashlib, configparser, sys
from pathlib import Path

VER = "0.6"

def hush():
	global last_hash_count, hash_count
	last_hash_count = hash_count
	hash_count = 0
	threading.Timer(1.0, hush).start()
	
shares = [0, 0]
last_hash_count = 0
hash_count = 0
config = configparser.ConfigParser()

if not Path("MinerConfig.ini").is_file():
	print("Initial configuration, you can edit 'MinerConfig.ini' file later.")
	print("Don't have an account? Use Wallet to register.\n")
	pool_address = input("Enter pool adddress (official: serveo.net): ")
	pool_port = input("Enter pool port (official: 14808): ")
	username = input("Enter username: ")
	password = input("Enter password: ")
	config['pool'] = {"address": pool_address,
	"port": pool_port,
	"username": username,
	"password": password}
	with open("MinerConfig.ini", "w") as configfile:
		config.write(configfile)
else:
	config.read("MinerConfig.ini")
	pool_address = config["pool"]["address"]
	pool_port = config["pool"]["port"]
	username = config["pool"]["username"]
	password = config["pool"]["password"]

while True:
	print("Connecting to pool...")
	soc = socket.socket()
	try:
		soc.connect((pool_address, int(pool_port)))
		print("Connected!")
		break
	except:
		print("Cannot connect to pool server. Retrying in 30 seconds...")
		time.sleep(30)
	time.sleep(0.025)
	
print("Checking version...")
SERVER_VER = soc.recv(1024).decode()
if SERVER_VER == VER:
	print("Miner is up-to-date.")
else:
	print("Miner is outdated, please download latest version from https://github.com/revoxhere/duino-coin/releases/")
	print("Exiting in 5s.")
	time.sleep(5)
	sys.exit()
	
print("Logging in...")
soc.send(bytes("LOGI," + username + "," + password, encoding="utf8"))
while True:
	resp = soc.recv(1024).decode()
	if resp == "OK":
		print("Logged in!")
		break
	if resp == "NO":
		print("Error, closing in 5 seconds...")
		soc.close()
		time.sleep(5)
		sys.exit()
	time.sleep(0.025)

print("Started mining thread...")
hush()
while True:
	soc.send(bytes("JOB", encoding="utf8"))
	while True:
		job = soc.recv(1024).decode()
		if job:
			break
		time.sleep(0.025)

	job = job.split(",")
	print("Recived new job from pool, difficulty: " + job[2])
	for iJob in range(100 * int(job[2]) + 1):
		hash = hashlib.sha1(str(job[0] + str(iJob)).encode("utf-8")).hexdigest()
		hash_count = hash_count + 1
		if job[1] == hash:
			soc.send(bytes(str(iJob) + "," + str(last_hash_count), encoding="utf8"))
			while True:
				good = soc.recv(1024).decode()
				if good == "GOOD":
					shares[0] = shares[0] + 1 # Share accepted
					print("Share accepted " + str(shares[0]) + "/" + str(shares[0] + shares[1]) + " (" + str(shares[0] / (shares[0] + shares[1]) * 100) + "%), " + str(last_hash_count) + " H/s (yay!!!)")
					break
				elif good == "BAD":
					shares[1] = shares[1] + 1 # SHare rejected
					print("Share rejected " + str(shares[0]) + "/" + str(shares[0] + shares[1]) + " (" + str(shares[0] / (shares[0] + shares[1]) * 100) + "%), " + str(last_hash_count) + " H/s (boo!!!)")
					break
				time.sleep(0.025)
			break
