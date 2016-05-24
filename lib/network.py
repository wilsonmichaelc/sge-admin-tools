#!/usr/bin/python

import os

interfaces = """
# This file describes the network interfaces available on your system
# and how to activate them. For more information, see interfaces(5).

source /etc/network/interfaces.d/*

# The loopback network interface
auto lo
iface lo inet loopback

# The primary network interface
auto enp0s3
iface enp0s3 inet dhcp

"""

def add_interface(new_ip, tmp_ip):
    global interfaces
    i = interfaces + "auto enp0s8\niface enp0s8 inet static\n\taddress %s\n\tnetmask 255.255.255.0\n\tgateway 10.0.0.1\n" % new_ip
    with open("interfaces", "w") as iface:
        iface.write(i)
    os.system("scp interfaces root@%s:/etc/network/interfaces" % tmp_ip)
    os.system("rm interfaces")
    return

def remove_interface(ip):
    global interfaces
    with open("interfaces", "w") as iface:
        iface.write(interfaces)
    os.system("scp interfaces root@%s:/etc/network/interfaces" % ip)
    os.system("rm interfaces")
    return
