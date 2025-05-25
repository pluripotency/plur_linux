import re
from mini.ansi_colors import red, light_red
from mini.menu import get_input, choose_num
from mini import misc
from plur import base_node
from nodes import new_node

class VmAccount:
    def __init__(self, vm):
        from lib import env_ops
        self.vm = vm
        self.env_account_set_list = env_ops.EnvAccountSet()
        self.user_list = self.env_account_set_list.get_current_index_account_set_as_user_list()
        self.set_users()

    def set_users(self):
        self.vm['offline_setups'] = {
            'users': self.user_list
        }
        for user in self.user_list:
            if user['username'] == 'root':
                self.vm['root_password'] = user['password']
            else:
                self.vm['username'] = user['username']
                self.vm['password'] = user['password']

    def set_users_menu(self):
        self.env_account_set_list.select_account_set_list_index()
        self.user_list = self.env_account_set_list.get_current_index_account_set_as_user_list()
        self.set_users()

    def get_menu_entry(self):
        return [f'Account({self.env_account_set_list.format_account_set(self.env_account_set_list.get_current_index_account_set())})', self.set_users_menu]

class VmResource:
    def __init__(self, vm):
        self.vm = vm
        self.resource_list = [
            {'vcpu': 2, 'vmem': 2048}
            , {'vcpu': 2, 'vmem': 4096}
            , {'vcpu': 4, 'vmem': 4096}
            , {'vcpu': 4, 'vmem': 8192}
        ]
        self.resource = {
            'vcpu': 2,
            'vmem': 2048,
        }
        self.set_resource()

    def format_resource(self, resource):
        return f'vcpu:{resource["vcpu"]} vmem:{resource["vmem"]}'

    def get_format_resource(self):
        return self.format_resource(self.resource)

    def set_resource(self):
        self.vm['vcpu'] = self.resource['vcpu']
        self.vm['vmem'] = self.resource['vmem']

    def set_resource_menu(self):
        num = choose_num([self.format_resource(res) for res in self.resource_list])
        self.resource = self.resource_list[num]
        self.set_resource()

    def get_menu_entry(self):
        return [f'Resource({light_red(self.get_format_resource())})', self.set_resource_menu]

def set_hostname_and_waitprompt(node_dict):
    if 'hostname' in node_dict:
        hostname = node_dict['hostname']
    else:
        hostname = 'localhost'
    hostname = get_input('^[a-z][a-z0-9_]{2,30}$', f'Hostname (Default: {hostname}): ', 'Invalid Hostname', hostname)
    node_dict['hostname'] = hostname
    return node_dict

def create_bash_params(node_dict):
    node_dict = set_hostname_and_waitprompt(node_dict)
    node_dict['login_method'] = 'bash'
    return node_dict

def create_virsh_console_params(node_dict):
    node_dict = set_hostname_and_waitprompt(node_dict)
    node_dict['login_method'] = 'virsh console'
    return node_dict

def create_ssh_params(node_dict):
    node_dict = set_hostname_and_waitprompt(node_dict)
    node_dict['login_method'] = 'ssh'
    if 'access_ip' in node_dict:
        access_ip = node_dict['access_ip']
    else:
        access_ip = '127.0.0.1'
    node_dict['access_ip'] = get_input('^' + misc.IPV4_EXP_STR + '$', f'IP (Default: {access_ip}): ', 'Invalid IP', access_ip)
    node_dict['ssh_options' ]= '-o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null'
    return node_dict

def create_create_vm_params(node_dict):
    node_dict = set_hostname_and_waitprompt(node_dict)
    size = int(get_input(r'\d+', 'Disk Size (Default: %d(G)): ' % node_dict['size'], 'invalid format', node_dict['size']))
    node_dict['size'] = size
    username = node_dict['username']
    hostname = node_dict['hostname']
    platform = node_dict['platform']
    if platform == 'centos7':
        partition = ['/dev/vda', 1]
    elif re.search('^ubuntu', platform):
        partition = ['/dev/vda', 1]
    else:
        partition = ['/dev/vda', 2]
    node_dict = new_node.create_single_iface_node_dict(hostname, None, misc.concat_dict([
        node_dict,
        {
            'prepare_vdisk': {
                'type': 'cloud_image',
                'size': size,
                'partition': partition
            },
        }
    ]), login_user=username)
    node_dict['login_method'] = 'create vm'
    return node_dict

class VmConnect:
    def __init__(self, initial_node_dict, connect_method_list):
        self.initial_node_dict = initial_node_dict
        if connect_method_list:
            self.connect_method_list = connect_method_list
        else:
            self.connect_method_list = [
                'ssh'
                , 'bash'
                , 'virsh console'
                , 'create vm'
            ]
        self.node_dict = None
        self.selected_con = None
        # self.select_con_menu()

    def get_format_con(self):
        if not self.selected_con:
            return light_red('not selected yet.')
        hostname = self.node_dict['hostname']
        if self.selected_con == 'ssh':
            access_ip = self.node_dict['access_ip']
            return f'{self.selected_con}(hostname:{hostname} access_ip:{access_ip})'
        if self.selected_con in ['bash', 'virsh console']:
            return f'{self.selected_con}(hostname:{hostname})'
        if self.selected_con == 'create vm':
            size = self.node_dict['size']
            access_ip = self.node_dict['access_ip']
            return f'{self.selected_con}(hostname:{hostname} access_ip:{access_ip}  size:{size}G)'
        return red('something wrong in VmConnect')

    def select_con_menu(self):
        num = choose_num(self.connect_method_list)
        selected = self.connect_method_list[num]
        self.selected_con = selected
        if selected == 'ssh':
            self.node_dict = create_ssh_params(self.initial_node_dict)
        elif selected == 'bash':
            self.node_dict = create_bash_params(self.initial_node_dict)
        elif selected == 'virsh console':
            self.node_dict = create_virsh_console_params(self.initial_node_dict)
        elif selected == 'create vm':
            self.node_dict = create_create_vm_params(self.initial_node_dict)
        else:
            print(red(f'no such connect_method: {selected}'))

    def get_menu_entry(self):
        return [f'Connect Method({self.get_format_con()})', self.select_con_menu]

def select_post_run(vm, instance_list, connect_method_list, hostname=None):
    tmp_vm = {}
    vm_resource = VmResource(tmp_vm)
    vm_account = VmAccount(tmp_vm)
    vm_connect = VmConnect(misc.concat_dict([vm, tmp_vm]), connect_method_list)
    while True:
        if hostname:
            menu_list = [
                vm_resource.get_menu_entry()
                , vm_account.get_menu_entry()
            ]
        else:
            menu_list = [
                vm_resource.get_menu_entry()
                , vm_account.get_menu_entry()
                , vm_connect.get_menu_entry()
            ]
        menu_list += [instance.menu_entry() for instance in instance_list]
        if vm_connect.node_dict or hostname:
            menu_list += [['Next']]

        num = choose_num([m[0] for m in menu_list], 'Select menu', vertical=True)
        if menu_list[num][0] == 'Next':
            if hostname:
                vm = misc.concat_dict([
                    vm,
                    tmp_vm
                ])
            else:
                vm = misc.concat_dict([
                    vm,
                    vm_connect.node_dict,
                    tmp_vm,
                ])
            vm['waitprompt'] = base_node.get_linux_waitprompt(vm['platform'], vm['hostname'], username=vm['username'])
            break
        menu_list[num][1]()
    return vm
