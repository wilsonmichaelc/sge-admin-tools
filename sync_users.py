#!/usr/bin/python

import os
import sys

#
#   Config
#

# min/max user ids
UID_MIN = 1500
UID_MAX = 1600
# min/max group ids
GID_MIN = 1500
GID_MAX = 1600
# Generate output files... this overwrites the *.node files
GENERATE_FILES = True
# Print output to terminal
TERMINAL_OUT = False

#
#   Some globals to track stuff
#
users = []
groups = []

#
#   Create a new passwd file
#
def passwd():
    # Read in passwd data for both files
    master = set(line.strip('\n') for line in open('./tmp/passwd.master'))
    node = set(line.strip('\n') for line in open('./tmp/passwd.node'))

    # Remove entries from node where ID in range UID_MIN to UID_MAX
    for n in node.copy():
        if UID_MIN <= int(n.split(':')[2]) < UID_MAX:
            node.remove(n)

    # Find entires in master where ID in range UID_MIN to UID_MAX
    #   Insert these into node.
    for n in master:
        if UID_MIN <= int(n.split(':')[2]) < UID_MAX:
            node.add(n)
            users.append(n.split(':')[0])

    # Sort by UID just for fun
    node = list(node)
    node.sort(key=lambda x: int(x.split(':')[2]))

    # Write out the new passwd file
    if GENERATE_FILES:
        f = open('./tmp/passwd.node', 'w')
        f.truncate()
        for l in node:
            if TERMINAL_OUT:
                print(l)
            f.write(l)
            f.write("\n")
        f.close()

    if TERMINAL_OUT:
        print("------------------------------------ passwd ------------------------------------")
        for l in node:
            print(l)

#
#   Create a new shadow file
#
def shadow():
    # New shadow file array
    shadow = []
    # Get the lines from the node's shadow file that are not users we need to change.
    #   Add them to the new shadow file array
    for line in open('./tmp/shadow.node'):
        line = line.strip('\n')
        if line.split(':')[0] not in users:
            shadow.append(line)
    # Get the lines from the master's shadow file that ARE users we need to change.
    #   Add them to the new shadow file array
    for line in open('./tmp/shadow.master'):
        line = line.strip('\n')
        if line.split(':')[0] in users:
            shadow.append(line)

    # Write out the new shadow file for the nodes
    if GENERATE_FILES:
        f = open('./tmp/shadow.node', 'w')
        f.truncate()
        for l in shadow:
            if TERMINAL_OUT:
                print(l)
            f.write(l)
            f.write("\n")
        f.close()

    if TERMINAL_OUT:
        print("------------------------------------ shadow ------------------------------------")
        for l in shadow:
            print(l)

#
#   Create a new group file
#
def group():
    master = [line.strip('\n') for line in open('./tmp/group.master')]
    node = [line.strip('\n') for line in open('./tmp/group.node')]
    # New group file
    group = []

    # First read the group master file and pull out the lines where GID in our defined range
    for line in node:
        if int(line.split(':')[2]) not in range(GID_MIN, GID_MAX):
            group.append(line)

    for line in master:
        if int(line.split(':')[2]) in range(GID_MIN, GID_MAX):
            group.append(line)
            groups.append(line.split(':')[0])

    # Write out the new shadow file for the nodes
    if GENERATE_FILES:
        f = open('./tmp/group.node', 'w')
        f.truncate()
        for l in group:
            if TERMINAL_OUT:
                print(l)
            f.write(l)
            f.write("\n")
        f.close()

    if TERMINAL_OUT:
        print("------------------------------------- group ------------------------------------")
        for l in group:
            print(l)

#
#   Create a new gshadow file
#
def gshadow():
    # New shadow file array
    gshadow = []

    # Get the lines from the node's gshadow file that are not users we need to change.
    #   Add them to the new gshadow file array
    for line in open('./tmp/gshadow.node'):
        line = line.strip('\n')
        if line.split(':')[0] not in groups:
            gshadow.append(line)
    # Get the lines from the master's gshadow file that ARE users we need to change.
    #   Add them to the new gshadow file array
    for line in open('./tmp/gshadow.master'):
        line = line.strip('\n')
        if line.split(':')[0] in groups:
            gshadow.append(line)

    # Write out the new gshadow file for the nodes
    if GENERATE_FILES:
        f = open('./tmp/gshadow.node', 'w')
        f.truncate()
        for l in gshadow:
            f.write(l)
            f.write("\n")
        f.close()

    if TERMINAL_OUT:
        print("------------------------------------ gshadow ------------------------------------")
        for l in gshadow:
            print(l)

#
#   Sync Users
#
def sync():
    # Get list of nodes
    nodelist = [line.strip('\n') for line in open('nodelist')]

    # Fetch files from first node, place in workdir
    print("Fetching local user data...")
    os.system("cp /etc/passwd ./tmp/passwd.master")
    os.system("cp /etc/shadow ./tmp/shadow.master")
    os.system("cp /etc/group ./tmp/group.master")
    os.system("cp /etc/gshadow ./tmp/gshadow.master")

    for node in nodelist:
        # Get data for this node
        print("Fetching user data for %s..." % node)
        os.system("scp root@%s:/etc/passwd ./tmp/passwd.node" % node)
        os.system("scp root@%s:/etc/shadow ./tmp/shadow.node" % node)
        os.system("scp root@%s:/etc/group ./tmp/group.node" % node)
        os.system("scp root@%s:/etc/gshadow ./tmp/gshadow.node" % node)

        # Make modifications to each local node file
        print("Updating user data for %s..." % node)
        passwd()
        shadow()
        group()
        gshadow()

        # SCP the newly synced data to the remote node
        print("Sending updated user data to %s" % node)
        os.system("scp ./tmp/passwd.node root@%s:/etc/passwd" % node)
        os.system("scp ./tmp/shadow.node root@%s:/etc/shadow" % node)
        os.system("scp ./tmp/group.node root@%s:/etc/group" % node)
        os.system("scp ./tmp/gshadow.node root@%s:/etc/gshadow" % node)

    # clean up files
    print("Cleaning up...")
    os.system("rm ./tmp/*")
    print("Done.\n")

sync()
