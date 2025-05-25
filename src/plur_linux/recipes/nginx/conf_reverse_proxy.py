from plur import base_shell
from plur import session_wrap
import coffee_src


def gen_htpasswd_lines(username, password, htpasswd_path='/etc/nginx/.htpasswd'):
    conf = f"""
    #! /bin/sh
    USER={username}
    PASS={password}
    printf "$USER:$(openssl passwd -crypt $PASS)\\n" > {htpasswd_path}
    """
    return [line[4:] for line in conf.split('\n')[1:]]


@session_wrap.bash()
def generate_local(session):
    nginx_mod_path = 'nginx/reverse_proxy.coffee'
    nginx_conf = {
        'location_list': [
            {
                'src_path': '/test',
                'dst_path': '/test',
                'url': '127.0.0.1',
                'port': '3001',
            },
            {
                'src_path': '/',
                'dst_path': '',
                'url': '192.168.122.11',
                'port': '3000',
            },
        ],
        'options': {
            'port': 80,
            'htpasswd_path': '/etc/nginx/.htpasswd'
        }
    }
    return coffee_src.generate_output(nginx_mod_path, nginx_conf)(session)


@session_wrap.sudo
def gen_nginx_conf(session):
    output_filepath = generate_local()
    base_shell.heredoc_from_local(output_filepath, '/etc/nginx/conf.d/default.conf')(session)
    base_shell.here_doc(session, '/root/gen_htpasswd.sh', gen_htpasswd_lines('testuser', '0n3pun!!'))
    base_shell.run(session, 'sh /root/gen_htpasswd.sh')
    base_shell.service_on(session, 'nginx')


