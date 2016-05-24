#!/usr/bin/python

import os, sys, socket, getpass
from lib import fstab, ping, sge, network, hosts, nodelist

#   Make sure the script is being run as root
whoami = getpass.getuser()

if whoami != 'root':
    print('This script must be run as root')
    sys.exit()
else:
    print('Running as root... OK')

# Get the name of the headnode... THIS NODE
headnode = socket.gethostname()

print("We'll need an IP address where the new node may be reached to get started.")
print("Login to the node and type `ifconfig` if you don't know it.")
tmp_ip = raw_input("IP Address: ")

if not ping.host_alive(tmp_ip):
    print("%s is not reachable. Exiting.")
    sys.exit()

#   Read in node list, sorting by IP
#   Determin next IP to use
print("Reading node list...")
nodes = nodelist.read_nodelist()
if len(nodes) > 0:
    num = (int(nodes[-1][-3:])+1)
    new_ip = "10.0.0." + str(num)
    new_node = "minion" + str(num)
else:
    new_ip = "10.0.0.101"
    new_node = "minion101"

#   Update the hosts file
print("Updating hosts file...")
hosts.add_node(headnode, nodes, new_ip, new_node, tmp_ip)

#   Set the hostname
print("Updating hostname...")
hosts.set_hostname(new_node, tmp_ip)

#   Generate network interfaces file for the new node
#   Replace the new nodes network interfaces file
print("Updating network interfaces...")
network.add_interface(new_ip, tmp_ip)

#   Fetch the new nodes fstab file
print("Adding mount for home directories...")
fstab.add_home(tmp_ip)

#   Finally, add the new node to the node list
print("Adding node to nodelist...")
nodelist.add_node(new_node)

#   Reboot node
print("Rebooting node...")
ping.reboot(tmp_ip)

#   Add this node to grid engine
print("Adding node to grid engine...")
sge.add_node(new_node, raw_input("How many cores does %s have?: " % new_node))

#   Perform final reboot
print("Going for last reboot...")
ping.reboot(new_ip)

#   Show the host list
os.system("sudo -u sgeadmin qhost")

print("done.")
