#!/usr/bin/python

import hashlib
from base64 import urlsafe_b64encode as encode
from base64 import urlsafe_b64decode as decode
import crypt, getpass
import getpass
import fileinput
import argparse
import sys
import os
import platform

parser = argparse.ArgumentParser()

parser.add_argument('--action', type=str, choices=['create_env', 'rebuild_env', 'destroy_env'])
parser.add_argument('--bitbucket_username', type=str, required = True)
parser.add_argument('--linux_username', type=str, required = True)

args = parser.parse_args()

if not os.geteuid() == 0:
	sys.exit('Script must be run as root')

platform = platform.dist()

if platform[1] == "14.04" or platform[1] == "14.10":
        deb = "deb https://apt.dockerproject.org/repo ubuntu-trusty main"

elif platform[1] == "12.04" or platform[1] == "12.10":
	deb = "deb https://apt.dockerproject.org/repo ubuntu-precise main"

elif platform[1] == "15.04" or platform[1] == "15.10":
	deb = "deb https://apt.dockerproject.org/repo ubuntu-wily main"

def replaceAll(file,searchExp,replaceExp):
    for line in fileinput.input(file, inplace=1):
        if searchExp in line:
            line = line.replace(searchExp,replaceExp)
        sys.stdout.write(line)

def makeSecret(password):
    salt = os.urandom(4)
    h = hashlib.sha1(password)
    h.update(salt)
    return "{SSHA}" + encode(h.digest() + salt)

if args.action == 'create_env':
	os.system("sudo ntpdate -s ntp.ubuntu.com")
	os.system("sudo sh -c 'echo \"deb http://download.virtualbox.org/virtualbox/debian $(lsb_release -cs) contrib\" >> /etc/apt/sources.list.d/virtualbox.list'")
	os.system("wget -q https://www.virtualbox.org/download/oracle_vbox.asc -O- | sudo apt-key add -")
	os.system("sudo apt-get update; sudo apt-get install -y virtualbox-5.0 apt-transport-https ca-certificates python-pip git")
        os.system("sudo apt-key adv --keyserver hkp://p80.pool.sks-keyservers.net:80 --recv-keys 58118E89F3A912897C070ADBF76221572C52609D")
        os.system("sudo touch /etc/apt/sources.list.d/docker.list; sudo chmod 777 /etc/apt/sources.list.d/docker.list;  echo \"%s\" > /etc/apt/sources.list.d/docker.list" % deb)
	os.system("sudo apt-get update; sudo apt-get install docker-engine -y; sudo gpasswd -a %s docker" % args.linux_username)
	os.system("echo \"DOCKER_OPTS=\\\"-H tcp://127.0.0.1:2375 -H unix:///var/run/docker.sock\\\"\" | sudo tee /etc/default/docker > /dev/null")
	os.system("sudo service docker restart; sudo pip install docker-compose")
	os.system("sudo curl -L https://github.com/docker/machine/releases/download/v0.6.0/docker-machine-`uname -s`-`uname -m` > /usr/local/bin/docker-machine && sudo chmod +x /usr/local/bin/docker-machine")
	os.system("git clone https://%s@bitbucket.org/authdash/authoriti-dashboard-environment.git ~/authoriti/authoriti_env" % args.bitbucket_username)
	os.system("git clone https://%s@bitbucket.org/authdash/authoriti-dashboard.git ~/authoriti/authoriti_dash" % args.bitbucket_username)
	os.system("cd ~/authoriti/authoriti_env; docker-machine create -d virtualbox dev; docker-machine regenerate-certs dev;  eval $(docker-machine env dev)")
	os.system("docker-compose build; docker-compose up -d")
