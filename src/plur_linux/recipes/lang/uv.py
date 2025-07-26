from plur import base_shell

def setup_uv(session):
    if not base_shell.check_command_exists(session, 'uv'):
        base_shell.run(session, 'curl -LsSf https://astral.sh/uv/install.sh | sh')
        # base_shell.run(session, 'echo \'eval "$(uv generate-shell-completion bash)"\' >> ~/.bashrc')
        line = 'eval "$(uv generate-shell-completion bash)"'
        base_shell.append_bashrc(session, line)

def uv_python_install(version):
    def inner(session):
        base_shell.run(session, f'uv python install {version}')
    return inner

def uv_venv(venv_name, venv_dir):
    def inner(session):
        if not base_shell.check_dir_exists(session, venv_dir):
            base_shell.work_on(session, venv_dir)
            base_shell.run(session, f'uv venv {venv_name}')
            line = f'alias {venv_name}=". {venv_dir}/{venv_name}/bin/activate"'
            base_shell.append_bashrc(session, line)
    return inner

# def install_python(version, venv_name, venv_dir):
def install_python(version):
    def inner(session):
        setup_uv(session)
        uv_python_install(version)(session)
        # uv_venv(venv_name, venv_dir)(session)
    return inner

def input_uv_params(self):
    from mini.menu import get_input
    # self.python_venv_dir = '$HOME/.virtualenv'
    self.python_version = get_input(expression=r'^3(\.\d{1,2})?$', message='python ver[3.13, 3, etc.]' + f'({self.python_version}): ', default_value=self.python_version)
    # self.python_venv = get_input(expression=r'^v\w+$', message=f'venv({self.python_venv}): ', default_value=self.python_venv)
    return {
        'version': self.python_version,
        # 'venv_name': self.python_venv,
        # 'venv_dir': self.python_venv_dir,
    }
