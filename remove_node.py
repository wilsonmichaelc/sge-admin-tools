#!/usr/bin/python

import os, sys, getpass
from lib import fstab, sge, hosts, nodelist, network

#   Make sure the script is being run as root
whoami = getpass.getuser()
if whoami != 'root':
    print('This script must be run as root')
    sys.exit()
else:
    print('Running as root... OK')

#   Ask wich node is being removed
if os.stat("nodelist").st_size != 0:
    nodes = nodelist.read_nodelist()
    print("\n------ Nodes ------")
    for i,n in enumerate(nodes):
        print("%d: %s" % (i, n))
    choice = raw_input("\nSelect a node to remove: ")
    try:
        choice = int(choice)
    except ValueError:
        print("That's not a valid selection!")
        sys.exit()
    if choice > len(nodes) or choice < 0:
        print("That's not a valid selection!")
        sys.exit()
    node = nodes[choice]
else:
    print("There are no nodes to remove.")
    sys.exit()

# Get this IP
ip = "10.0.0." + node[-3:]

#   Remove node from grid engine
print("Removing node from grid engine...")
sge.remove_node(node)

#   Remove fstab entry
print("Removing fstab entry...")
fstab.remove_home(ip)

#   Remove network interface
print("Removing interface for enp0s8")
network.remove_interface(ip)

print("Resetting hostname...")
hosts.set_hostname("minion", ip)

#   Node is safe to delete
print("Sending shutdown signal...")
os.system("ssh root@%s 'shutdown -h now'" % ip)
print("Node is powering off...")

#   Remove node from nodelist and hosts
print("Removing node from nodelist...")
nodelist.remove_node(node)
print("Removing node from hosts file...")
hosts.remove_node(node)

print("Done.")
