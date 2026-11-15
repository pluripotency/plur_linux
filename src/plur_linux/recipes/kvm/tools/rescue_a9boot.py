from mini import misc

def rescue_command():
    return misc.del_indent("""
    # 1. インストール先を /boot 直下（BLS標準）に固定し、保持カーネル世代数を2に制限
    mkdir -p /etc/kernel
    echo "layout=bls" > /etc/kernel/install.conf
    sed -i 's/^installonly_limit=.*/installonly_limit=2/' /etc/dnf/dnf.conf

    # 2. 誤配置された <machine-id> ディレクトリがあれば削除し、古いカーネルを整理
    MID=$(cat /etc/machine-id)
    rm -rf /boot/efi/"$MID" /boot/"$MID"
    rpm -q kernel-core | sort -V | head -n -1 | xargs -r dnf remove -y

    # 3. 対象最新カーネルのバージョン取得とデッドリンク掃除
    KVER=$(rpm -q kernel-core --qf '%{VERSION}-%{RELEASE}.%{ARCH}\n' | sort -V | tail -n 1)
    find /lib/modules/"$KVER"/weak-updates -xtype l -delete 2>/dev/null || true
    depmod -a "$KVER"

    # 4. initramfs と BLSブートエントリの再生成・デフォルト設定
    dracut -f /boot/initramfs-"$KVER".img "$KVER"
    kernel-install add "$KVER" /boot/vmlinuz-"$KVER"
    grubby --set-default=/boot/vmlinuz-"$KVER"
    """)

def confirm_rescue():
    return """ls -lh /boot/initramfs-"$KVER".img && grep -E '^(linux|initrd)' /boot/loader/entries/*"$KVER"*.conf"""

def mount_vm_qcow2(vmname, vm_images_dir, nbd='nbd0'):
    vm_path = f'{vm_images_dir}/{vmname}.qcow2'
    mt_root = f'/mnt/{vmname}'
    root_pnum = 4
    return misc.del_indent(f"""
    sudo qemu-nbd --connect=/dev/{nbd} {vm_path}
    lsblk /dev/{nbd}
    sudo rm -rf {mt_root}
    sudo mkdir -p {mt_root}
    sudo mount /dev/{nbd}p{root_pnum} {mt_root}
    sudo mount /dev/{nbd}p{root_pnum-1} {mt_root}/boot
    sudo mount /dev/{nbd}p{root_pnum-2} {mt_root}/boot/efi
    sudo mount --bind /dev {mt_root}/dev
    sudo mount --bind /proc {mt_root}/proc
    sudo mount --bind /sys {mt_root}/sys
    """)

def umount_vm_qcow2(vmname, nbd='nbd0'):
    mt_root = f'/mnt/{vmname}'
    return misc.del_indent(f"""
    sudo umount {mt_root}/sys {mt_root}/proc {mt_root}/dev
    sudo umount {mt_root}/boot/efi 2>/dev/null || true
    sudo umount {mt_root}/boot {mt_root}
    sudo qemu-nbd --disconnect /dev/{nbd}
    """)

if __name__ == '__main__':
    vm_images_dir = '/vm_images'
    vmname = 'a9dev'
    # contents = mount_vm_qcow2(vmname, vm_images_dir)
    contents = umount_vm_qcow2(vmname)
    print(contents)


