ks_file_contents = """# accept VMware EULA
vmaccepteula

# Setting rootpw
# for generating encrypted pasword : Use openssl passwd -1 (rootpw)
rootpw --iscrypted $1$a5Kw3EG3$SEATiQZtW7HSjac7Wr/HY.

# install target
#install --firstdisk --preservevmfs
install --firstdisk --overwritevmfs

# network setting
#network --bootproto=static --ip=172.22.159.146 --gateway=172.22.158.1 --netmask=255.255.254.0 --vlanid=19 --hostname=hoge.example.com --addvmportgroup=1
network --bootproto=dhcp --device=vmnic0

# reboot after install
reboot

%post --interpreter=python --ignorefailure=true
import time
stampFile = open('/finished.stamp', mode='w')
stampFile.write(time.asctime())

%firstboot --interpreter=busybox
vim-cmd hostsvc/enable_ssh
vim-cmd hostsvc/start_ssh

vim-cmd hostsvc/enable_esx_shell
vim-cmd hostsvc/start_esx_shell

# enable password login (SSH)
sed -i "s/PasswordAuthentication no/PasswordAuthentication yes/g" /etc/ssh/sshd_config"""
