from plur import session_wrap
from plur.base_shell import *
from plur import output_methods


def keygen(passphrase="", key_type="rsa", key_bit=2048, key_path='$HOME/.ssh'):
    """
    -q: no stdout
    -t: keytype
    -b: keybit
    -f: path to save
    -N: passphrase
    """
    def func(session):
        run(session, f'ssh-keygen -q -t {key_type} -b {str(key_bit)} -f {key_path}/id_rsa -N "{passphrase}"')
    return func


def keygen_no_pass(session):
    keygen()(session)


def keygen_interact(passphrase=''):
    """Generate rsa key with ssh-keygen
       Default passphrase is none.
    """
    def func(session):
        successcase = ''  #waitprompt
        enterfilecase = 'Enter file in which to save the key'
        overwritefilecase = r'Overwrite \(y/n\)\?'
        enterpasscase = 'Enter passphrase'
        enterpassagaincase = 'Enter same passphrase again'

        rows = [[successcase, output_methods.waitprompt, None, "DONE:ssh-keygen."],
                [enterfilecase, output_methods.send_line, '', "key file name sets default"],
                [overwritefilecase, output_methods.send_line, 'y', "Existing keys are overwritten"],
                [enterpasscase, output_methods.send_line, passphrase, "Entering passphrase"],
                [enterpassagaincase, output_methods.send_line, passphrase, "Confirming passphrase again"]]

        session.do(create_sequence("ssh-keygen -t rsa", rows))
    return func


def remove_known(hostname_or_ip):
    return lambda session: run(session, f'ssh-keygen -R {hostname_or_ip}')


def copy_id(username, hostname_or_ip, password, public_key='~/.ssh/id_rsa.pub'):
    def func(session):
        action = f'ssh-copy-id -i {public_key} {username}@{hostname_or_ip}'
        rows = expects_on_login(password)
        rows += [["to make sure we haven't added extra keys that you weren't expecting.", output_methods.waitprompt, '']]

        session.do(create_sequence(action, rows))
    return func


def copy_id_force(username, hostname_or_ip, password, public_key='~/.ssh/id_rsa.pub'):
    def func(session):
        remove_known(hostname_or_ip)(session)
        copy_id(username, hostname_or_ip, password, public_key)(session)
    return func


def one_liner_to_remote_node(remote_node, one_liner_str):
    remote_str = f'{remote_node.username}@{remote_node.access_ip}'
    action = f'ssh {remote_str} {one_liner_str}'
    rows = expects_on_login(remote_node.password)
    def func(session):
        session.do(create_sequence(action, rows))
    return func


def scp(session, src_path, dst_path, password='', options='-o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null', timeout=3600):
    action = f'scp -r {options} {src_path} {dst_path}'

    rows = expects_on_login(password)
    del(rows[-1])
    rows.append([r'100\%', output_methods.success, None, action])

    session.do(create_sequence(action, rows), timeout)
    session.child.expect(session.waitprompt)


def scp_from_local(src_path, dst_path, password=''):
    @session_wrap.bash()
    def func(session):
        scp(session, src_path, dst_path, password)
    func()

