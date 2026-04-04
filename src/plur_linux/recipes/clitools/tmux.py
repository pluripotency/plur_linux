from plur import base_shell

def install_tmux_appimage(version='3.5a'):
    def inner(session):
        dst_dir = '/usr/local/bin'
        image_name = 'tmux.appimage'
        url = f'https://github.com/nelsonenzo/tmux-appimage/releases/download/{version}/{image_name}'
        base_shell.work_on(session, '/tmp')
        base_shell.run(session, f'curl -LO {url}')
        base_shell.run(session, f'chmod +x ./{image_name}')
        base_shell.run(session, f'sudo mv ./{image_name} {dst_dir}')
        alias_str = f'alias tmux="{dst_dir}/{image_name}"'
        base_shell.idempotent_append(session, '~/.bashrc', alias_str, alias_str)
    return inner


