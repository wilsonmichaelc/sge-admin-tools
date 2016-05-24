#!/usr/bin/python

import os

def add_home(ip):
    os.system("scp root@%s:/etc/fstab ." % ip)
    os.system("sed -i '/gru\:\/home/d' fstab")
    with open("fstab", "a") as fstab:
        fstab.write("\n")
        fstab.write("gru:/home/\t/home\tnfs4\t_netdev,auto\t0\t0\n")
    os.system("scp fstab root@%s:/etc/fstab" % ip)
    os.system("rm fstab")
    return

def remove_home(ip):
    os.system("scp root@%s:/etc/fstab ." % ip)
    os.system("sed -i '/gru\:\/home/d' fstab")
    os.system("scp fstab root@%s:/etc/fstab" % ip)
    os.system("rm fstab")
    os.system("ssh root@%s 'mount -a'" % ip)
    return
