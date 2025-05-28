from plur import session_wrap
from plur import base_shell
from mini import misc

tftp_boot_dir = '/tftpboot'

ex_ip_prefix = '192.168.0'
ex_mac = '52:54:00:5e:bc:81'
ex_dnsmasq_conf = {
    'ifname': 'eth0',
    'ip': f'{ex_ip_prefix}.153',
    'netmask': '255.255.255.0',
    'dns_list': [
        '8.8.8.8',
        '8.8.4.4',
    ],
    'dhcp_range': f'{ex_ip_prefix}.0,static',
    # 'dhcp_range': f'{ex_ip_prefix}.50,{ex_ip_prefix}.100,12h',
    'dhcp_host_list': [
        f'{ex_mac},192.168.0.22,ubuntu-server',
    ]
}


def here_doc(data):
    def func(session):
        base_shell.here_doc(session, data[0], data[1])
    return func


def create_dnsmasq_conf_str(ifname, ip, netmask, dns_list, dhcp_range, dhcp_host_list):
    """
    >>> print('\\n'.join(create_dnsmasq_conf_str(**ex_dnsmasq_conf)[1]))
    """
    file_path = '/etc/dnsmasq.conf'
    dns = ','.join(dns_list)
    lines = misc.del_indent_lines(f"""
    interface={ifname}
    bind-interfaces
    
    # DNSサーバー機能を無効化
    port=0

    # TFTPサーバー機能を有効化
    enable-tftp
    tftp-root={tftp_boot_dir}

    # DHCPサーバーの設定
    dhcp-leasefile=/var/lib/misc/dnsmasq.leases
    dhcp-option=option:domain-name,"example.com"  # ドメイン名
    dhcp-option=option:router,{ip} # ルータのIPアドレス
    dhcp-option=option:netmask,{netmask} # サブネットマスク
    dhcp-option=option:dns-server,{dns} # DNSサーバーのIPアドレス
    dhcp-match=set:efi-x86_64,option:client-arch,7 # EFI bytecode
    dhcp-match=set:efi-x86_64,option:client-arch,9 # EFI x86-64
    dhcp-boot=tag:efi-x86_64,"/grubnetx64.efi"
    dhcp-match=set:bios,option:client-arch,0 # Intel x86PC
    dhcp-boot=tag:bios,"pxelinux.0"

    dhcp-range={dhcp_range} # ネットワークアドレス 
    
    """)
    lines += [f'dhcp-host={host}' for host in dhcp_host_list]
    return [file_path, lines]


def create_grub_cfg_str():
    file_path = f'{tftp_boot_dir}/grub/grub.cfg'
    lines = misc.del_indent_lines("""
    set timeout=2
    
    loadfont unicode
    
    set menu_color_normal=white/black
    set menu_color_highlight=black/light-gray

    if [ -s "${prefix}/system/${net_default_mac}" ]; then
      source "${prefix}/system/${net_default_mac}"
      echo "Machine specific grub config file ${prefix}/system/${net_default_mac} loaded"
    else
      echo "Could not find machine specific grub config file ${prefix}/system/${net_default_mac}"
      sleep 30
    fi
    """)
    return [file_path, lines]


def create_grub_menu_str(mac, pxe_ip, iso_name):
    url = f'http://{pxe_ip}/iso/{iso_name}'
    auurl = f'http://{pxe_ip}/autoinstall/' + '${net_default_mac}/'
    file_path = f'{tftp_boot_dir}/grub/system/{mac}'
    lines = ['menuentry "AutoInstall Ubuntu Server (jammy)" {']
    lines += misc.del_indent_lines(f"""
      set gfxpayload=keep
      linux   /images/jammy/vmlinuz autoinstall ip=dhcp url={url} ds="nocloud-net;s={auurl}" ---
      initrd  /images/jammy/initrd
    """)
    lines += ['}']
    return [file_path, lines]


def setup_bootloader(session):
    [base_shell.run(session, a) for a in misc.del_indent_lines(f"""
    cp /usr/lib/syslinux/modules/bios/ldlinux.c32 {tftp_boot_dir}/
    cp /usr/lib/PXELINUX/pxelinux.0 {tftp_boot_dir}/
    wget -O {tftp_boot_dir}/grubnetx64.efi http://archive.ubuntu.com/ubuntu/dists/jammy/main/uefi/grub2-amd64/current/grubnetx64.efi
    mkdir -p {tftp_boot_dir}/grub/system
    mkdir -p {tftp_boot_dir}/pxelinux.cfg
    """)]
    here_doc(create_grub_cfg_str())(session)


def create_nginx_default_conf_str():
    file_path = '/etc/nginx/conf.d/default.conf'
    lines = misc.del_indent_lines("""
    server {
        listen 80;
        server_name pxe;
        
        location / {
            # First attempt to serve request as file, then
            # as directory, then fall back to displaying a 404.
            try_files $uri $uri/ =404;
        }

        location /autoinstall {
            root /var/www/;
            autoindex on;
        }

        location /iso {
            root /var/www/;
            autoindex on;
        }
    }
    """)
    return [file_path, lines]


def setup_nginx(session):
    [base_shell.run(session, a) for a in misc.del_indent_lines(f"""
    mkdir /var/www/autoinstall /var/www/iso
    unlink /etc/nginx/sites-enabled/default
    """)]
    here_doc(create_nginx_default_conf_str())(session)
    base_shell.run(session, 'systemctl restart nginx')


def prepare_jammy_iso(session):
    iso_url = "https://ftp.riken.jp/Linux/ubuntu-releases/jammy/ubuntu-22.04.4-live-server-amd64.iso"
    iso_name = "ubuntu-22.04.4-live-server-amd64.iso"
    mount_dir = f'/mnt'
    iso_dir = '/var/www/iso'

    base_shell.work_on(session, iso_dir)
    if not base_shell.check_file_exists(session, f'{iso_dir}/{iso_name}'):
        [base_shell.run(session, a) for a in misc.del_indent_lines(f"""
        curl -O {iso_url}
        mount -t iso9660 {iso_name} {mount_dir}
        mkdir -p {tftp_boot_dir}/images/jammy
        cp /mnt/casper/initrd /mnt/casper/vmlinuz {tftp_boot_dir}/images/jammy/
        umount {mount_dir}
        """)]
    return iso_name


def create_bios_menu_str(mac, pxe_ip, iso_name):
    mac_fname = '-'.join(mac.split(':'))
    url = f'http://{pxe_ip}/iso/{iso_name}'
    auurl = f'http://{pxe_ip}/autoinstall/{mac}/'
    file_path = f'{tftp_boot_dir}/pxelinux.cfg/{mac_fname}'
    lines = misc.del_indent_lines(f"""
    default linux
    prompt 0
    timeout 30
    label linux
      kernel /images/jammy/vmlinuz
      ipappend 2
      append initrd=/images/jammy/initrd autoinstall ip=dhcp url={url} ds=nocloud-net;s={auurl} ---
    """)
    return [file_path, lines]


def create_user_data_str(mac):
    file_path = f'/var/www/autoinstall/{mac}/user-data'
    lines = misc.del_indent_lines("""
    #cloud-config
    autoinstall:
      version: 1
      identity:
        hostname: ubuntu-server
        username: worker
        password: "$1$v4y/Tz8G$mq2hT5nsuafCpIB7KlQTQ/"
      ssh:
        install-server: yes 
    storage:
      version: 2
      grub:
        # ブートオーダーを更新させない
        reorder_uefi: false
      # パーティショニング設定。config句で設定しないとreorder_uefiの設定が反映されない
      config:
        # パーティションテーブルの作成
        - type: disk
          id: sda
          ptable: gpt
          path: /dev/sda
          wipe: superblock
          preserve: false
          name: ''
          grub_device: false

        # パーティションの作成
        # ESP
        - type: partition
          id: sda1
          device: sda
          number: 1
          flag: boot
          wipe: superblock
          preserve: false
          offset: 1073741824 # 1GiB
          size: 1073741824   # 1GiB; 末尾は先頭から2GiB
          grub_device: true
        # スワップ
        - type: partition
          id: sda2
          device: sda
          number: 2
          flag: swap
          wipe: superblock
          preserve: false
          offset: 2147484160 # 前のパーティションの末尾+512バイト => 2GiB+512
          size: 34359738368  # 32GiB; 末尾は先頭から34GiB+512
          grub_device: false
        # ルートファイルシステム
        - type: partition
          id: sda3
          device: sda
          number: 3
          wipe: superblock
          preserve: false
          offset: 36507223040 # 前のパーティションの末尾+512バイト => 34GiB+512+512
          size: -1            # -1で100%指定
          grub_device: false

        # ファイルシステムの作成
        # ESP
        - type: format
          id: fs-sda1
          volume: sda1  # パーティションの作成で設定したidを指定する
          fstype: fat32 # ESPはfat32でフォーマットする
          preserve: false
        # スワップ
        - type: format
          id: fs-sda2
          volume: sda2
          fstype: swap # スワップ領域はswapを指定する
          label: swap
          preserve: false
        # ルートファイルシステム
        - type: format
          id: fs-sda3
          volume: sda3
          fstype: ext4
          preserve: false

        # マウントポイント
        # ESP
        - type: mount
          id: mount-efi
          device: fs-sda1 # ファイルシステムの作成で設定したidを指定する
          path: /boot/efi
        # スワップ
        - type: mount
          id: mount-swap
          device: fs-sda2
          path: none      # スワップ領域はnoneを指定する
        # ルートファイルシステム
        - type: mount
          id: mount-root
          device: fs-sda3
          path: /
    """)
    return [file_path, lines]


@session_wrap.sudo
def setup_pxe(session):
    base_shell.run(session, f'mkdir {tftp_boot_dir}')
    from recipes.ubuntu import ops
    ops.sudo_apt_install_y([
        'dnsmasq',
        'nginx',
        'pxelinux',
        'syslinux',
    ], True)(session)
    setup_bootloader(session)
    base_shell.run(session, 'reset')
    iso_name = prepare_jammy_iso(session)
    iso_name = "ubuntu-22.04.4-live-server-amd64.iso"
    # mac = '52:54:00:5e:bc:81'
    mac_list = ['52:54:00:63:c5:cc']
    pxe_ip = '192.168.0.153'

    setup_nginx(session)
    for mac in mac_list:
        base_shell.run(session, f'mkdir /var/www/autoinstall/{mac}')
        here_doc(create_bios_menu_str(mac, pxe_ip, iso_name))(session)
        here_doc(create_user_data_str(mac))(session)
        base_shell.run(session, f'touch /var/www/autoinstall/{mac}/meta-data')
        here_doc(create_grub_menu_str(mac, pxe_ip, iso_name))(session)
    ip_prefix = '192.168.10'
    dnsmasq_conf = {
        # 'ifname': 'eth0',
        'ifname': 'enp4s0',
        'ip': f'{ip_prefix}.153',
        'netmask': '255.255.255.0',
        'dns_list': [
            f'{ip_prefix}.1'
            # '8.8.8.8',
            # '8.8.4.4',
        ],
        'dhcp_range': f'{ip_prefix}.0,static',
        'dhcp_host_list': [f'{mac},192.168.0.22,ubuntu-server' for mac in mac_list]
    }
    here_doc(create_dnsmasq_conf_str(**dnsmasq_conf))(session)
    base_shell.run(session, 'systemctl restart dnsmasq')




