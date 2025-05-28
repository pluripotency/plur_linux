from mini import misc
from plur import base_shell


def create_ks_str(dist_url='', disk_dev='sda', with_console=True):
    rootpw = 'rootpw  --iscrypted $1$v4y/Tz8G$mq2hT5nsuafCpIB7KlQTQ/'
    bootloader = f'bootloader --location=mbr --boot-drive={disk_dev}'
    if with_console:
        bootloader += ' --append=" rhgb crashkernel=auto quiet vconsole.keymap=jp106 net.ifnames=0 biosdevname=0 console=ttyS0,115200n8r"'

    value = misc.del_indent(f"""
    reboot

    {dist_url}

    # インストールディスクを指定
    ignoredisk --only-use={disk_dev}

    # キーボードレイアウト
    keyboard --vckeymap=jp106 --xlayouts='jp','us'

    # システムのロケール
    lang en_US.UTF-8

    # ネットワーク設定
    network  --bootproto=dhcp --noipv6 --activate --hostname=localhost

    # 生成した root パスワード
    {rootpw}

    # タイムゾーン
    timezone Asia/Tokyo --isUtc --nontp

    # ブートローダーの設定
    {bootloader}

    # パーティションテーブルは全て初期化
    zerombr
    clearpart --all --initlabel
    part /boot --fstype="ext4" --ondisk={disk_dev} --size=1024
    part /boot/efi --fstype="vfat" --ondisk={disk_dev} --size=512
    part / --fstype xfs --grow --size=1

    %packages
    @core
    %end
    
    """)
    return value


def prepare_ks(session, pxe_ip, dist_dir):
    dist_url = f'url --url=http://{pxe_ip}/{dist_dir}/'
    ks_meta_list = [
        ['phy.ks', create_ks_str(dist_url, 'sda', with_console=False)],
        ['vda.ks', create_ks_str(dist_url, 'vda')],
        ['sda.ks', create_ks_str(dist_url, 'sda')],
    ]
    ks_dir = '/var/www/html/ks'
    base_shell.work_on(session, ks_dir)
    ks_filename_list = []
    for item in ks_meta_list:
        [
            filename,
            contents
        ] = item
        ks_filename_list += [filename]
        base_shell.here_doc(session, f'{ks_dir}/{filename}', contents.split('\n'))
    base_shell.run(session, f'chmod -R 644 {ks_dir}/*')
    return ks_filename_list
