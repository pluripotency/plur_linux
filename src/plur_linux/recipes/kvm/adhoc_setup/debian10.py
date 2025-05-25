from mini.menu import *
from nodes.util import *
from recipes.kvm.adhoc_setup import run_account, generic


def get_selection():
    platform = 'debian'
    vm = {
        'hostname': 'localhost',
        'platform': platform,
        'ssh_options': '-o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null',
        'size': 10,
    }
    postrun_list = [
    ]
    return [vm, postrun_list]


