from mini import misc
from plur import session_wrap
from plur import base_shell
from recipes import firewalld


def install_base(session):
    base_shell.run(session, 'sudo dnf install -y ' + ' '.join([
        'vim',
        'git',
        'tmux',
        'wget',
        'iproute-tc',
    ]))


def prepare_kubenetes_official_repo(session):
    version = 'v1.31'
    base_shell.run(session, misc.del_indent(f"""
    # This overwrites any existing configuration in /etc/yum.repos.d/kubernetes.repo
    cat <<EOF | sudo tee /etc/yum.repos.d/kubernetes.repo
    [kubernetes]
    name=Kubernetes
    baseurl=https://pkgs.k8s.io/core:/stable:/{version}/rpm/
    enabled=1
    gpgcheck=1
    gpgkey=https://pkgs.k8s.io/core:/stable:/{version}/rpm/repodata/repomd.xml.key
    exclude=kubelet kubeadm kubectl cri-tools kubernetes-cni
    EOF

    """))


def install_helm(session):
    [base_shell.run(session, action) for action in misc.del_indent_lines("""
    curl -O https://raw.githubusercontent.com/helm/helm/main/scripts/get-helm-3
    bash ./get-helm-3
    helm version
    """)]



def setup_manager_node(host_lines, ctl_ip ='192.168.10.82'):
    @session_wrap.sudo
    def inner(session):
        install_base(session)
        [base_shell.run(session, f"echo '{line}' >> /etc/hosts") for line in host_lines]
        base_shell.run(session, misc.del_indent("""
        setsebool -P httpd_can_network_connect on
        setsebool -P httpd_graceful_shutdown on
        setsebool -P httpd_can_network_relay on
        setsebool -P nis_enabled on
        semanage port -a -t http_port_t -p tcp 6443 
        """))
        firewalld.configure(services=[
            'kube-apiserver',
            'https',
            'http',
        ], add=True)(session)
        base_shell.run(session, 'dnf install -y nginx nginx-mod-stream')
        nginx_conf_path = '/etc/nginx/nginx.conf'
        [base_shell.run(session, f"echo '{line}' >> {nginx_conf_path}") for line in misc.del_indent_lines(f"""
        stream {{
            upstream k8s-api {{
                server {ctl_ip}:6443;
            }}
            server {{
                listen 6443;
                proxy_pass k8s-api;
            }}
        }}
        """)]
        [base_shell.sed_replace(session, exp[0], exp[1], nginx_conf_path) for exp in [
            ['        listen       80;', '        listen       8080;'],
            [r'        listen       \[::]:80;', '        listen       [::]:8080;']
        ]]
        base_shell.run(session, 'systemctl enable --now nginx')
        prepare_kubenetes_official_repo(session)
        base_shell.run(session, 'sudo yum install --enablerepo=kubernetes -y kubectl --disableexcludes=kubernetes')
    return inner


def configure_sysctl(session):
    base_shell.run(session, misc.del_indent(f"""
    cat <<EOF | sudo tee /etc/sysctl.d/99-k8s-cri.conf
    net.bridge.bridge-nf-call-iptables=1
    net.ipv4.ip_forward=1
    net.bridge.bridge-nf-call-ip6tables=1
    fs.inotify.max_user_watches = 524288
    fs.inotify.max_user_instances = 512
    EOF

    """))
    base_shell.run(session, 'sudo sysctl --system')


@session_wrap.sudo
def configure_modules(session):
    [base_shell.run(session, action) for action in misc.del_indent_lines(r"""
    modprobe overlay
    modprobe br_netfilter
    echo -e overlay\\nbr_netfilter > /etc/modules-load.d/k8s.conf
    """)]


def create_kubeadm_init_sh_str(mgr_ip='192.168.10.81', ctl_ip='192.168.10.82', podnet='10.255.0.0/16'):
    return misc.del_indent(rf"""
    cat <<'EOF' | sudo tee /root/kubeadm_init.sh
    #! /bin/bash
    MGRIP={mgr_ip}
    CTLIP={ctl_ip}
    PODNET={podnet}

    kubeadm init --control-plane-endpoint=$MGRIP \
        --apiserver-advertise-address=$CTLIP \
        --pod-network-cidr=$PODNET \
        --cri-socket=unix:///var/run/crio/crio.sock
    EOF

    """)

def create_hosts(host_lines):
    @session_wrap.sudo
    def inner(session):
        [base_shell.run(session, f"echo '{line}' >> /etc/hosts") for line in host_lines]
    return inner

