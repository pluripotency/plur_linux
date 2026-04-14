from plur.base_shell import run, work_on, here_doc, patch


def ntp_patch(session, node):
    if hasattr(node, 'ntpservers') and session.username == 'root':
        ntpservers = node.ntpservers
        work_on(session, '/etc/')

        patch_list = [
            '*** ntp.conf',
            '--- ntp.conf',
            '***************',
            '*** 20,27 ****',
            '  # Use public servers from the pool.ntp.org project.',
            '  # Please consider joining the pool (http://www.pool.ntp.org/join.html).',
            '! server 0.centos.pool.ntp.org iburst',
            '! server 1.centos.pool.ntp.org iburst',
            '! server 2.centos.pool.ntp.org iburst',
            '! server 3.centos.pool.ntp.org iburst',
            '  ',
            '  #broadcast 192.168.1.255 autokey\t# broadcast server'
        ]
        line_count = 23
        servers = []
        for srv in ntpservers:
            line_count = line_count + 1
            servers += [
                '! server %s iburst' % srv
            ]

        patch_list += [
            '--- 20,%d ----' % line_count,
            '  # Use public servers from the pool.ntp.org project.',
            '  # Please consider joining the pool (http://www.pool.ntp.org/join.html).'
        ]
        patch_list += servers
        patch_list += [
            '  ',
            '  #broadcast 192.168.1.255 autokey\t# broadcast server'
        ]

        patch_file = '/root/ntp_patch'
        here_doc(session, patch_file, patch_list)
        patch(session, patch_file)
        run(session,'rm -rf ' + patch_file)


def configure(session, node):
    if hasattr(node, 'ntpservers'):
        ntp_patch(session, node)

    run(session, 'service ntpd start')
    run(session, 'chkconfig ntpd on')

