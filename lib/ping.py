#!/usr/bin/python

import os, time

def host_alive(ip):
    response = os.system("ping -c 1 " + ip)
    if response == 0:
        time.sleep(2)
        return True
    else:
        return False

def reboot(ip):
    os.system("ssh root@%s 'shutdown -r now'" % ip)
    time.sleep(5)
    x = host_alive(ip)
    while not x:
        print(".")
        time.sleep(1)
        x = host_alive(ip)
    return
