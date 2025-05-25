from plur import base_shell
from recipes.centos.kubernetes import kubeadm


def install_kvm2(session):
    commands = """
sudo yum install libvirt-daemon-kvm qemu-kvm
sudo usermod -aG libvirt $(whoami)
newgrp libvirt
curl -LO https://storage.googleapis.com/minikube/releases/latest/docker-machine-driver-kvm2
chmod +x docker-machine-driver-kvm2
sudo mv docker-machine-driver-kvm2 /usr/local/bin/
"""
    [base_shell.run(session, a) for a in commands.split('\n')[1:]]


def install_kubectl(session):
    # curl -Lo kubectl https://storage.googleapis.com/kubernetes-release/release/$(curl -s https://storage.googleapis.com/kubernetes-release/release/stable.txt)/bin/linux/amd64/kubectl
    commands = """
KUBE_VERSION=curl -s https://storage.googleapis.com/kubernetes-release/release/stable.txt
curl -Lo kubectl https://storage.googleapis.com/kubernetes-release/release/$KUBE_VERSION/bin/linux/amd64/kubectl
chmod +x kubectl
sudo mv kubectl /usr/local/bin/
    """
    [base_shell.run(session, a) for a in commands.split('\n')[1:]]


def install_minikube(session):
    commands = """
curl -Lo minikube https://storage.googleapis.com/minikube/releases/latest/minikube-linux-amd64
chmod +x minikube
sudo mv minikube /usr/local/bin/
"""
    [base_shell.run(session, a) for a in commands.split('\n')[1:]]


def start_minikube(driver=None):
    def func(session):
        if driver is "kvm2":
            install_kvm2(session)
            # need to enable path /usr/local/bin by visudo
            commands = """
sudo minikube start --vm-driver kvm2
"""
        else:
            commands = """
export MINIKUBE_WANTUPDATENOTIFICATION=false
export MINIKUBE_WANTREPORTERRORPROMPT=false
export MINIKUBE_HOME=$HOME
export CHANGE_MINIKUBE_NONE_USER=true
mkdir $HOME/.kube || true
touch $HOME/.kube/config
export KUBECONFIG=$HOME/.kube/config
sudo -E ./minikube start --vm-driver=none
"""
        [base_shell.run(session, a) for a in commands.split('\n')[1:]]
    return func


def setup(session):
    kubeadm.kubeadm_only()(session)
    # kubeadm.install_kubectl(session)
    # install_kubectl(session)

    install_minikube(session)

