from mini import misc
from plur import base_shell
from plur import session_wrap


def install_packages(session):
    base_shell.run(session, "dnf install -y epel-release")
    base_shell.run(session, "dnf install -y google-authenticator qrencode")


def create_google_authenticator_sh(session):
    creator_path = '~/start_google_auth.sh'
    contents = misc.del_indent_lines("""
    #! /bin/bash
    # this command will display QR code in cli
    # man google-authenticator
    # -t: TOTP
    # -d: disallow-reuse same token
    # -W: Disable window of concurrently valid codes
    # -R 30 -r 3: rate limit 3attempts/30sec
    # -e 10: 10 emergency token are saved into .google_authenticator
    # --secret: output filepath(path should care to avoid SELINUX issue)
    
    OUTFILE=/home/${USER}/.ssh/.google_authenticator
    
    if [ -f $OUTFILE ];then
        echo "$OUTFILE already exists"
    else
        google-authenticator -t -d -W -R 30 -r 3 -e 10 -f --secret=$OUTFILE
    fi
    
    """)
    base_shell.here_doc(session, creator_path, contents)


def configure_sshd(session):
    base_shell.sed_replace(
        session,
        '^ChallengeResponseAuthentication no$',
        'ChallengeResponseAuthentication yes',
        '/etc/ssh/sshd_config'
    )


def configure_pam(session):
    """
    nullok: normal ssh auth if no .ssh/.google_authenticator exists
    echo_verification: display verification code
    """
    line = r'auth required pam_google_authenticator.so nullok echo_verification_code secret=/home/${USER}/.ssh/.google_authenticator'
    base_shell.idempotent_append(
        session,
        '/etc/pam.d/sshd',
        '^' + line + '$',
        line
    )


@session_wrap.sudo
def as_root(session):
    if not base_shell.check_command_exists(session, 'google-authenticator'):
        install_packages(session)
        configure_sshd(session)
        configure_pam(session)
        base_shell.run(session, 'systemctl reload sshd')


def setup(session):
    as_root(session)
    create_google_authenticator_sh(session)
