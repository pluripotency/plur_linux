import re
from mini.ansi_colors import red, light_red
from mini.menu import get_input, choose_num
from mini import misc
from plur import base_node
from plur_linux.nodes import new_node

class VmAccount:
    def __init__(self, vm, initial_username=None):
        from plur_linux.lib import env_ops
        self.vm = vm
        self.env_account_set_list = env_ops.EnvAccountSet()
        self.account_index = self._resolve_initial_index(initial_username)
        self.user_list = self._get_account_set_as_user_list(self.account_index)
        self.set_users()

    def _resolve_initial_index(self, initial_username):
        account_sets = self.env_account_set_list.get_account_set_list()
        if initial_username:
            for idx, acc in enumerate(account_sets):
                if acc.get('username') == initial_username:
                    return idx
        cur_idx = self.env_account_set_list.get_current_index()
        if 0 <= cur_idx < len(account_sets):
            return cur_idx
        return 0

    def _get_selected_account_set(self):
        return self.env_account_set_list.get_account_set_list()[self.account_index]

    def _get_account_set_as_user_list(self, index):
        account_set = self.env_account_set_list.get_account_set_list()[index]
        return [
            {
                'username': account_set['username'],
                'password': account_set['password'],
                'sudoers': account_set['sudoers'],
            },
            {
                'username': 'root',
                'password': account_set['root_password'],
            }
        ]

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
        self.account_index = self.env_account_set_list.get_current_index()
        self.user_list = self._get_account_set_as_user_list(self.account_index)
        self.set_users()

    def get_menu_entry(self):
        return [f'Account({self.env_account_set_list.format_account_set(self._get_selected_account_set())})', self.set_users_menu]

class VmResource:
    def __init__(self, vm, initial_resource=None):
        self.vm = vm
        self.resource_list = [
            {'vcpu': 2, 'vmem': 2048}
            , {'vcpu': 2, 'vmem': 4096}
            , {'vcpu': 4, 'vmem': 4096}
            , {'vcpu': 4, 'vmem': 8192}
        ]
        if isinstance(initial_resource, dict) and 'vcpu' in initial_resource and 'vmem' in initial_resource:
            self.resource = {
                'vcpu': int(initial_resource['vcpu']),
                'vmem': int(initial_resource['vmem']),
            }
        else:
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

def set_hostname(node_dict):
    if 'hostname' in node_dict:
        hostname = node_dict['hostname']
    else:
        hostname = 'localhost'
    hostname = get_input(r'^[a-z][a-z0-9_.-]{2,100}$', f'Hostname (Default: {hostname}): ', 'Invalid Hostname', hostname)
    node_dict['hostname'] = hostname
    return node_dict

def create_bash_params(node_dict):
    me = base_node.Me()
    node_dict = me.__dict__
    node_dict['login_method'] = 'bash'
    return node_dict

def create_virsh_console_params(node_dict):
    node_dict = set_hostname(node_dict)
    node_dict['login_method'] = 'virsh console'
    return node_dict

def create_ssh_params(node_dict):
    node_dict = set_hostname(node_dict)
    node_dict['login_method'] = 'ssh'
    default_ip = node_dict.get('access_ip', '')
    if default_ip == node_dict['hostname']:
        default_ip = ''
    prompt = (
        f'IP (Default: {default_ip}, blank to set hostname): '
        if default_ip
        else 'IP (blank to set hostname): '
    )
    tmp_access_ip = get_input('^(|' + misc.IPV4_EXP_STR + ')$', prompt, 'Invalid IP', default_ip)
    if tmp_access_ip == '':
        node_dict['access_ip'] = node_dict['hostname']
    else:
        node_dict['access_ip'] = tmp_access_ip
    node_dict['ssh_options'] = '-o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null'
    return node_dict

def _strip_bound_net_keys(node_dict):
    return {k: v for k, v in node_dict.items() if k not in ('ifaces', 'vnets')}

def create_vm_params(node_dict):
    from plur_linux.recipes.kvm.kvm_menu import lib as kvm_menu_lib
    node_dict = _strip_bound_net_keys(node_dict)
    node_dict = set_hostname(node_dict)
    size = int(get_input(r'^\d+$', 'Disk Size (Default: %d(G)): ' % node_dict['size'], 'invalid format', node_dict['size']))
    node_dict['size'] = size
    username = node_dict['username']
    hostname = node_dict['hostname']
    platform = node_dict['platform']
    if re.search('^ubuntu', platform):
        partition = ['/dev/vda', 1]
    else:
        partition = ['/dev/vda', 2]
    definexml, restart_before_setup = kvm_menu_lib.select_vm_boot_options(node_dict)
    node_dict = new_node.create_single_iface_node_dict(hostname, None, misc.concat_dict([
        node_dict,
        {
            'definexml': definexml,
            'restart_before_setup': restart_before_setup,
            'prepare_vdisk': {
                'type': 'cloud_image',
                'size': size,
                'partition': partition
            },
        }
    ]), login_user=username)
    node_dict['login_method'] = 'create vm'
    return node_dict

def create_vm_by_copy_params(node_dict):
    from plur_linux.recipes.kvm.kvm_menu import lib as kvm_menu_lib
    node_dict = _strip_bound_net_keys(node_dict)
    node_dict = set_hostname(node_dict)
    username = node_dict['username']
    hostname = node_dict['hostname']
    definexml, restart_before_setup = kvm_menu_lib.select_vm_boot_options(node_dict)
    node_dict = new_node.create_single_iface_node_dict(hostname, None, misc.concat_dict([
        node_dict,
        {
            'definexml': definexml,
            'restart_before_setup': restart_before_setup,
        }
    ]), login_user=username)
    node_dict['login_method'] = 'create vm by copy'
    return node_dict

class VmConnect:
    def __init__(self, initial_node_dict, connect_method_list, restored_connect=None):
        self.initial_node_dict = dict(initial_node_dict)
        if connect_method_list:
            self.connect_method_list = connect_method_list
        else:
            self.connect_method_list = [
                'ssh'
                , 'bash'
                , 'virsh console'
                , 'create vm'
                , 'create vm by copy'
            ]
        self.node_dict = None
        self.selected_con = None
        if isinstance(restored_connect, dict):
            from plur_linux.recipes.kvm.adhoc_setup import adhoc_history
            selected_con, restored_dict = adhoc_history.restore_connect_node_dict(
                restored_connect, self.connect_method_list
            )
            if selected_con and restored_dict:
                self.selected_con = selected_con
                self.node_dict = restored_dict
            else:
                for key in ('hostname', 'size', 'restart_before_setup', 'definexml'):
                    if key in restored_connect:
                        self.initial_node_dict[key] = restored_connect[key]

    def _get_vm_mode_label(self):
        from plur_linux.recipes.kvm import spawn

        return spawn.get_vm_boot_mode_label(self.node_dict)

    def get_format_con(self):
        if not self.selected_con:
            return light_red('not selected yet.')
        if self.node_dict and 'hostname' in self.node_dict:
            hostname = self.node_dict['hostname']
            if self.selected_con == 'ssh':
                access_ip = self.node_dict['access_ip']
                return f'{self.selected_con}(hostname:{hostname} access_ip:{access_ip})'
            if self.selected_con in ['bash', 'virsh console']:
                return f'{self.selected_con}(hostname:{hostname})'
            if self.selected_con == 'create vm by copy':
                mode = self._get_vm_mode_label()
                return f'{self.selected_con}(hostname:{hostname} mode:{mode})'
            if self.selected_con == 'create vm':
                size = self.node_dict['size']
                access_ip = self.node_dict['access_ip']
                mode = self._get_vm_mode_label()
                return f'{self.selected_con}(hostname:{hostname} access_ip:{access_ip}  size:{size}G mode:{mode})'
        return red('something wrong in VmConnect')

    def _build_base_node_dict(self):
        base = dict(self.initial_node_dict)
        if isinstance(self.node_dict, dict):
            for key in ('hostname', 'size', 'access_ip', 'restart_before_setup', 'definexml'):
                if key in self.node_dict:
                    base[key] = self.node_dict[key]
        return base

    def select_con_menu(self):
        if len(self.connect_method_list) == 1:
            selected = self.connect_method_list[0]
        else:
            num = choose_num(self.connect_method_list)
            selected = self.connect_method_list[num]
        self.selected_con = selected
        base_dict = self._build_base_node_dict()
        if selected == 'ssh':
            self.node_dict = create_ssh_params(base_dict)
        elif selected == 'bash':
            self.node_dict = create_bash_params(base_dict)
        elif selected == 'virsh console':
            self.node_dict = create_virsh_console_params(base_dict)
        elif selected == 'create vm':
            self.node_dict = create_vm_params(base_dict)
        elif selected == 'create vm by copy':
            self.node_dict = create_vm_by_copy_params(base_dict)
        else:
            print(red(f'no such connect_method: {selected}'))

    def get_menu_entry(self):
        return [f'Connect Method({self.get_format_con()})', self.select_con_menu]

def select_post_run(vm, instance_list, connect_method_list, hostname=None, history_entry=None, os_label=None):
    tmp_vm = {}
    initial_resource = history_entry.get('resource') if isinstance(history_entry, dict) else None
    initial_username = (
        history_entry.get('account', {}).get('username')
        if isinstance(history_entry, dict) and isinstance(history_entry.get('account'), dict)
        else None
    )
    restored_connect = (
        history_entry.get('connect')
        if isinstance(history_entry, dict) and not hostname
        else None
    )
    vm_resource = VmResource(tmp_vm, initial_resource=initial_resource)
    vm_account = VmAccount(tmp_vm, initial_username=initial_username)
    vm_connect = VmConnect(
        misc.concat_dict([vm, tmp_vm]),
        connect_method_list,
        restored_connect=restored_connect,
    )
    menu_message = f'Select menu ({os_label})' if os_label else 'Select menu'
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

        num = choose_num([m[0] for m in menu_list], menu_message, vertical=True)
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
