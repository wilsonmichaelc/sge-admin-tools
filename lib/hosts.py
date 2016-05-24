#!/usr/bin/python

import os

def add_node(headnode, nodes, new_ip, new_node, tmp_ip):
    with open("/etc/hosts", "w") as hosts:
        hosts.write("127.0.0.1\tlocalhost\n")
        hosts.write("10.0.0.100\t%s\n" % headnode)
        if len(nodes) > 0:
            for node in nodes:
                hosts.write("10.0.0.%s\t%s\n" % (node[-3:], node))
        hosts.write("%s\t%s\n" % (new_ip, new_node))
    # Send the file over
    if len(nodes) > 0:
        for node in nodes:
            os.system("scp /etc/hosts root@%s:/etc/hosts" % node)
    os.system("scp /etc/hosts root@%s:/etc/hosts" % tmp_ip)
    return

def set_hostname(node, ip):
    with open("hostname", "w") as hostname:
        hostname.write(node)
    os.system("scp hostname root@%s:/etc/hostname" % ip)
    os.system("rm hostname")
    return

def remove_node(node):
    os.system("sed -i '/%s/d' /etc/hosts" % node)
    return
