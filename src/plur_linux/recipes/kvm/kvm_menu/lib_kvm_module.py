from plur import base_node
from plur import session_wrap_by_node_dict
from lib import env_ops
from mini.ansi_colors import blue, green, cyan
from mini.menu import choose_num, select_2nd, get_input
from . import lib
kvm_module_list = [
    ['input KVM params', False],
    ['Me', False]
]
len_mod = len(kvm_module_list)


def create_kvm_dict(hostname, access_ip, username, password, platform):
    login_waitprompt = base_node.get_linux_waitprompt(platform, hostname, username)
    return {
        'platform': platform,
        'ssh_options': '-o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null',
        'access_ip': access_ip,
        'hostname': hostname,
        'username': username,
        'password': password,
        'waitprompt': login_waitprompt,
    }


def input_kvm_dict():
    hostname = 'localhost'
    access_ip = '127.0.0.1'
    username = 'worker'
    password = 'password'
    platform = 'almalinux9'
    hostname = get_input('[a-z][a-z0-9_]{0,30}', f'kvm(default={hostname}):', 'Invalid name', hostname)
    access_ip = get_input(r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}', f'kvm ip(default: {access_ip}): ', 'Invalid IP', access_ip)
    username = get_input(r'\w.', f'kvm username(default={username}):', default_value=username)
    password = get_input(r'\w.', f'kvm password(default={password}):', default_value=password)
    platform = get_input(r'\w.', f'kvm os platform(default={platform}):', default_value=platform)
    return create_kvm_dict(hostname, access_ip, username, password, platform)


def select_kvm():
    env_kvm_entry_list = env_ops.get_kvm_entry_list()
    menu_list = [item[0] for item in env_kvm_entry_list]
    num = choose_num(menu_list + [
        'Show all vm in kvm',
        'Other',
    ], blue("Please select KVM"))
    if num < len(menu_list):
        kvm = base_node.Node(create_kvm_dict(**env_kvm_entry_list[num][1]))
        return kvm
    elif num == len(menu_list):
        for item in env_kvm_entry_list:
            kvm_dict = create_kvm_dict(**item[1])
            print(cyan(f"\n{item[0]}"))
            log_params = {
                'enable_stdout': False
            }
            session_wrap_by_node_dict.ssh(kvm_dict, log_params)(lib.list_kvm_guests)()
        return select_kvm()
    else:
        num = choose_num([kvm[0] for kvm in kvm_module_list], blue("Please select KVM"))
        if num == len_mod - 1:
            return False
        elif num == len_mod - 2:
            return base_node.Node(input_kvm_dict())
        else:
            kvm = select_2nd(kvm_module_list[num][1].create_nodes())
            return kvm


def select_kvm_history(selection):
    num = choose_num([kvm[0] for kvm in kvm_module_list], blue("Please select KVM"))
    if num == len_mod - 1:
        selection.append({'key': 'kvm_module', 'index': [num]})
        return False
    elif num == len_mod - 2:
        kvm_params_dict = input_kvm_dict()
        selection.append({'key': 'kvm_module', 'index': [num, kvm_params_dict]})
        return base_node.Node(kvm_params_dict)
    else:
        selected_module = kvm_module_list[num]
        selected_module_list = selected_module[1].create_nodes()
        kvm_num = choose_num([mod[0] for mod in selected_module_list])
        selected_kvm_module = selected_module_list[kvm_num]
        print(green(f'kvm: KVM module: {selected_module[0]} > {selected_kvm_module[0]}'))
        selection.append({'key': 'kvm_module', 'index': [num, kvm_num]})
        return selected_kvm_module[1]()
 
