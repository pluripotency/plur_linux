from mini import misc
from plur.base_shell import re, run, here_doc
from plur import session_wrap


def add_standard_logrotate(logrotate_name, log_path_list, term='weekly', rotate=4):
    @session_wrap.sudo
    def func(session):
        platform = session.nodes[-1].platform
        out_path = f'/etc/logrotate.d/{logrotate_name}'
        contents = log_path_list + misc.del_indent_lines(f"""
        {{
            notifempty
            {term}
            rotate {rotate}
            compress
            missingok
            sharedscripts
        """)
        if re.search('^(alma)', platform):
            contents += misc.del_indent_lines("""
                postrotate
                    /usr/bin/systemctl -s HUP kill rsyslog.service >/dev/null 2>&1 || true
                endscript
            }
            """)
        else:
            contents += misc.del_indent_lines("""
                postrotate
                    /bin/kill -HUP `cat /var/run/syslogd.pid 2> /dev/null` 2> /dev/null || true
                endscript
            }
            """)
        run(session, f'rm -f {out_path}')
        here_doc(session, out_path, contents)
    return func


def add_custom_logrotate(logrotate_name, log_path_list, custom_contents):
    contents = '\n'.join(log_path_list)
    contents += '\n' + custom_contents
    out_path = f'/etc/logrotate.d/{logrotate_name}'

    @session_wrap.sudo
    def func(session):
        run(session, f'rm -f {out_path}')
        here_doc(session, out_path, contents.split('\n'))
    return func


def add_c2021(session):
    name = 'c2021'
    mcloud_log_dir = '/var/log/MCloud'
    log_path_list = [f'{mcloud_log_dir}/{name}.log' for name in [
        'c2021_*',
        'local1'
    ]]
    add_standard_logrotate(name, log_path_list)(session)
