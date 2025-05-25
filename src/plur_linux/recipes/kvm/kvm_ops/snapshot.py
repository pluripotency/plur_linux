import re
from plur import base_shell


def info_snapshot(vmname, snapshotname=None):
    def on_kvm(session):
        if snapshotname:
            capt = base_shell.run(session, f'virsh snapshot-info --domain {vmname} --snapshotname {snapshotname}')
        else:
            capt = base_shell.run(session, f'virsh snapshot-info --domain {vmname} --current')
        return capt
    return on_kvm


def list_snapshot(vmname):
    def on_kvm(session):
        capt = base_shell.run(session, f'virsh snapshot-list --domain {vmname}')
        on_entry = False
        entries = []
        for line in re.split('\n', capt):
            if re.search('^----+', line):
                on_entry = True
            if on_entry:
                entries.append(line)
        return entries
    return on_kvm


def create_snapshot(vmname, snapshotname):
    def on_kvm(session):
        return base_shell.run(session, f'virsh snapshot-create-as --domain {vmname} --name {snapshotname}')
    return on_kvm


def delete_snapshot(vmname, snapshotname):
    def on_kvm(session):
        return base_shell.run(session, f'virsh snapshot-delete --domain {vmname} --snapshotname {snapshotname}')
    return on_kvm


def revert_snapshot(vmname, snapshotname):
    def on_kvm(session):
        return base_shell.run(session, f'virsh snapshot-revert --domain {vmname} --snapshotname {snapshotname}')
    return on_kvm


