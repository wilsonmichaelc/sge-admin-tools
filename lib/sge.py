#!/usr/bin/python

import os, time

def add_node(node, cores):
    # Modify the template for this node
    os.system("sed -i -e 's/template/%s/g' fname" % node)
    # Add the exec node using the template
    os.system("sudo -u sgeadmin qconf -Ae fname")
    # Add the node to the main queue
    os.system("sudo -u sgeadmin qconf -aattr queue slots [%s=%s] main.q" % (node, cores))
    # Add the node to the host list
    os.system("sudo -u sgeadmin qconf -aattr hostgroup hostlist %s @allhosts" % node)
    # Reset the template
    os.system("sed -i -e 's/%s/template/g' fname" % node)
    return

def remove_node(node):
    #print("Disabling node to prevent job allocation...")
    os.system("sudo -u sgeadmin qmod -d main.q@%s" % node)
    #print("Waiting for jobs to finish...")
    time.sleep(10) #TODO: check that node is actually done working on jobs before killing it
    os.system("sudo -u sgeadmin qconf -ke %s" % node)
    #print("Removing node from cluster...")
    os.system("sudo -u sgeadmin qconf -purge queue slots main.q@%s" % node)
    #print("Removing node from host group...")
    os.system("sudo -u sgeadmin qconf -dattr hostgroup hostlist %s @allhosts" % node)
    #print("Removing node from execution host list...")
    os.system("sudo -u sgeadmin qconf -de %s" % node)
    return
