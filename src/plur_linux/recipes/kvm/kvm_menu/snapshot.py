from mini.menu import *
from plur import session_wrap
from plur import base_shell
from recipes.kvm.kvm_ops import snapshot
from . import lib


def menu_info_snapshot(vmname):
    def func(session):
        snapshotname = get_input('[a-zA-Z][a-zA-Z0-9_-]+', f'Please input info snapshotname for {vmname}: ')
        return snapshot.info_snapshot(vmname, snapshotname)(session)
    return func


def menu_create_snapshot(vmname):
    def func(session):
        snapshotname = get_input('[a-zA-Z][a-zA-Z0-9_-]+', f'Please input create snapshotname for {vmname}: ')
        return snapshot.create_snapshot(vmname, snapshotname)(session)
    return func


def menu_delete_snapshot(vmname):
    def func(session):
        snapshotname = get_input('[a-zA-Z][a-zA-Z0-9_-]+', f'Please input delete snapshotname for {vmname}: ')
        return snapshot.delete_snapshot(vmname, snapshotname)(session)
    return func


def menu_revert_snapshot(vmname):
    def func(session):
        snapshotname = get_input('[a-zA-Z][a-zA-Z0-9_-]+', f'Please input revert snapshotname for {vmname}: ')
        return snapshot.revert_snapshot(vmname, snapshotname)(session)
    return func


@session_wrap.sudo
def menu_on_kvm(session):
    vmname = lib.select_vmname(session, yellow('Please select Number to snapshot: '))

    def inner(session):
        snapshot.list_snapshot(vmname)(session)
        menu_list = [
            ['info snapshot', menu_info_snapshot(vmname)]
            , ['create snapshot', menu_create_snapshot(vmname)]
            , ['delete snapshot', menu_delete_snapshot(vmname)]
            , ['revert to snapshot', menu_revert_snapshot(vmname)]
            , ['Back']
        ]

        num = choose_num([item[0] for item in menu_list], append_exit=True)
        if num == len(menu_list) - 1:
            return
        else:
            menu_list[num][1](session)
            return inner(session)

    return inner(session)
