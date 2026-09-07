from mini import misc
from plur import base_shell


def create_timezone_str(a10=False):
    """Generate timezone and timesource configuration for kickstart."""
    if a10:
        return "# タイムゾーン\ntimezone Asia/Tokyo --utc\ntimesource --ntp-disable"
    else:
        return "# タイムゾーン\ntimezone Asia/Tokyo --isUtc --nontp"


def create_standard_volume_str(disk_dev='sda'):
    """Generate standard partitioning configuration: single root partition growing to fill disk."""
    return f"""# パーティションテーブルは全て初期化
zerombr
clearpart --all --initlabel
part /boot --fstype="ext4" --ondisk={disk_dev} --size=2048
part /boot/efi --fstype="vfat" --ondisk={disk_dev} --size=512
part / --fstype xfs --grow --size=1"""


def create_lvm_data_volume_str(
    disk_dev='sda',
    root_size_mb=51200,
    swap_size_mb=8192,
    vg_name='vg_system',
):
    """Generate LVM partitioning configuration: 50GB root, 8GB swap, remaining disk space allocated to /data."""
    return f"""# ストレージ・パーティション設定 (UEFI / LVM + XFS)
zerombr
clearpart --all --initlabel

# 1. UEFI ブート用必須パーティション (/boot/efi)
part /boot/efi --fstype="efi" --size=600 --ondisk={disk_dev}

# 2. ブートパーティション (/boot)
part /boot --fstype="xfs" --size=1024 --ondisk={disk_dev}

# 3. LVM 物理ボリューム (PV) の作成 (残りを全割り当て)
part pv.01 --fstype="lvmpv" --size=1 --grow --ondisk={disk_dev}

# 4. ボリュームグループ (VG) の構築
volgroup {vg_name} pv.01

# 5. 論理ボリューム (LV) の切り分け
logvol / --fstype="xfs" --size={root_size_mb} --name=lv_root --vgname={vg_name}
logvol swap --fstype="swap" --size={swap_size_mb} --name=lv_swap --vgname={vg_name}
logvol /data --fstype="xfs" --size=1 --grow --name=lv_data --vgname={vg_name}"""


def create_ks_str(
    dist_url='',
    disk_dev='sda',
    with_console=True,
    a10=False,
    volume_type='standard',
    volume_str=None,
    root_size_mb=51200,
    swap_size_mb=8192,
    vg_name='vg_system',
):
    """Unified Kickstart configuration string generator.

    Supports:
    - a10=False: AlmaLinux 8/9 timezone syntax
    - a10=True: AlmaLinux 10 timezone & timesource syntax
    - volume_type='standard': full disk single root partition
    - volume_type='lvm' / 'lvm_data': LVM with 50GB root, 8GB swap, rest to /data
    - volume_str: custom partitioning string
    """
    rootpw = 'rootpw  --iscrypted $1$v4y/Tz8G$mq2hT5nsuafCpIB7KlQTQ/'
    bootloader = f'bootloader --location=mbr --boot-drive={disk_dev}'
    if with_console:
        bootloader += ' --append=" rhgb crashkernel=auto quiet vconsole.keymap=jp106 net.ifnames=0 biosdevname=0 console=ttyS0,115200n8r"'

    timezone_part = create_timezone_str(a10=a10)

    if volume_str is not None:
        partition_part = volume_str.strip()
    elif volume_type in ('lvm', 'lvm_data'):
        partition_part = create_lvm_data_volume_str(
            disk_dev=disk_dev,
            root_size_mb=root_size_mb,
            swap_size_mb=swap_size_mb,
            vg_name=vg_name,
        )
    else:
        partition_part = create_standard_volume_str(disk_dev=disk_dev)

    value = f"""reboot

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

{timezone_part}

# ブートローダーの設定
{bootloader}

{partition_part}

%packages
@core
%end
"""
    return value


def create_a10_ks_str(dist_url='', disk_dev='sda', with_console=True, volume_type='standard', **kwargs):
    """Backward-compatible wrapper for AlmaLinux 10 Kickstart generation."""
    return create_ks_str(
        dist_url=dist_url,
        disk_dev=disk_dev,
        with_console=with_console,
        a10=True,
        volume_type=volume_type,
        **kwargs,
    )


def prepare_ks(session, pxe_ip, dist_dir, a10=False, include_lvm=True):
    """Prepare and deploy kickstart files on the PXE server."""
    dist_url = f'url --url=http://{pxe_ip}/{dist_dir}/'
    ks_meta_list = [
        ['phy.ks', create_ks_str(dist_url, 'sda', with_console=False, a10=a10, volume_type='standard')],
        ['vda.ks', create_ks_str(dist_url, 'vda', with_console=True, a10=a10, volume_type='standard')],
        ['sda.ks', create_ks_str(dist_url, 'sda', with_console=True, a10=a10, volume_type='standard')],
    ]
    if include_lvm:
        ks_meta_list += [
            ['phy_lvm.ks', create_ks_str(dist_url, 'sda', with_console=False, a10=a10, volume_type='lvm_data')],
            ['vda_lvm.ks', create_ks_str(dist_url, 'vda', with_console=True, a10=a10, volume_type='lvm_data')],
            ['sda_lvm.ks', create_ks_str(dist_url, 'sda', with_console=True, a10=a10, volume_type='lvm_data')],
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
