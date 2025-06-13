from mini.menu import *
from mini.misc import concat_dict, toml
from plur import base_node
from plur import session_wrap
from plur import log_param_templates
from plur_linux.recipes.kvm import virsh
from plur_linux.recipes.kvm.kvm_menu import lib_kvm_module
from plur_linux.nodes import new_node
from plur_linux.recipes.kvm.kvm_menu import runner


bash_target_definition_toml_str = """
[hostname]
type = 'string'
message = 'Input Hostname'
exp = '[a-z][a-z0-9_]{2,30}'
"""
ssh_target_definition_toml_str = bash_target_definition_toml_str + r"""
[access_ip]
type = 'string'
message = 'Input SSH Access IP'
exp = '\d{1,3}(\.\d{1,3}){3}'
"""
on_kvm_target_definition_toml_str = bash_target_definition_toml_str + r"""
[access_ip]
type = 'string'
message = 'Input SSH Access IP'
exp = '\d{1,3}(\.\d{1,3}){3}'
"""


class VmImplTarget:
    def __init__(self, vm):
        self.selected_num = 0
        self.vm = vm
        self.impl_target = {
            'access_ip': '127.0.0.1',
        }
        self.impl_type = None

    def set_target(self, target, impl_type):
        for k in target:
            self.vm[k] = target[k]
            self.impl_target[k] = target[k]
        self.impl_type = impl_type

    def set_target_menu(self):
        while True:
            menu_list = [
                'ssh',
                'virsh console',
                'create new vm on kvm',
                'Back'
            ]
            num = choose_num(menu_list)
            self.selected_num = num
            if num == 0:
                target = get_obj_by_definition(toml.loads(ssh_target_definition_toml_str), self.impl_target)
                if target:
                    self.set_target(target, 'ssh')
                break
            elif num == len(menu_list)-1:
                break
            else:
                break

    def format_target(self):
        impl_type = self.impl_type
        if impl_type == 'ssh':
            hostname = self.impl_target['hostname']
            access_ip = self.impl_target['access_ip']
            return f'type:ssh hostname:{hostname} access_ip:{access_ip}'
        else:
            return f'type:{red("not selected.")}'

    def get_menu_entry(self):
        return [f'Impl({self.format_target()})', self.set_target_menu]

    def run(self, func):
        username = self.vm['username']
        hostname = self.vm['hostname']
        self.vm['waitprompt'] = rf'\[?{username}@{hostname}.+[$#] '
        impl_type = self.impl_type
        if impl_type == 'ssh':
            vm = base_node.Node(self.vm)
            session_wrap.ssh(vm, log_params=log_param_templates.normal())(func)()


class Account:
    def __init__(self, vm):
        self.vm = vm
        self.vm_impl_target = VmImplTarget(vm)

    def run_menu(self, instance_list):
        def func(session):
            for instance in instance_list:
                instance.setup(session)

        while True:
            menu_list = [
                ['run']
                , ['spawn_and_set']
                , self.vm_impl_target.get_menu_entry()
            ]
            num = choose_num([m[0] for m in menu_list], 'Select menu', vertical=True)
            if num == 0:
                if not self.vm_impl_target.impl_type:
                    print(yellow('Please set Implement Target'))
                else:
                    self.vm_impl_target.run(func)
                    break
            elif num == 1:
                self.spawn_and_set(func)
                break
            else:
                menu_list[num][1]()

    def spawn_and_set(self, run_post):
        num = choose_num([
            'ssh',
            'virsh console',
            'create new vm on kvm',
            'create new vm on kvm by libguestfs',
        ], 'Please choose login method: ', vertical=True)
        hostname = get_input(r'[a-z][a-z0-9_]{0,30}', 'vm(default:%s):' % self.vm['hostname'], 'Invalid name', self.vm['hostname'])
        self.vm['hostname'] = hostname
        username = self.vm['username']

        if num == 0:
            default_access_ip = '127.0.0.1'
            self.vm['access_ip'] = get_input(r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}', f'IP (Default: {default_access_ip}): ', 'Invalid IP', default_access_ip)
            self.vm['waitprompt'] = rf'\[?{username}@{hostname}.+[$#] '
            if get_y_n('Do you want to run '):
                vm = base_node.Node(self.vm)
                session_wrap.ssh(vm, log_params=log_param_templates.normal())(run_post)()
        elif num == 1:
            self.vm['waitprompt'] = rf'\[?{username}@{hostname}.+[$#] '
            kvm = lib_kvm_module.select_kvm()
            if get_y_n('Do you want to run '):
                vm = base_node.Node(self.vm)
                if kvm:
                    session_wrap.ssh(kvm, log_params=log_param_templates.normal())(virsh.console(vm)(run_post))()
                else:
                    session_wrap.bash(log_params=log_param_templates.normal())(virsh.console(vm)(run_post))()
        elif num in [2, 3]:
            self.vm['size'] = int(get_input(r'\d+', 'Disk Size (Default: %d(G)): ' % self.vm['size'], 'invalid format', self.vm['size']))
            platform = self.vm['platform']
            if platform == 'centos7':
                partition = ['/dev/vda', 1]
            elif re.search('^ubuntu', platform):
                partition = ['/dev/vda', 1]
            else:
                partition = ['/dev/vda', 2]
            vm_dict = new_node.create_single_iface_node_dict(hostname, None, concat_dict([
                self.vm,
                {
                    'prepare_vdisk': {
                        'type': 'cloud_image',
                        'size': self.vm['size'],
                        'partition': partition
                    },
                }
            ]), login_user=username)
            vm_dict['setups'] = {
                'run_post': run_post
            }
            kvm = lib_kvm_module.select_kvm()
            if get_y_n('Do you want to run '):
                if num == 3:
                    runner.create_vm_dict_on(kvm, vm_dict, by_libguestfs=True)
                else:
                    runner.create_vm_dict_on(kvm, vm_dict)
