from plur import base_shell


def change_resolve_order(session):
    nsswitch_conf = '/etc/nsswitch.conf'
    base_shell.create_backup(session, nsswitch_conf)
    base_shell.sed_pipe(session, nsswitch_conf + '.org', nsswitch_conf, [
        ['^hosts:      files dns myhostname', 'hosts:      files myhostname dns'],
    ])


