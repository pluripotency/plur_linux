#! /usr/bin/env python
import os
import json
from mini.ansi_colors import red, yellow, green, cyan, dummy_color
from mini import menu
from mini.misc import is_file, read_json, read_toml, write_toml, toml, prepare_dir_if_not_exists
ACCOUNT_SET_LIST_KEY = 'account_set'
SELECTED_ACCOUNT_SET_INDEX_KEY = 'selected_account_set_index'
ACCOUNT_SET_DEFINITION_TOML_STR = r"""
[username]
type = 'string'
message = 'Input Username'
exp = '\w.'
[password]
message = 'Input Password'
type = 'string'
[sudoers]
type = 'bool'
[root_password]
type = 'string'
message = 'Input Root Password'
"""
default_account_set = {
    'username': 'worker',
    'password': 'p@ssw0rd!',
    'sudoers': True,
    'root_password': 'p@ssw0rd!',
}

SEGMENTS_KEY = 'segments'
SEGMENT_DEFINITION_TOML_STR = r"""
[type]
type = 'string'
message = 'Network type(ex. openvswitch|default|direct|bridge|macvtap)'
exp = 'openvswitch|default|direct|bridge|macvtap'
[net_source]
type = 'string'
message = 'net_source(ex. br0|default)'
[ip_base_prefix]
type = 'string'
message = 'Input ip segment(ex. 192.168.0)'
exp = '\d{1,3}(\.\d{1,3}){0,2}'
[prefix]
type = 'string'
message = 'Input prefix(ex. 24)'
exp = '\d{1,2}'
[gateway_seed]
type = 'string'
message = 'Input gateway seed(ex. 254)'
exp = '\d{1,3}'
[search]
type = 'string'
message = 'Input Search Domain(ex. dom.local)'
[nameservers]
type = 'string'
message = 'Input nameservers seperate by comma'
"""
default_segment = {
    'type': 'default',
    'net_source': 'default',
    'ip_base_prefix': '192.168.122',
    'prefix': '24',
    'gateway_seed': '1',
    'search': 'local',
    'nameservers': '192.168.122.1',
}

KVM_LIST_KEY = 'kvm_list'
KVM_DEFINITION_TOML_STR = r"""
[hostname]
type = 'string'
message = 'hostname'
exp = '\w+'
[username]
type = 'string'
message = 'hostname'
exp = '\w+'
[password]
type = 'string'
message = 'password'
exp = '\w+'
[platform]
type = 'string'
message = 'platform'
exp = '\w+'
[access_ip]
type = 'string'
message = 'access_ip'
exp = '\d{1,3}(\.\d{1,3}){3}'
"""
default_kvm = {
    'hostname': 'myhost',
    'username': 'worker',
    'password': 'p@ssw0rd!',
    'platform': 'almalinux9',
    'access_ip': '127.0.0.1',
}
# USER_LIST_GROUP_KEY = 'user_list_group'
# SELECTED_USER_LIST_GROUP_INDEX_KEY = 'selected_user_list_group_index'
#
# USER_DEFINITION_TOML_STR = r"""
# [username]
# type = 'string'
# message = 'Input Username'
# exp = '\w.'
# [password]
# message = 'Input Password'
# type = 'string'
# [sudoers]
# type = 'bool'
# [sudoers.skip_on]
# username = 'root'
# """
# default_user = {
#     'username': 'worker',
#     'password': 'p@ssw0rd!',
#     'sudoers': True
# }
# default_user_list = [
#     default_user,
#     {
#         'username': 'root',
#         'password': 'p@ssw0rd!'
#     }
# ]
def show_json(data, color=dummy_color):
    print(color(json.dumps(data, indent=2)))


def show_toml(data, color=dummy_color):
    print(color(toml.dumps(data)))


class EnvOpsBase:
    def __init__(self):
        env_dir_path = os.getenv('PLUR_ENV_DIR')
        if not env_dir_path:
            env_dir_path = os.path.expanduser('~/.plur')
        self.env_json_file_path = os.path.expanduser(f'{env_dir_path}/env.json')
        self.env_toml_file_path = os.path.expanduser(f'{env_dir_path}/env.toml')
        env_dict = None
        if is_file(self.env_toml_file_path):
            env_dict = read_toml(self.env_toml_file_path)
        elif is_file(self.env_json_file_path):
            env_dict = read_json(self.env_json_file_path)
        if isinstance(env_dict, dict):
            self.env_dict = env_dict
        else:
            prepare_dir_if_not_exists(env_dir_path)
            self.env_dict = {}

    def create_table(self, dict_list):
        header = dict_list[0].keys()
        space_num_list = [len(key) for key in header]
        value_table = []
        for item in dict_list:
            value_list = []
            for index, key in enumerate(header):
                str_value = str(item[key])
                cur_space = space_num_list[index]
                item_space = len(str_value)
                if cur_space < item_space:
                    space_num_list[index] = item_space
                value_list += [str_value]
            value_table += [value_list]

        header_col_list = []
        for index, col in enumerate(header):
            space_num = space_num_list[index]
            header_col_list +=  [yellow(col) + ' ' * (space_num - len(col))]
        header_line = yellow(' | ').join(header_col_list)

        table_body = []
        for value_list in value_table:
            spaced_list = []
            for index, col in enumerate(value_list):
                space_num = space_num_list[index]
                spaced_list +=  [col + ' ' * (space_num - len(col))]
            table_body += [yellow(' | ').join(spaced_list)]
        return table_body, header_line

    def create_menu_table(self, dict_list, message=cyan('Please Select Number')):
        table_body, header_line = self.create_table(dict_list)
        header_with_message = f'{message}\n   ' + header_line
        return table_body, header_with_message

    def write(self):
        # write_json(self.env_json_file_path, self.env_dict)
        write_toml(self.env_toml_file_path, self.env_dict)

    def show(self):
        # show_json(self.env_dict, cyan)
        show_toml(self.env_dict, cyan)

    def get(self, key):
        return self.env_dict[key]

    def set(self, key, value):
        self.env_dict[key] = value
        self.write()
        return True


class EnvAccountSet():
    def __init__(self, env_ops=None):
        if isinstance(env_ops, EnvOpsBase):
            self.env_ops = env_ops
        else:
            self.env_ops = EnvOpsBase()
        self.title = 'Account Set'
        self.env_dict = self.env_ops.env_dict
        self.get = self.env_ops.get
        self.set = self.env_ops.set
        self.set_default()
        self.env_ops.write()
        self.account_set_definition = toml.loads(ACCOUNT_SET_DEFINITION_TOML_STR)

    def set_default(self):
        if not ACCOUNT_SET_LIST_KEY in self.env_dict:
            self.env_dict[ACCOUNT_SET_LIST_KEY] = [default_account_set]
        if not SELECTED_ACCOUNT_SET_INDEX_KEY in self.env_dict:
            self.env_dict[SELECTED_ACCOUNT_SET_INDEX_KEY] = 0

    def format_account_set(self, account_set):
        username = account_set["username"]
        password = account_set["password"]
        sudoers = account_set["sudoers"]
        root_password = account_set["root_password"]
        return green(f'{username}:{password}(sudoers: {sudoers}) root:{root_password}')

    def create_table(self):
        return self.env_ops.create_table(self.get_account_set_list())

    def create_menu_table(self, message=cyan('Please Select Number')):
        return self.env_ops.create_menu_table(self.get_account_set_list(), message)

    def show_account_set(self, account_set):
        show_toml(account_set, cyan)

    def get_account_set_list(self):
        return self.get(ACCOUNT_SET_LIST_KEY)

    def get_current_index(self):
        return self.get(SELECTED_ACCOUNT_SET_INDEX_KEY)

    def get_current_index_account_set(self):
        return self.get_account_set_list()[self.get_current_index()]

    def get_current_index_account_set_as_user_list(self):
        current_account_set = self.get_current_index_account_set()
        return [
            {
                'username': current_account_set['username'],
                'password': current_account_set['password'],
                'sudoers': current_account_set['sudoers'],
            },
            {
                'username': 'root',
                'password': current_account_set['root_password'],
            }
        ]

    def add_account_set(self):
        account_set  = menu.get_obj_by_definition(self.account_set_definition, default_account_set)
        if account_set:
            current_account_set_list = self.get_account_set_list()
            current_account_set_list += [account_set]
            self.set(ACCOUNT_SET_LIST_KEY, current_account_set_list)

    def set_account_set(self, index):
        current_account_set_list = self.get_account_set_list()
        target_account_set = current_account_set_list[index]
        account_set  = menu.get_obj_by_definition(self.account_set_definition, target_account_set)
        if account_set:
            current_account_set_list[index] = account_set
            self.set(ACCOUNT_SET_LIST_KEY, current_account_set_list)

    def select_account_set_list_index(self):
        menu_list, header_with_message = self.create_menu_table(cyan('Select account set index'))
        num = menu.choose_num(menu_list, header_with_message, color=dummy_color)
        self.set(SELECTED_ACCOUNT_SET_INDEX_KEY, num)

    def delete_account_set(self):
        current_account_set_list = self.get_account_set_list()
        if len(current_account_set_list) < 2:
            print(yellow('last account_set can not be deleted.'))
            return
        menu_list, header_with_message = self.create_menu_table(red('Select delete account set index'))
        num = menu.choose_num(menu_list + ['Back'], header_with_message, color=dummy_color)
        if num < len(menu_list):
            self.show_account_set(current_account_set_list[num])
            if menu.get_y_n(red('Do you really want to DELETE?')):
                del current_account_set_list[num]
                self.set(ACCOUNT_SET_LIST_KEY, current_account_set_list)
                cur_index = self.get_current_index()
                if num == cur_index:
                    print(yellow('you must select new default account_set'))
                    self.select_account_set_list_index()
                elif num < cur_index:
                    self.set(SELECTED_ACCOUNT_SET_INDEX_KEY, cur_index-1)

    def account_set_list_menu(self):
        while True:
            current_index = self.get_current_index()
            menu_list, header_with_message = self.create_menu_table(cyan('Select Account Set Menu'))
            menu_list += [
                green('Add account set'),
                red('Delete account set'),
                green(f'Select index(current: {current_index + 1})'),
                'Back']
            num = menu.choose_num(menu_list, message=header_with_message, color=dummy_color)
            if num == len(menu_list)-4:
                # Add
                self.add_account_set()
            elif num == len(menu_list) - 3:
                # Delete
                self.delete_account_set()
            elif num == len(menu_list)-2:
                # Select
                self.select_account_set_list_index()
            elif num == len(menu_list)-1:
                break
            else:
                self.set_account_set(num)


# class EnvUserList():
#     def __init__(self, env_ops=None):
#         if isinstance(env_ops, EnvOpsBase):
#             self.env_ops = env_ops
#         else:
#             self.env_ops = EnvOpsBase()
#         self.env_dict = self.env_ops.env_dict
#         self.get = self.env_ops.get
#         self.set = self.env_ops.set
#         self.set_default()
#         self.env_ops.write()
#         self.user_input_definition = toml.loads(USER_DEFINITION_TOML_STR)
#
#     def set_default(self):
#         if not USER_LIST_GROUP_KEY in self.env_dict:
#             self.env_dict[USER_LIST_GROUP_KEY] = [default_user_list]
#         if not SELECTED_ACCOUNT_SET_INDEX_KEY in self.env_dict:
#             self.env_dict[SELECTED_USER_LIST_GROUP_INDEX_KEY] = 0
#
#     def format_user(self, user):
#         if user['username'] == 'root':
#             return f'{user["username"]}: {user["password"]}  '
#         sudoers = False
#         if 'sudoers' in user and user['sudoers']:
#             sudoers = True
#         return f'{user["username"]}(sudoers: {sudoers}): {user["password"]}  '
#
#     def format_user_list(self, user_list):
#         msg = ''
#         for user in user_list:
#             msg += self.format_user(user)
#         return msg
#
#     def show_user(self, user):
#         show_json(user, cyan)
#
#     def show_user_list(self, user_list):
#         for user in user_list:
#             self.show_user(user)
#
#     def show_current_user_list(self):
#         self.show_user_list(self.get_current_index_user_list())
#
#     def get_user_list_group(self):
#         return self.get(USER_LIST_GROUP_KEY)
#
#     def get_current_index(self):
#         return self.get(SELECTED_USER_LIST_GROUP_INDEX_KEY)
#
#     def get_current_index_user_list(self):
#         return self.get_user_list_group()[self.get_current_index()]
#
#     def add_user(self, group_index):
#         user = menu.get_obj_by_definition(self.user_input_definition, default_user)
#         if user:
#             self.set_user_list(user, group_index)
#
#     def set_user(self, index, group_index):
#         cur_user = self.get_user_list_group()[group_index][index]
#         user = menu.get_obj_by_definition(self.user_input_definition, cur_user)
#         if user:
#             self.set_user_list(user, group_index, index)
#
#     def set_user_list(self, user, group_index, set_index=False):
#         if user:
#             current_user_list_group = self.get_user_list_group()
#             if isinstance(set_index, int):
#                 current_user_list_group[group_index][set_index] = user
#             else:
#                 current_user_list_group[group_index] += [user]
#             self.set(USER_LIST_GROUP_KEY, current_user_list_group)
#
#     def set_users_menu(self, user_list, group_index):
#         current_user_list_group = self.get_user_list_group()
#         if group_index == len(current_user_list_group):
#             current_user_list_group += [user_list]
#             self.set(USER_LIST_GROUP_KEY, current_user_list_group)
#
#         while True:
#             print(self.format_user_list(user_list))
#             menu_list = [f'{user["username"]}: {user["password"]}' for user in user_list] + \
#                         ['Add user', 'Back']
#             num = menu.choose_num(menu_list)
#             if num == len(menu_list)-2:
#                 self.add_user(group_index)
#             elif num == len(menu_list)-1:
#                 break
#             else:
#                 self.set_user(num, group_index)
#
#     def select_user_list_group_index(self, user_list_group):
#         menu_list = [self.format_user_list(user_list) for user_list in user_list_group] + ['Back']
#         num = menu.choose_num(menu_list, 'select default user list group')
#         if num < len(menu_list):
#             self.set(SELECTED_USER_LIST_GROUP_INDEX_KEY, num)
#
#     def delete_user_list_group(self, user_list_group):
#         menu_list = [self.format_user_list(user_list) for user_list in user_list_group] + ['Back']
#         num = menu.choose_num(menu_list, red('Delete user list group index'))
#         if num < len(menu_list):
#             current_user_list_group = self.get_user_list_group()
#             self.show_user_list(current_user_list_group[num])
#             if menu.get_y_n(red('Do you really want to DELETE?')):
#                 del current_user_list_group[num]
#                 self.set(USER_LIST_GROUP_KEY, current_user_list_group)
#
#     def user_list_group_menu(self):
#         user_list_group = self.get_user_list_group()
#         _ = [print(self.format_user_list(user_list)) for user_list in user_list_group]
#         while True:
#             current_index = self.get_current_index()
#             menu_list = [self.format_user_list(user_list) for user_list in user_list_group] + \
#                         ['Add user list group', red('Delete user list group'),
#                             f'Select default index(current: {current_index + 1})', 'Back']
#             num = menu.choose_num(menu_list)
#             if num == len(menu_list)-4:
#                 self.set_users_menu(default_user_list, len(user_list_group))
#             elif num == len(menu_list) - 3:
#                 self.delete_user_list_group(user_list_group)
#             elif num == len(menu_list)-2:
#                 self.select_user_list_group_index(user_list_group)
#             elif num == len(menu_list)-1:
#                 break
#             else:
#                 user_list = user_list_group[num]
#                 self.set_users_menu(user_list, num)


class EnvKVM():
    def __init__(self, env_ops=None):
        if isinstance(env_ops, EnvOpsBase):
            self.env_ops = env_ops
        else:
            self.env_ops = EnvOpsBase()
        self.title = 'KVM dict'
        self.env_dict = self.env_ops.env_dict
        self.get = self.env_ops.get
        self.set = self.env_ops.set
        self.set_default()
        self.env_ops.write()
        self.kvm_definition = toml.loads(KVM_DEFINITION_TOML_STR)

    def set_default(self):
        if not KVM_LIST_KEY in self.env_dict:
            self.env_dict[KVM_LIST_KEY] = [default_kvm]

    def create_table(self):
        return self.env_ops.create_table(self.get_kvm_list())

    def create_menu_table(self, message=cyan('Please Select Number')):
        return self.env_ops.create_menu_table(self.get_kvm_list(), message)

    def show_kvm(self, kvm_dict):
        show_toml(kvm_dict, cyan)

    def get_kvm_list(self):
        return self.get(KVM_LIST_KEY)

    def add_kvm(self):
        kvm_dict = menu.get_obj_by_definition(self.kvm_definition, default_kvm)
        if kvm_dict:
            current_kvm_list = self.get_kvm_list()
            current_kvm_list += [kvm_dict]
            self.set(KVM_LIST_KEY, current_kvm_list)

    def set_kvm(self, index):
        current_kvm_list = self.get_kvm_list()
        target_kvm_dict = current_kvm_list[index]
        kvm_dict = menu.get_obj_by_definition(self.kvm_definition, target_kvm_dict)
        if kvm_dict:
            current_kvm_list[index] = kvm_dict
            self.set(KVM_LIST_KEY, current_kvm_list)

    def delete_kvm(self):
        current_kvm_list = self.get_kvm_list()
        if len(current_kvm_list) < 2:
            print(yellow('last kvm can not be deleted.'))
            return
        menu_list, header_with_message = self.create_menu_table(red('Select delete account set index'))
        num = menu.choose_num(menu_list + ['Back'], header_with_message, color=dummy_color)
        if num < len(menu_list):
            self.show_kvm(current_kvm_list[num])
            if menu.get_y_n(red('Do you really want to DELETE?')):
                del current_kvm_list[num]
                self.set(KVM_LIST_KEY, current_kvm_list)

    def kvm_list_menu(self):
        while True:
            menu_list, header_with_message = self.create_menu_table(cyan('Select KVM Menu'))
            num = menu.choose_num(menu_list + [
                green('Add kvm'),
                red('Delete kvm'),
                'Back'
            ], message=header_with_message, color=dummy_color)
            if num == len(menu_list):
                # Add
                self.add_kvm()
            elif num == len(menu_list) + 1:
                # Delete
                self.delete_kvm()
            elif num == len(menu_list) + 2:
                break
            else:
                self.set_kvm(num)


class EnvSegments():
    def __init__(self, env_ops=None):
        if isinstance(env_ops, EnvOpsBase):
            self.env_ops = env_ops
        else:
            self.env_ops = EnvOpsBase()
        self.title = 'KVM Segments'
        self.env_dict = self.env_ops.env_dict
        self.get = self.env_ops.get
        self.set = self.env_ops.set
        self.set_default()
        self.env_ops.write()
        self.segment_definition = toml.loads(SEGMENT_DEFINITION_TOML_STR)

    def set_default(self):
        if not SEGMENTS_KEY in self.env_dict:
            self.env_dict[SEGMENTS_KEY] = [default_segment]

    def create_table(self):
        return self.env_ops.create_table(self.get_segment_list())

    def create_menu_table(self, message=cyan('Please Select Number')):
        return self.env_ops.create_menu_table(self.get_segment_list(), message)

    def get_segment_list(self):
        return self.get(SEGMENTS_KEY)

    def set_segment(self, index):
        segments = []
        cur_segment = default_segment
        if 'segments' in self.env_dict:
            segments = self.env_dict['segments']
            if index < len(segments):
                cur_segment = segments[index]
        tmp_segment = menu.get_obj_by_definition(self.segment_definition, cur_segment)
        if tmp_segment:
            current_segments = self.get(SEGMENTS_KEY)
            if len(segments) == index:
                current_segments += [tmp_segment]
            else:
                current_segments[index] = tmp_segment
            self.set(SEGMENTS_KEY, current_segments)

    def format_segment_list(self, segments):
        return [f"{s['ip_base_prefix']}.0/{s['prefix']} {s['net_source']}(type: {s['type']})" for s in segments]

    def segments_menu(self):
        while True:
            segments = self.get(SEGMENTS_KEY)
            menu_list = ['Add network']
            menu_list += self.format_segment_list(segments)
            menu_list += [red('Delete segment'), 'Back']
            num = menu.choose_num(menu_list)
            if num == 0:
                self.set_segment(len(segments))
            elif num == len(menu_list) - 2:
                self.delete_segment(segments)
            elif num == len(menu_list)-1:
                break
            else:
                self.set_segment(num-1)

    def delete_segment(self, segments):
        while True:
            menu_list = self.format_segment_list(segments) + ['Back']
            num = menu.choose_num(menu_list, red('Delete segment index'))
            if num == len(menu_list) - 1:
                break
            else:
                cur_segments = self.get(SEGMENTS_KEY)
                print(cyan(self.format_segment_list([cur_segments[num]])[0]))
                if menu.get_y_n(red('Do you really want to DELETE?')):
                    del cur_segments[num]
                    self.set(SEGMENTS_KEY, cur_segments)
                break

    def bind_env(self, org_env):
        bound_env = {}
        if 'ifaces' in org_env and 'vnets' in org_env:
            if 'segments' in self.env_dict:
                ifaces = []
                vnets = []
                for i, iface in enumerate(org_env['ifaces']):
                    vnet = org_env['vnets'][i]
                    if 'ip_seed' in iface:
                        menu_item = []
                        for s in self.env_dict['segments']:
                            ip_base_prefix = s['ip_base_prefix']
                            prefix = s['prefix']
                            net_source = s['net_source']
                            net_type = s['type']
                            menu_item += [
                                ip_base_prefix + '.{0}/' + f'{prefix} {net_source}(type: {net_type})'
                            ]

                        num = menu.choose_num(menu_item)
                        segment = self.env_dict['segments'][num]
                        if iface['ip_seed'] == 'dhcp':
                            iface['ip'] = 'dhcp'
                        else:
                            iface['ip'] = segment['ip_base_prefix'] + f".{iface['ip_seed']}/{segment['prefix']}"
                            iface['gateway'] = segment['ip_base_prefix'] + '.' + segment['gateway_seed']
                            iface['search'] = segment['search']
                            iface['nameservers'] = segment['nameservers'].split(',')
                            iface['segment'] = segment
                        vnet['type'] = segment['type']
                        vnet['net_source'] = segment['net_source']
                    if 'bridge' in vnet:
                        vnet['net_source'] = vnet['bridge']
                    ifaces.append(iface)
                    vnets.append(vnet)
                bound_env['ifaces'] = ifaces
                bound_env['vnets'] = vnets

        return bound_env


class EnvMenu:
    def __init__(self):
        self.env_ops = EnvOpsBase()
        self.env_account_set = EnvAccountSet(self.env_ops)
        # self.env_user_list = EnvUserList(self.env_ops)
        self.env_segments = EnvSegments(self.env_ops)
        self.env_kvm = EnvKVM(self.env_ops)

    def show(self):
        for attr in [self.env_account_set, self.env_kvm, self.env_segments]:
            table_body, header_line = attr.create_table()
            print(green(attr.title))
            print(header_line)
            for line in table_body:
                print(line)

    def run_menu(self):
        while True:
            menu.select_2nd([
                ['Show Current Env', self.show],
                ['Account Set', self.env_account_set.account_set_list_menu],
                # ['User List Group', self.env_user_list.user_list_group_menu],
                ['Set KVM segments', self.env_segments.segments_menu],
                ['Set KVM', self.env_kvm.kvm_list_menu],
            ])

def get_current_index_user_list():
    return EnvAccountSet().get_current_index_account_set_as_user_list()

def get_kvm_entry_list():
    kvm_entry_list = []
    for kvm_dict in EnvKVM().get_kvm_list():
        hostname = kvm_dict['hostname']
        access_ip = kvm_dict['access_ip']
        platform = kvm_dict['platform']
        kvm_entry_list += [[f'{hostname}({platform}):{access_ip}', kvm_dict]]
    return kvm_entry_list

def get_env_password(username):
    user_list = EnvAccountSet().get_current_index_account_set_as_user_list()
    env_password = ''
    for user in user_list:
        if user['username'] == username:
            env_password = user['password']
    return env_password
