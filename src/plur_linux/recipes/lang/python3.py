from plur import base_shell

def setup_python36u(session):
    """
    Procedure from
    https://www.digitalocean.com/community/tutorials/how-to-install-python-3-and-set-up-a-local-programming-environment-on-centos-7
    """
    url = 'https://centos7.iuscommunity.org/ius-release.rpm'
    [f(session) for f in [
        base_shell.yum_y_install([url]),
        base_shell.yum_y_install(['python36u'])
    ]]

def create_virtualenv(env_name, python_path='python3', venv_dir='$HOME/.virtualenv'):
    def func(session):
        base_shell.work_on(session, venv_dir)
        if not base_shell.check_dir_exists(session, f'{venv_dir}/{env_name}'):
            base_shell.run(session, f'{python_path} -m venv {env_name}')
        line = f'alias {env_name}=". {venv_dir}/{env_name}/bin/activate"'
        base_shell.append_bashrc(session, line)
    return func

def install_python3(venv_name):
    def on_user(session):
        create_virtualenv(venv_name)(session)

    def func(session):
        base_shell.yum_y_install(['python3'])(session)
        on_user(session)
    return func

