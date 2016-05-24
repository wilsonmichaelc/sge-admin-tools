#!/usr/bin/python

import os

def read_nodelist():
    if os.stat("nodelist").st_size > 1:
        nodes = sorted([line.strip('\n') for line in open("nodelist")], key=lambda x: x[-3:])
        nodes = filter(None, nodes)
        return nodes
    else:
        return []

def add_node(node):
    with open("nodelist", "a") as nodelist:
        nodelist.write("%s\n" % node)
    return

def remove_node(node):
    os.system("sed -i '/%s/d' nodelist" % node)
    return
