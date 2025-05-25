import os
import sys
sys.path.append(os.pardir)
from plur import base_shell as shell
from plur import session_wrap
from string import Template


def runnable():
    return [
        setup
    ]


def setup(nfs_exports):
    """
    nfs setting with /etc/exports
    No chkconfig nfs on. Run it yourself if you need it.
    """
    @session_wrap.sudo
    def func(session):
        nfs_exports_path = '/etc/exports'
        for l in nfs_exports:
            if not shell.check_dir_exists(session, l['path']):
                shell.create_dir(session, l['path'])
            if not 'options' in l:
                l['options'] = '(rw,no_root_squash,sync)'

        shell.here_doc(session, nfs_exports_path, create_exports_contents(nfs_exports))
        shell.yum_install(session, {'packages': ['nfs-utils']})
        edit_idmapd_conf(session)
        shell.run(session, 'service rpcbind restart')
        shell.run(session, 'service nfslock restart')
        capture = shell.run(session, 'service nfs restart')
    return func


def sed(s_exp, d_exp):
    return "sed -e 's/%s/%s/' | " % (s_exp, d_exp)


def change_domain(domain):
    s_exp = r'#Domain = local.domain.edu'
    d_exp = 'Domain = %s' % domain
    return sed(s_exp, d_exp)


def edit_idmapd_conf(session):
    """
    >>> from plur import session_wrap
    >>> from plur import base_node
    >>> session = session_wrap.ssh(base_node.Linux('test'))
    >>> session.sudo_i()
    >>> edit_idmapd_conf(session)
    >>> session.su_exit()
    >>> session.close()

    """
    node = session.nodes[-1]
    domain_array = node.fqdn.split('.')
    del domain_array[0]
    domain = '.'.join(domain_array)
    idmapd_conf = '/etc/idmapd.conf'
    pipe = change_domain(domain)
    shell.create_backup(session, idmapd_conf)
    src_file = idmapd_conf + '.org'
    file_in = 'cat %s | ' % src_file
    file_out = 'cat > %s' % idmapd_conf
    shell.run(session, file_in + pipe + file_out)


def create_exports_contents(nfs_exports):
    """
    >>> from nodes.KVM import nodes
    >>> import json
    >>> json.dumps(create_exports_contents(nodes().vpf14.nfs_exports), indent=2)
    """
    nfs_exports_template = Template("$path        $ip$options")
    return [nfs_exports_template.substitute(path=l['path'], ip=l['ip'], options=l['options']) for l in nfs_exports]

