from mini.menu import *
from plur_linux.nodes.util import *
from plur_linux.recipes.kvm.adhoc_setup import generic


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


