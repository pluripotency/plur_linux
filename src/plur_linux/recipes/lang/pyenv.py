from mini import misc
from plur import base_shell
from plur.output_methods import send_line, waitprompt

def install_requirements(session):
    package_lines = misc.del_indent_lines("""
    tar
    xz-devel
    gcc
    zlib-devel
    bzip2
    bzip2-devel
    readline
    readline-devel
    sqlite
    sqlite-devel
    openssl
    openssl-devel
    libffi-devel
    make
    """)
    if not base_shell.check_command_exists(session, 'git'):
        package_lines += ['git']
    base_shell.run(session, 'sudo yum install -y ' + ' \\\n'.join(package_lines))

def clone_pyenv_repo(session):
    pyenv_path = '$HOME/.pyenv'
    if not base_shell.check_dir_exists(session, pyenv_path):
        base_shell.run(session, f'git clone https://github.com/pyenv/pyenv.git {pyenv_path}')
    return pyenv_path

def pyenv_init(session, pyenv_path, rcpath='~/.bashrc'):
    if not base_shell.check_line_exists_in_file(session, rcpath, 'PYENV_ROOT'):
        [base_shell.run(session, a) for a in misc.del_indent_lines(f"""
        echo 'export PYENV_ROOT="{pyenv_path}"' >> {rcpath}
        echo 'export PATH="$PYENV_ROOT/bin:$PATH"' >> {rcpath}
        echo 'eval "$(pyenv init -)"' >> {rcpath}
        source {rcpath}
        """)]

def install_pyenv(session):
    install_requirements(session)
    pyenv_path = clone_pyenv_repo(session)
    pyenv_init(session, pyenv_path)

def setup_python_by_pyenv(version):
    def func(session):
        session.do(base_shell.create_sequence(f'pyenv install {version}', [
            [r'installation. \(y/N\) ', send_line, 'y'],
            ['', waitprompt, ''],
        ]))
        base_shell.run(session, f'pyenv global {version}')
    return func

def install(version, venv_name, venv_dir):
    def func(session):
        install_pyenv(session)
        setup_python_by_pyenv(version)(session)
        if venv_name:
            from recipes.lang import python3
            python3.create_virtualenv(venv_name, python_path='~/.pyenv/shims/python', venv_dir=venv_dir)(session)
    return func

def input_pyenv_params(self):
    from lib.menu import get_input
    self.python_venv_dir = '$HOME/.virtualenv'
    self.python_version = get_input(expression=r'^3(\.\d{1,2})?$', message='python ver[3.13, 3, etc.]' + f'({self.python_version}): ', default_value=self.python_version)
    self.python_venv = get_input(expression=r'^v\w+$', message=f'venv({self.python_venv}): ', default_value=self.python_venv)
    return {
        'version': self.python_version,
        'venv_name': self.python_venv,
        'venv_dir': self.python_venv_dir,
    }
