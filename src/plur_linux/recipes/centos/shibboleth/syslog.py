from plur import base_shell as shell


def configure(p):
    def func(session):
        if 'syslog_ip' in p:
            syslog_ip = p['syslog_ip']
            rsyslog = '/etc/rsyslog.conf'
            shell.create_backup(session, rsyslog)
            shell.sed_pipe(session, rsyslog + '.org', rsyslog, [
                [
                    '^\*\.info;mail\.none;authpriv\.none;cron\.none                /var/log/messages$',
                    '*.info;mail.none;authpriv.none;cron.none                /var/log/messages\\n' +
                    '*.info;mail.none;authpriv.none;cron.none                @' + syslog_ip
                ],
                [
                    '^authpriv\.\*                                              /var/log/secure$',
                    'authpriv.*                                              /var/log/secure\\n' +
                    'authpriv.*                                              @' + syslog_ip
                ]
            ])
            shell.service_on(session, 'rsyslog')
    return func

