from plur import base_shell
from plur import session_wrap


def configure(src_path, dst_path='/etc/default/grub', console=True, devname=True):
    @session_wrap.sudo
    def func(session):
        options = []
        if console:
            options += ['console=ttyS0,115200n8r']
        if devname:
            options += ['net.ifnames=0 biosdevname=0']
        if len(options) > 0 and src_path:
            opt = ' '.join(options)
            line = "sed '/^GRUB_CMDLINE_LINUX=/s/" + f'"$/ {opt}"/g' + f"' {src_path} > {dst_path}"
            base_shell.run(session, line)
            platform = session.nodes[-1].platform
            if platform in ['almalinux9']:
                # https://unix.stackexchange.com/questions/762697/the-grub2-mkconfig-does-not-propagate-renamed-root-logical-volume-on-rhel-9
                action = 'grub2-mkconfig --update-bls-cmdline -o /boot/grub2/grub.cfg'
            else:
                action = 'grub2-mkconfig -o /boot/grub2/grub.cfg'
            base_shell.run(session, action)
    return func


def configure_ubuntu(src_path, dst_path='/etc/default/grub', console=True, devname=True):
    @session_wrap.sudo
    def func(session):
        options = []
        if console:
            options += ['console=ttyS0,115200n8r']
        if devname:
            options += ['net.ifnames=0 biosdevname=0']
        if len(options) > 0 and src_path:
            opt = ' '.join(options)
            line = "sed '/^GRUB_CMDLINE_LINUX=/s/" + f'"$/ {opt}"/g' + f"' {src_path} > {dst_path}"
            base_shell.run(session, line)
            base_shell.run(session, 'grub-mkconfig -o /boot/grub/grub.cfg')
    return func

