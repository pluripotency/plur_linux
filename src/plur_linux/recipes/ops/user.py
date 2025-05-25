import re
from plur.base_shell import run, create_sequence, add_sudoer, create_backup, sed_replace
from plur.output_methods import success, waitprompt, send_pass, send_pass_f, send_line_f


def check_id(session, id):
    action = 'id ' + id
    rows = [
        [r'uid=\d{1,5}\(%s\) gid=\d{1,5}\(%s\) groups=\d{1,5}\(%s\)' % (id, id, id), success, True, ''],
        [r'uid=\d{1,5}.{1,10} gid=\d{1,5}.{1,10} groups=\d{1,5}.+', success, True, ''],
        ['id: .?%s.?: [nN]o such user' % id, success, False, ''],
    ]
    result = session.do(create_sequence(action, rows))
    session.child.expect(session.waitprompt)
    return result


def add_user_to_group(session, groupname, username):
    action = 'gpasswd -a %s %s' % (username, groupname)

    true_case = "Adding user %s to group %s" % (username, groupname)
    rows = [[true_case, success, True, true_case]]

    session.do(create_sequence(action, rows))
    session.child.expect(session.waitprompt)
    return run(session, 'cat /etc/group | grep ' + groupname)


def del_user_from_group(session, groupname, username):
    action = 'gpasswd -d %s %s' % (username, groupname)
    run(session, action)

    # true_case = "Removing user %s to group %s" % (username, groupname)
    # rows = [[true_case, waitprompt, True, true_case]]
    # session.do(create_sequence(action, rows))

    session.child.expect(session.waitprompt)


def is_user_in_group(groupname, username):
    action = 'cat /etc/group | egrep "%s:x:[0-9]+:.*%s.*"' % (groupname, username)
    true_case = '%s:x:[0-9]+:.*%s.*' % (groupname, username)
    rows = [[true_case, success, True, true_case]]
    rows += ['', waitprompt, False, 'no output.']
    return create_sequence(action, rows)


def groupadd(session, groupname, gid=None):
    if gid is None:
        action = 'groupadd %s' % groupname
    else:
        action = 'groupadd -g %s %s' % (gid, groupname)

    false_case = "groupadd: group '%s' already exists" % groupname
    return not re.search(false_case, run(session, action))


def useradd(session, username, uid=None):
    if uid is None:
        action = f'useradd {username} -m -d /home/{username}'
    else:
        action = f'useradd -u {uid} {username} -m -d /home/{username}'
    false_case = f"useradd: user '{username}' already exists"
    return not re.search(false_case, run(session, action))


def usermod(session, username, options):
    ops = []
    if 'home' in options:
        ops += ['-d', options['home']]
    if 'uid' in options:
        ops += ['-u', options['uid']]
    if 'shell' in options:
        ops += ['-s', options['shell']]

    action = 'usermod ' + ' '.join(ops) + ' ' + username
    run(session, action)


def cat_user(session, username):
    action = 'cat /etc/passwd | grep %s' % username
    true_case = '%s:x:[0-9]+:[0-9]+:.*:.*'
    return not re.search(true_case, run(session, action))


def chpasswd(session, username, password):
    run(session, "echo '%s:%s' | chpasswd" % (username, password))


def passwd(username, password):
    def func(session):
        action = 'passwd %s' % username
        success_centos = r'passwd: all authentication tokens updated successfully\.'
        success_ubuntu = 'passwd: password updated successfully'

        row = [['New password: ', send_pass, password, 'changing password']]
        row += [['Retype new password: ', send_pass, password, 'changing password']]
        row += [['new UNIX password: ', send_pass, password, '']]
        row += [[success_centos, success, True, '']]
        row += [[success_ubuntu, success, True, '']]
        row += [['updated successfully', success, True, '']]

        session.do(create_sequence(action, row))
        session.child.expect(session.waitprompt)
    return func


def adduser_ubuntu(session, username, password):
    rows = [
        ['New password:', send_pass_f(password), '']
        , ['Retype new password:', send_pass_f(password), '']
        , [r'Full Name \[]:',   send_line_f('')]
        , [r'Room Number \[]:', send_line_f('')]
        , [r'Work Phone \[]:',  send_line_f('')]
        , [r'Home Phone \[]:',  send_line_f('')]
        , [r'Other \[]:',       send_line_f('')]
        , [r'Is the information correct\? \[Y/n]', send_line_f('y')]
        , ['', waitprompt, True]
    ]
    session.do(create_sequence(f'adduser {username}', rows))


def add_users(session, users):
    """
    users = [
        {
            'username': 'worker',
            'password': 'worker',
            'login_shell': '/bin/bash',
            'group': 'wheel'
        }
    ]
    """
    import json
    # if session.platform == 'centos7':
    #     session.child.delaybeforesend = 1
    if session.username != 'root':
        # must be root
        return
    platform = session.nodes[-1].platform
    for user in users:
        # print(ansi_colors.cyan(json.dumps(user, indent=2)))
        if 'username' in user and 'password' in user:
            username = user['username']
            password = user['password']
            if username == 'root':
                if platform != 'ubuntu':
                    passwd(username, password)(session)
            elif not check_id(session, username):
                if platform == 'ubuntu':
                    adduser_ubuntu(session, username, password)
                else:
                    useradd(session, username)
                    passwd(username, password)(session)
            else:
                passwd(username, password)(session)
            if 'login_shell' in user:
                usermod(session, username, {'shell': user['login_shell']})
            if 'sudoers' in user and user['sudoers']:
                add_sudoer(session, username)
            if 'group' in user:
                group = user['group']
                if group == 'wheel':
                    enable_wheel(session)
                add_user_to_group(session, username, group)


def useradd_with_login_shell(session, username, login_shell='/bin/bash'):
    node = session.nodes[-1]
    if node.username != 'root':
        session.sudo_i()
    useradd(session, username)
    usermod(session, username, {'shell': login_shell})
    if node.username != 'root':
        session.su_exit()


def enable_wheel(session):
    su_file = '/etc/pam.d/su'
    s_exp = r'#auth\t\trequired\tpam_wheel.so use_uid'
    d_exp = r'auth\t\trequired\tpam_wheel.so use_uid'
    create_backup(session, su_file)
    sed_replace(session, s_exp, d_exp, su_file + '.org', su_file)

    captured = run(session, 'cat /etc/pam.d/su')

