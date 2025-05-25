import json
import sys
import re
from termios import tcflush, TCIFLUSH
import toml
from mini.ansi_colors import red, green, brown, blue, purple, cyan, white, light_red, light_green, yellow, light_blue, pink, light_cyan
from mini.menu import get_input, get_y_n
from mini import misc

ex_user_definition = {
    'username': {
        'type': 'string',
    },
    'password': {
        'type': 'string',
        'exp': r'\w.'
    },
    'sudoers': {
        'type': 'bool',
        'skip_on': {
            'username': 'root'
        }
    },

}
ex_default_user = {
    'username': 'worker',
    'password': 'password',
    'sudoers': True
}


def get_obj_by_definition(input_definition, default_values, color=cyan):
    """
    ex) input_definition: ex_user_definition
    ex) default_values: ex_default_user
    """
    obj = {}
    for k, v in input_definition.items():
        if 'type' in v:
            v_type = v['type']
            if 'skip_on' in v:
                skip = False
                for sk, sv in v['skip_on'].items():
                    if obj[sk] == sv:
                        print(obj, sk, sv)
                        skip = True
                if skip:
                    continue
            message = k
            if 'message' in v:
                message = v['message']
            if v_type == 'string':
                exp = r'\w.'
                if 'exp' in v:
                    exp = v['exp']
                if k in default_values:
                    default_value = default_values[k]
                    obj[k] = get_input(exp, f'{message}(default={default_value}):', default_value=default_value)
                else:
                    obj[k] = get_input(exp, f'{message}:')
            elif v_type == 'int':
                exp = r'\d+'
                if 'exp' in v:
                    exp = v['exp']
                if k in default_values:
                    default_value = default_values[k]
                    value_str = get_input(exp, f'{message}(default={default_value}):', default_value=default_value)
                else:
                    value_str = get_input(exp, f'{message}:')
                obj[k] = int(value_str)
            elif v_type == 'bool':
                if k in default_values:
                    default_value = default_values[k]
                    obj[k] = get_y_n(f'{message}(default={default_value}):', default=default_value, colored=False)
                else:
                    obj[k] = get_y_n(f'{message}:', colored=False)
    print(color(toml.dumps(obj)))
    if get_y_n('OK?'):
        return obj
    else:
        return None


class Selection:
    def __init__(self, menu_type, output_dir='/tmp/plur_history'):
        if not menu_type:
            self.error('menu_type is needed')
        self.menu_type= misc.sanitize_to_file_name(menu_type)
        self.title = None
        self.selected_list = []

        prepare_result = misc.prepare_dir_if_not_exists(output_dir)
        if not prepare_result:
            self.error(f'couldn\'t prepare dir: {output_dir}')
        self.output_dir = output_dir

    def error(self, err):
        print('error in menu.Selection', err)
        exit(1)

    def append(self, value):
        self.selected_list.append(value)

    def set_title(self, title):
        self.title = misc.sanitize_to_file_name(title)
        print('set selection: menu_type:' + self.menu_type + ' title:' + self.title)

    def input_title(self):
        self.set_title(get_input(message='Selection Name: '))

    def create_file_name(self):
        return self.menu_type + '_' + self.title + '.sel'

    def create_file_path(self):
        return self.output_dir + '/' + self.create_file_name()

    def save(self):
        if not self.title:
            self.input_title()
        misc.open_write(self.create_file_path(), json.dumps(self.selected_list, indent=2), 'w')

    def load(self, title):
        self.set_title(title)
        loaded_json = misc.read_json(self.create_file_path())
        if loaded_json:
            self.selected_list = loaded_json
        else:
            self.error(f'couldn\'t load: {self.create_file_path()}')

