#! /usr/bin/env python
import os
import sys
sys.path.append(os.pardir)
from plur import base_shell
from plur import session_wrap
from recipes.kvm import virsh
from recipes.kvm import qemu_img
import getpass
import re
from recipes.ops import ssh


def get_backingfile_path(node, filepath):
    session = node.session
    info = qemu_img.info(session, filepath)
    for line in re.split('\n|\r\n', info):
        if re.match('^backing file: .+ \(actual path: ', line):
            backingfile = re.split('\(actual path: |\)', line)[1]
            return backingfile

        if re.match('^backing file: .+', line):
            backingfile = re.split(': | \(actual', line)[1]
            return backingfile

    return False


def get_all_backingfile(node, filepath):
    bf_list = []
    while True:
        bf = get_backingfile_path(node, filepath)
        if bf:
            bf_list += [bf]
            filepath = bf
        else:
            break

    return bf_list


def migrate_storage_inc(mig_from, mig_to, vmlist):
    if not hasattr(mig_from, 'password'):
        mig_from.password = getpass.getpass('Input %s ssh password:' % mig_from.hostname)
    if not hasattr(mig_to, 'password'):
        mig_to.password = getpass.getpass('Input %s ssh password:' % mig_to.hostname)

    session_from = session_wrap.ssh(mig_from)
    mig_from.session = session_from

    okvmlist = []
    okvm_backingfile_list = []
    okvm_allbackingfile_list = []
    for vm in vmlist:
        # check guest can be migrated by storage migration
        if vm.diskformat == "qcow2":
            # check guest is running
            if virsh.isRunning(session_from, vm.vmname):
                print('Domain is running, continue.')
                okvmlist += [vm]

                vdisk_path = f'/vm_images/{vm.hostname}.qcow2'
                okvm_backingfile_list += [dict(vm=vdisk_path, bfile=get_backingfile_path(mig_from, vdisk_path))]
                okvm_allbackingfile_list += get_all_backingfile(mig_from, vdisk_path)
            else:
                print('Domain is not running skip: ' + vm.vmname)

    session_from.close()

    # get backing filepath that not exists
    session_to = session_wrap.ssh(mig_to)
    bfile_copy_list = []
    for bfile in okvm_allbackingfile_list:
        if not base_shell.check_file_exists(session_to, bfile):
            bfile_copy_list += [bfile]
    session_to.close()

    # scp all backing file needed
    session_from = session_wrap.ssh(mig_from)
    for bfile in bfile_copy_list:
        src_file = bfile
        dst_file = mig_to.username + '@' + mig_to.hostname + ':' + bfile
        session_from.do(ssh.scp(src_file, dst_file))
    session_from.close()

    # create backing file on migto
    session_to = session_wrap.ssh(mig_to)
    for vm_dict in okvm_backingfile_list:
        qemu_img.backing(session_to, vm_dict['vm'], vm_dict['bfile'])
    session_to.close()

    # run storage migration
    session_from = session_wrap.ssh(mig_from)
    for vm in okvmlist:
        virsh.migrate_storageinc(session_from, vm.vmname, mig_to.hostname)
    session_from.close()


