from mini import misc
from plur import session_wrap
from plur import base_shell
from plur_linux.recipes import firewalld


def create_test_page(session):
    base_shell.here_doc(session, '/var/www/html/index.html', misc.del_indent_lines("""
    <html>
    <body>
    <div style="width: 100%; font-size: 40px; font-weight: bold; text-align: center;">
    Test Page
    </div>
    </body>
    </html>
    """))


ex_http_params = {
    'file_name': 'pxeboot.conf',
    'alias': '/almalinux8',
    'dir_path': '/var/pxe/almalinux8',
    'allowed_net': '192.168.10.0/24'
}


def create_pxe_http_str(alias, dir_path, allowed_net, file_name):
    """
    >>> file_name, contents = create_pxe_http_str(**ex_http_params)
    >>> print(contents)
    Alias /almalinux8 /var/pxe/almalinux8
    <Directory /var/pxe/almalinux8>
        Options Indexes FollowSymLinks
        Require ip 127.0.0.1 192.168.10.0/24
    </Directory>
    """
    return file_name,  misc.del_indent(f"""
    Alias {alias} {dir_path}
    <Directory {dir_path}>
        Options Indexes FollowSymLinks
        Require ip 127.0.0.1 {allowed_net}
    </Directory>
    """)


def prepare_conf(session, http_params):
    # conf_path = '/etc/httpd/conf/httpd.conf'
    file_name, contents = create_pxe_http_str(**http_params)
    base_shell.here_doc(session, f'/etc/httpd/conf.d/{file_name}', contents.split('\n'))


def setup(set_fw=True, http_params=None):
    @session_wrap.sudo
    def func(session):
        if set_fw:
            firewalld.configure(services=['http'], add=True)
        base_shell.run(session, 'dnf install -y httpd')
        base_shell.run(session, 'mv /etc/httpd/conf.d/welcome.conf /etc/httpd/conf.d/welcome.conf.org')
        if http_params:
            prepare_conf(session, http_params)
        create_test_page(session)
        base_shell.run(session, 'systemctl enable --now httpd')
    return func

