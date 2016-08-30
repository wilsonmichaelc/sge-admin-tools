#!/usr/bin/python3
import subprocess, sys, os, time, getpass

#   Make sure the script is being run as root
whoami = getpass.getuser()
if whoami != 'root':
    print('This script must be run as root')
    sys.exit()

# Should be resolvable via hosts file
HEAD_NODE = "yourheadnode" 

# Directory where you archive old users home dirs: NO TRAILING SLASH
archivedir = "/home/archive"

# Min/Max UID & GID's
GID_MIN = 1500
GID_MAX = 1600
UID_MIN = 1600
UID_MAX = 1700

# Interface that nodes use for external connection.
# I leave these turned off unless needed. This script will bring up/take down external interfaces
EXTERNAL_INTERFACE = "eth0"

# The menu
menu = """
Welcome to the Grid Management Tool

This script helps you perform some common tasks on the nodes via ssh remote execute.

What would you like to do?

1.  Update/Upgrade Nodes
2.  Install a package from apt on Nodes
3.  Execute an R Script on Nodes(The script must specify a CRAN mirror)
4.  Add a system user to all nodes (including head node)
5.  Completely Remove a System User
6.  Add a group for a project
7.  Add existing user to a supplementary group
8.  Execute an arbitrary command on all nodes
9.  Restart Ganglia Monitor on all nodes
10.  Reboot the Nodes
0.  Quit.
"""

# Execute a command on each node
def execute(command):
    for node in nodes:
        print("Executing '%s' on %s" % (command, node))
        ip = subprocess.check_output(["getent hosts %s | cut -d' ' -f1" % node], shell=True).decode('ascii').strip()
        proc = subprocess.Popen(["ssh", "%s" % ip, command], shell=False, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        out, err = proc.communicate()
        if proc.returncode != 0:
            print("Failed to execute on %! \nERROR\n%s" % (node, err))
            
def execute_arb(command):
    for node in nodes:
        print("Executing '%s' on %s" % (command, node))
        ip = subprocess.check_output(["getent hosts %s | cut -d' ' -f1" % node], shell=True).decode('ascii').strip()
        proc = subprocess.Popen(["ssh", "%s" % ip, command], shell=False, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        out, err = proc.communicate()
        if proc.returncode != 0:
            print("Failed to execute on %! \nERROR\n%s" % (node, err))
        else:
            print("Response: %s" % out)

# Bring up the external interfaces
def ifup():
    for node in nodes:
        ip = subprocess.check_output(["getent hosts %s | cut -d' ' -f1" % node], shell=True).decode('ascii').strip()
        proc = subprocess.Popen(["ssh", "%s" % ip, "ifup %s" % EXTERNAL_INTERFACE], shell=False, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        out, err = proc.communicate()
        if proc.returncode != 0:
            print("Failed to execute on %! \nERROR\n%s" % (node, err))
        else:
            command = "ifconfig %s | grep 'inet addr' | cut -d':' -f2 | cut -d' ' -f1" % EXTERNAL_INTERFACE
            proc = subprocess.Popen(["ssh", "%s" % ip, command], shell=False, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            out, err = proc.communicate()
            if proc.returncode != 0:
                print("Failed to execute on %s! \nERROR\n%s" % (ip, err))
            else:
                print("%s %s up, ip: %s" % (node, EXTERNAL_INTERFACE, out.decode('ascii').strip()))

# Take down the external interfaces
def ifdown():
    for node in nodes:
        ip = subprocess.check_output(["getent hosts %s | cut -d' ' -f1" % node], shell=True).decode('ascii').strip()
        proc = subprocess.Popen(["ssh", "%s" % ip, "ifdown %s" % EXTERNAL_INTERFACE], shell=False, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        out, err = proc.communicate()
        if proc.returncode != 0:
            print("Failed to execute on %! \nERROR\n%s" % (node, err))
        else:
            print("%s: %s down" % (node, EXTERNAL_INTERFACE))

# Add a system user and set the password expiration
def addSystemUser(fullname, username, uid, gid):
    print("Adding %s to %s" % (fullname, HEAD_NODE))
    os.system("useradd -m -d /home/%s -u %s -g %s  -c '%s' -s /bin/bash %s" % (username, uid, gid, fullname, username))
    os.system("chage -M 180 -I 5 -W 14 %s" % username)
    for node in nodes:
        print("Adding user %s to %s" % (fullname, node))
        ip = subprocess.check_output(["getent hosts %s | cut -d' ' -f1" % node], shell=True).decode('ascii').strip()
        command = "useradd -d /home/%s -u %s -g %s -c '%s' -s /bin/bash %s && chage -M 180 -I 5 -W 14 %s" % (username, uid, gid, fullname, username, username)
        proc = subprocess.Popen(["ssh", ip, command], shell=False, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        out, err = proc.communicate()
        if proc.returncode != 0:
            print("Failed to execute on %! \nERROR\n%s" % (node, err))

# Remove a system user and optionally archive the home directory before removing it
def removeSystemUser(username, archivedir):
    # Archive the users home directory
    if archivedir != "":
        homedir = subprocess.check_output(["grep %s /etc/passwd | cut -f6 -d:" % username], shell=True).decode('ascii').strip()
        print("%s's Home Directory: %s" % (username, homedir))
        archive = "%s/%s-%s" % (archivedir, username, time.strftime("%Y%m%d-%H%M%S"))
        print("Archiving %s's home directory to %s" % (username, archivedir))
        os.system("tar -zcf %s.tar.gz %s" % (archive, homedir))
    # Remove the user and home dir from head node
    print("Removing %s from %s" % (username, HEAD_NODE))
    os.system("userdel -r %s" % username)
    # Remove the user from all compute nodes
    for node in nodes:
        print("Removing %s from %s" % (username, node))
        ip = subprocess.check_output(["getent hosts %s | cut -d' ' -f1" % node], shell=True).decode('ascii').strip()
        command = "userdel %s" % username
        proc = subprocess.Popen(["ssh", ip, command], shell=False, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        out, err = proc.communicate()
        if proc.returncode != 0:
            print("Failed to execute on %! \nERROR\n%s" % (node, err))

# Get the next available UID based on the range provided above
def getNextUID():
    cmd = """awk -F: '{uid[$3]=1}END{for(x=%s; x<%s; x++) {if(uid[x] != ""){}else{print x; exit;}}}' /etc/passwd""" % (UID_MIN, UID_MAX)
    uid = subprocess.check_output(cmd, shell=True).decode('ascii').strip()
    return uid
    
# Get the next available UID based on the range provided above
def getNextGID():
    cmd = """awk -F: '{gid[$3]=1}END{for(x=%s; x<%s; x++) {if(gid[x] != ""){}else{print x; exit;}}}' /etc/group""" % (GID_MIN, GID_MAX)
    gid = subprocess.check_output(cmd, shell=True).decode('ascii').strip()
    return gid

# Get a list of groups from the range provided above
def getGroups():
    groups = {}
    for line in open('/etc/group', 'r'):
        parts = line.strip('\n').split(':')
        if int(parts[2]) >= GID_MIN and int(parts[2]) < GID_MAX:
            groups[parts[0]] = parts[2]
    return groups

# Get a list of nodes from SGE... actually execution hosts
def getNodes():
    # Get array of nodes
    nodes = []
    out = subprocess.Popen(["qconf", "-sel"], shell=False, stdout=subprocess.PIPE)
    for node in out.stdout:
        n = node.rstrip().decode('ascii')
        if n != HEAD_NODE:
            nodes.append(n)
    return nodes

# Initialize nodes/groups
nodes = getNodes()
groups = getGroups()

# Bring up interfaces before we start
print("Bringing up interfaces (this can take a minute or two)...")
ifup()

# Loop until user wants to quit.
selection = True
while selection:
    os.system('clear')
    print(menu)
    print("Please make sure no jobs are running on the cluster before attempting any maintenance that would adversly affect performance.")
    #print("Nodes in this cluster: %s" % nodes)

    selection = input("What would you like to do? ")
    os.system('clear')
    #
    #   Update/update all nodes
    #
    if selection == "1":
        print("\nUpdate/Upgrade All Nodes\n")
        print("\nWARNING!!!\n")
        print("You are about to perform an update/upgrade on all nodes.")
        confirm = input("Are you sure you want to continue (y/N)? ")
        if confirm == "y" or confirm == "Y":
            execute("apt-get update")
            execute("apt-get -y upgrade")
            time.sleep(2)
        else:
            print("CANCELED. Returning to menu...")
            time.sleep(2)
    #
    #   Install package(s) on all nodes
    #
    elif selection == "2":
        print("\nInstall package(s) on All Nodes\n")
        packages = input("Package(s) to install from apt-get... separated by a single space: ")
        print("\nWARNING!!!\n")
        print("You are about to install the following packages on all nodes.\n%s" % packages)
        confirm = input("Are you sure you want to continue (y/N)? ")
        if confirm == "y" or confirm == "Y":
            execute("apt-get install -y %s" % packages)
            time.sleep(2)
        else:
            print("CANCELED. Returning to menu...")
            time.sleep(2)
    #
    #   Execute an R script on all nodes
    #
    elif selection == "3":
        print("\nExecute An R Script On All Nodes (The script must specify a CRAN mirror)\n")
        print("Script must be somewhere inside the home directory and must be executable.\n")
        full_path = input("Full path to script: ")
        print("\nWARNING!!!\n")
        print("You are about to execute an R script on all nodes.")
        confirm = input("Are you sure you want to continue (y/N)? ")
        if confirm == "y" or confirm == "Y":
            execute("Rscript " + full_path)
            time.sleep(2)
        else:
            print("CANCELED. Returning to menu...")
            time.sleep(2)
    #
    #   Add a system user to all nodes (including head)
    #
    elif selection == "4":
        print("\nAdd A System User To All Nodes (including head node)\n")
        fullname = input("Full Name: ")
        username = input("Username (lowercase recommended): ")
        print("\nAdd A System User To All Nodes (including head node)\n")
        fullname = input("Full Name: ")
        avail_grps = "Available Groups: "
        for group, gid in groups.items():
            avail_grps = "%s %s=%s" % (avail_grps, group, gid)
        print(avail_grps)
        gid = input("Select a GID (eg. 1500): ")
        print("\nWARNING!!!\n")
        print("You are about to add the following system user to all nodes (including %s)." % HEAD_NODE)
        print("Full Name[%s], Username[%s], UID[%s], GID[%s]" % (fullname, username, uid, gid))
        confirm = input("Are you sure you want to continue (y/N)? ")
        if confirm == "y" or confirm == "Y":
            addSystemUser(fullname, username, uid, gid)
            time.sleep(2)
        else:
            print("CANCELED. Returning to menu...")
            time.sleep(2)
    #
    #   Archive users home directory
    #   Remove a system user from all nodes (including head node)
    #
    elif selection == "5":
        print("\nCompletely Remove A System User\n")
        username = input("Username: ")
        archive = input("Do you want to archive this users home directory (Y/n)? ")
        print("\nWARNING!!!\n")
        print("You are about to remove the following system user from all nodes (including %s)." % HEAD_NODE)
        print("Username: %s" % username)
        confirm = input("Are you sure you want to continue (y/N)? ")
        if confirm == "y" or confirm == "Y":
            if archive == "n" or archive == "N":
                removeSystemUser(username, "")
            else:
                removeSystemUser(username, archivedir)
            time.sleep(2)
        else:
            print("CANCELED. Returning to menu...")
            time.sleep(2)
    #
    #   Add a new group
    #
    elif selection == "6":
        print("\nAdd A New Group To All Nodes (including head node)\n")
        groupname = input("Group Name: ")
        gid = getNextGID()
        print("\nWARNING!!!\n")
        print("You are about to add the following group all the nodes.")
        print("Group: %s:%s" % (groupname, gid))
        confirm = input("Are you sure you want to continue (y/N)? ")
        if confirm == "y" or confirm == "Y":
            command = "groupadd -g %s %s" % (gid, groupname)
            execute(command)
            time.sleep(2)
        else:
            print("CANCELED. Returning to menu...")
            time.sleep(2)
    #
    #   Add existing user to existing group
    #
    elif selection == "7":
        print("\nAdd Existing User To Group On All Nodes (including head node)\n")
        username = input("Username: ")
        avail_grps = "Available Groups: "
        groups = getGroups()
        for group, gid in groups.items():
            avail_grps = "%s %s=%s" % (avail_grps, group, gid)
        print(avail_grps)
        gid = input("Select a GID (eg. 1500): ")
        while not gid in groups.values():
            print("Not a valid GID.")
            gid = input("Select a GID (eg. 1500): ")
        print("\nWARNING!!!\n")
        print("You are about to add %s as supplementary group for %s on all the nodes." % (gid, username))
        confirm = input("Are you sure you want to continue (y/N)? ")
        if confirm == "y" or confirm == "Y":
            command = "usermod -a -G %s %s" % (gid, username)
            execute(command)
            time.sleep(2)
        else:
            print("CANCELED. Returning to menu...")
            time.sleep(2)
    #
    #   Execute arbitrary command on all nodes
    #
    elif selection == "8":
        print("\nExecute an arbitrary command on all nodes\n")
        print("\nWARNING!!!\n")
        print("\nUSE THIS VERY CAREFULLY\n")
        print("\nWARNING!!!\n")
        command = input("Command you would like to run: ")
        print("You are about to execute the following command on all the nodes.")
        print("Command: %s" % command)
        confirm = input("Are you sure you want to continue (y/N)? ")
        if confirm == "y" or confirm == "Y":
            execute_arb(command)
            time.sleep(2)
        else:
            print("CANCELED. Returning to menu...")
            time.sleep(2)
    #
    #   Restart ganglia monitor on all nodes
    #
    elif selection == "9":
        print("\nRestart Ganglia Monitor On All Nodes\n")
        print("You are about to restart the ganglia monitor service on all the nodes.")
        confirm = input("Are you sure you want to continue (y/N)? ")
        if confirm == "y" or confirm == "Y":
            execute("service ganglia-monitor restart")
            time.sleep(2)
        else:
            print("CANCELED. Returning to menu...")
            time.sleep(2)
    #
    #   Reboot all nodes
    #
    elif selection == "10":
        print("\nReboot All The Nodes\n")
        print("\nWARNING!!!\n")
        print("You are about to reboot all the nodes.")
        confirm = input("Are you sure you want to continue (y/N)? ")
        if confirm == "y" or confirm == "Y":
            execute("shutdown -r now")
            time.sleep(2)
        else:
            print("CANCELED. Returning to menu...")
            time.sleep(2)
    #
    #   Exit this tool
    #
    elif selection == "0":
        selection = None
        print("Taking down external interfaces...")
        ifdown()
    else:
        print("Unknown option selected!")


print("Goodbye!")
