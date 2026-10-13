#! /usr/bin/env python
import sys
import os
sys.path.append(os.pardir)

from plur import base_shell
from plur import session_wrap
from plur_linux.recipes.ops import ops
from plur_linux.recipes import firewalld

k8s_conf = """
net.ipv4.ip_forward = 1
net.bridge.bridge-nf-call-ip6tables = 1
net.bridge.bridge-nf-call-iptables = 1
""".split('\n')[1:]

kube_repo = """
[kubernetes]
name=Kubernetes
baseurl=https://packages.cloud.google.com/yum/repos/kubernetes-el7-x86_64
enabled=1
gpgcheck=1
repo_gpgcheck=1
gpgkey=https://packages.cloud.google.com/yum/doc/yum-key.gpg https://packages.cloud.google.com/yum/doc/rpm-package-key.gpg
""".split('\n')[1:]


@session_wrap.sudo
def install_kubectl(session):
    ops.disable_selinux(session)
    base_shell.here_doc(session, '/etc/sysctl.d/k8s.conf', k8s_conf)
    base_shell.run(session, 'sysctl --system')
    base_shell.here_doc(session, '/etc/yum.repos.d/kubernetes.repos', kube_repo)
    base_shell.yum_install(session, {'packages': [
        'kubectl'
    ]})


def install_kubeadm(version=None):
    @session_wrap.sudo
    def func(session):
        ops.disable_selinux(session)
        base_shell.here_doc(session, '/etc/sysctl.d/k8s.conf', k8s_conf)
        base_shell.run(session, 'sysctl --system')

        base_shell.here_doc(session, '/etc/yum.repos.d/kubernetes.repos', kube_repo)
        if version is None:
            base_shell.yum_install(session, {'packages': [
                'kubelet',
                'kubeadm',
                'kubectl'
            ]})
        else:
            base_shell.yum_install(session, {'packages': [
                'kubelet-' + version,
                'kubeadm-' + version,
                'kubectl-' + version
            ]})
        base_shell.service_on(session, 'kubelet')
    return func


def kubeadm_only(kube_version=None):
    # if kube_version is None:
    #     kube_version = '1.11.0'

    def func(session):
        from plur_linux.recipes.centos.docker import setup_docker
        setup_docker.install_docker_if_not_installed(session)
        install_kubeadm(kube_version)(session)
    return func


def create_kube_dir_local(session):
    create_kube_config = [
        'mkdir -p $HOME/.kube',
        'sudo cp -f /etc/kubernetes/admin.conf $HOME/.kube/config',
        'sudo chown $(id -u):$(id -g) $HOME/.kube/config',
    ]
    [base_shell.run(session, a) for a in create_kube_config]


def copy_additional(ssh_host, password=None):
    script_dir = os.path.dirname(__file__)
    @session_wrap.bash()
    def func(session2):
        from plur_linux.recipes.ops import ssh
        ssh.scp(session2, os.path.join(script_dir, 'tutorial'), f'{ssh_host}:~', password)
        ssh.scp(session2, os.path.join(script_dir, 'dashboard'), f'{ssh_host}:~', password)
    return func


show_all = lambda session: base_shell.run(session, 'kubectl get all --all-namespaces -o wide')


def setup_master(pod_network='10.244.0.0/16', cni='calico', api_ip=None):
    @session_wrap.sudo
    def kubeadm_init(session):
        import datetime
        timestamp = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
        options = ' '.join([
            f'--apiserver-advertise-address={api_ip}' if api_ip else '',
            f'--pod-network-cidr={pod_network}',
        ])
        base_shell.run(session, ' | '.join([
            f"kubeadm init {options}",
            f"tee kubeadm_init_{timestamp}.txt",
            "awk '/^kubeadm/,/discovery/' > kubeadm_join.sh"
        ]))

    def post_run(session):
        # master
        if not base_shell.check_command_exists(session, 'kubectl'):
            print('kubeadm must be installed')
            exit(1)
        else:
            fw_ports = [
                '6443/tcp',  # api server
                '2379-2380/tcp',  # etcd
                '10250/tcp',  # kubelet api
                '10251/tcp',  # kube-scheduler
                '10252/tcp',  # kube-controller-manager
                '10255/tcp',  # readonly kubelet api
            ]
            if cni == 'flannel':
                cni_apply = ['kubectl apply -f %s' % repo for repo in [
                    'https://raw.githubusercontent.com/coreos/flannel/v0.9.1/Documentation/kube-flannel.yml'
                ]]
                fw_ports += [
                    '8472/udp',  # flanneld
                ]
            else: # calico
                cni_apply = ['kubectl apply -f https://docs.projectcalico.org/v3.8/manifests/calico.yaml']
                fw_ports += [
                    # Calico
                    '179/tcp',
                    '5473/tcp',
                    '4789/udp',
                ]
            # base_shell.service_off(session, 'firewalld')
            firewalld.configure(ports=fw_ports, masquerade=True, add=True)(session)
            kubeadm_init(session)
            create_kube_dir_local(session)
            [base_shell.run(session, a) for a in cni_apply]
            base_shell.run(session, 'sudo cat /root/kubeadm_join.sh')

    return post_run


def setup_minion(session):
    # minion
    firewalld.configure(ports=[
        '10250/tcp',        # kubelet api
        '10255/tcp',        # readonly kubelet api
        '30000-32767/tcp',  # NodePort Services
        
        # '8472/udp',  # flanneld
        # '9100/tcp',  # prometheus
        # Calico
        '179/tcp',
        '5473/tcp',
        '4789/udp',
    ], masquerade=True, add=True)(session)


def drain_on_master(hostname_list):
    def post_run(session):
        for node_name in hostname_list:
            [base_shell.run(session, a) for a in [
                "kubectl drain %s --delete-local-data --force --ignore-daemonsets" % node_name,
                "kubectl delete node %s" % node_name,
            ]]
        base_shell.run(session, 'kubeadm reset')
    return post_run


def etcd_cluster_step1(host0_ip, host1_ip, host2_ip):
    @session_wrap.sudo
    def func(session):
        [base_shell.run(session, a) for a in """
cat << EOF > /etc/systemd/system/kubelet.service.d/20-etcd-service-manager.conf
[Service]
ExecStart=
#  Replace "systemd" with the cgroup driver of your container runtime. The default value in the kubelet is "cgroupfs".
ExecStart=/usr/bin/kubelet --address=127.0.0.1 --pod-manifest-path=/etc/kubernetes/manifests --cgroup-driver=systemd
Restart=always
EOF

systemctl daemon-reload
systemctl restart kubelet\n""".split('\n')[1:]]

        [base_shell.run(session, a) for a in f"""
# Update HOST0, HOST1, and HOST2 with the IPs or resolvable names of your hosts
export HOST0={host0_ip}
export HOST1={host1_ip}
export HOST2={host2_ip}
""".split('\n')[1:]]

        [base_shell.run(session, a) for a in """
# Create temp directories to store files that will end up on other hosts.
mkdir -p /tmp/${HOST0}/ /tmp/${HOST1}/ /tmp/${HOST2}/

ETCDHOSTS=(${HOST0} ${HOST1} ${HOST2})
NAMES=("infra0" "infra1" "infra2")

for i in "${!ETCDHOSTS[@]}"; do
HOST=${ETCDHOSTS[$i]}
NAME=${NAMES[$i]}
cat << EOF > /tmp/${HOST}/kubeadmcfg.yaml
apiVersion: "kubeadm.k8s.io/v1beta2"
kind: ClusterConfiguration
etcd:
    local:
        serverCertSANs:
        - "${HOST}"
        peerCertSANs:
        - "${HOST}"
        extraArgs:
            initial-cluster: ${NAMES[0]}=https://${ETCDHOSTS[0]}:2380,${NAMES[1]}=https://${ETCDHOSTS[1]}:2380,${NAMES[2]}=https://${ETCDHOSTS[2]}:2380
            initial-cluster-state: new
            name: ${NAME}
            listen-peer-urls: https://${HOST}:2380
            listen-client-urls: https://${HOST}:2379
            advertise-client-urls: https://${HOST}:2379
            initial-advertise-peer-urls: https://${HOST}:2380
EOF
done
""".split('\n')[1:]]

        base_shell.run(session, 'kubeadm init phase certs etcd-ca')

        [base_shell.run(session, a) for a in """
kubeadm init phase certs etcd-server --config=/tmp/${HOST2}/kubeadmcfg.yaml
kubeadm init phase certs etcd-peer --config=/tmp/${HOST2}/kubeadmcfg.yaml
kubeadm init phase certs etcd-healthcheck-client --config=/tmp/${HOST2}/kubeadmcfg.yaml
kubeadm init phase certs apiserver-etcd-client --config=/tmp/${HOST2}/kubeadmcfg.yaml
cp -R /etc/kubernetes/pki /tmp/${HOST2}/
# cleanup non-reusable certificates
find /etc/kubernetes/pki -not -name ca.crt -not -name ca.key -type f -delete

kubeadm init phase certs etcd-server --config=/tmp/${HOST1}/kubeadmcfg.yaml
kubeadm init phase certs etcd-peer --config=/tmp/${HOST1}/kubeadmcfg.yaml
kubeadm init phase certs etcd-healthcheck-client --config=/tmp/${HOST1}/kubeadmcfg.yaml
kubeadm init phase certs apiserver-etcd-client --config=/tmp/${HOST1}/kubeadmcfg.yaml
cp -R /etc/kubernetes/pki /tmp/${HOST1}/
find /etc/kubernetes/pki -not -name ca.crt -not -name ca.key -type f -delete

kubeadm init phase certs etcd-server --config=/tmp/${HOST0}/kubeadmcfg.yaml
kubeadm init phase certs etcd-peer --config=/tmp/${HOST0}/kubeadmcfg.yaml
kubeadm init phase certs etcd-healthcheck-client --config=/tmp/${HOST0}/kubeadmcfg.yaml
kubeadm init phase certs apiserver-etcd-client --config=/tmp/${HOST0}/kubeadmcfg.yaml
# No need to move the certs because they are for HOST0

# clean up certs that should not be copied off this host
find /tmp/${HOST2} -name ca.key -type f -delete
find /tmp/${HOST1} -name ca.key -type f -delete
""".split('\n')[1:]]
