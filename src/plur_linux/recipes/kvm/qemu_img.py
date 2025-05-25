#! /usr/bin/env python
import os
from mini import menu
from plur import base_shell
from plur import output_methods
from plur.ansi_colors import red, light_blue
from plur import session_wrap
import re


def info(session, image_file):
    return base_shell.run(session, f'qemu-img info {image_file}')


def create(session, image_file, image_size, img_format='qcow2'):
    base_shell.run(session, f'qemu-img create {image_file} -f {img_format} {image_size}')


def convert(session, src_img, dst_img, img_format='qcow2'):
    base_shell.run(session, f'qemu-img convert -c {src_img} -O {img_format} {dst_img}')


def commit(session, img_file):
    base_shell.run(session, f'qemu-img commit {img_file}')


def backing(session, src_qcow2, create_qcow2):
    base_shell.run(session, f'qemu-img create -b {src_qcow2} -f qcow2 {create_qcow2}')


def resize(image_file, add_size_by_giga):
    action = f'qemu-img resize {image_file} +{add_size_by_giga}G'
    return lambda session: base_shell.run(session, action)


def resize_with_check(image_file, add_size_by_giga):
    actions = [
        f'qemu-img resize {image_file} +{add_size_by_giga}G',
        f'qemu-img check -r all {image_file}',
        f'qemu-img info {image_file}',
    ]
    return lambda session: [base_shell.run(session, a) for a in actions]


def get_virtual_size(session, image_file):
    capture = info(session, image_file)
    virtual_size = None
    for line in capture.split('\r\n|\n'):
        match = re.search(r'virtual size: (\d+|\d+.\d+)\s?G', line)
        if match:
            size_str = match.groups(0)[0]
            virtual_size = int(float(size_str))
            print(light_blue(f'detected virtual size is {virtual_size}'))
            break
    if virtual_size:
        return virtual_size
    else:
        print(red(f'could not get virtual size of {image_file}'))
        exit(1)


def resize_to(image_path, to_size_by_giga):
    def func(session):
        virtual_size = get_virtual_size(session, image_path)
        if virtual_size:
            if to_size_by_giga > virtual_size:
                resize(image_path, to_size_by_giga - virtual_size)(session)
            elif to_size_by_giga == virtual_size:
                pass
            else:
                print(red(f"Couldn't resize to {to_size_by_giga}G, orginal size: {virtual_size}G."))
                exit(1)

    return func


def dd_expand(session, vdisk_abs_path, add_size_by_giga):
    action = f'dd if=/dev/zero bs=1M count=$(({add_size_by_giga} * 1024)) >> {vdisk_abs_path}'
    base_shell.run(session, action)


def sfdisk(session, vdisk_abs_path, option='-l'):
    action = 'sfdisk %s %s' % (option, vdisk_abs_path)
    return base_shell.run(session, action)


def write_partition_table_by_here_docs(session, vdisk_path, contents):
    # To seperate from previous commands, insert enter before and after.
    vdisk_abs_path = os.path.expanduser(vdisk_path)
    curret = [['> ', output_methods.success, None, '']]
    session.do(base_shell.create_sequence('sfdisk -f %s << EOF' % vdisk_abs_path, curret))
    [session.do(base_shell.create_sequence(content, curret)) for content in contents]
    base_shell.run(session, 'EOF')


def find_unused_loop_dev(session):
    output = base_shell.run(session, 'losetup -f')
    for line in re.split("\r\n|\n", output):
        if re.match(r'.*/dev/loop\d', line):
            return line
    session.close()
    exit(1)


def expand_vdisk_by_qemu(session, vdisk_abs_path, vdisk_size_to_gigabyte_by_int, virtual_size_gigabyte):
    if isinstance(vdisk_size_to_gigabyte_by_int, int):
        if vdisk_size_to_gigabyte_by_int > virtual_size_gigabyte:
            expand_size = vdisk_size_to_gigabyte_by_int - virtual_size_gigabyte
            resize(vdisk_abs_path, expand_size)(session)


def expand_vdisk_by_dd(session, vdisk_abs_path, vdisk_size_to_gigabyte_by_int, virtual_size_gigabyte):
    if isinstance(vdisk_size_to_gigabyte_by_int, int):
        if vdisk_size_to_gigabyte_by_int > virtual_size_gigabyte:
            expand_size = vdisk_size_to_gigabyte_by_int - virtual_size_gigabyte
            dd_expand(session, vdisk_abs_path, expand_size)


def get_partition_sector_counts(session, vdisk_abs_path):
    re_disk_info = re.compile(r'^Disk %s: \d+ cylinders, \d+ heads, \d+ sectors/track' % vdisk_abs_path)
    vdisk_partition_info = sfdisk(session, vdisk_abs_path)
    for i in re.split('\n|\r\n', vdisk_partition_info):
        if re_disk_info.match(i):
            print(i)
            splitter = re.split(r'\s+', i)
            cylinders = int(splitter[2])
            heads = int(splitter[4])
            sectors_by_track = int(splitter[6])
            sectors = cylinders * heads * sectors_by_track

            return sectors

    return None


def generate_new_partition_table(session, vdisk_abs_path, vdisk_sector_counts):
    vdisk_partition_dump = sfdisk(session, vdisk_abs_path, '-d')
    re_partition = re.compile('^%s[1-4] : start=' % vdisk_abs_path)
    re_linux = re.compile('Id=83')
    re_linux_lvm = re.compile('Id=8e')
    partitions = []
    for i in re.split('\r\n|\n', vdisk_partition_dump):
        if re_partition.match(i):
            partitions.append(i)


    i = 0
    while i > -4:
        i -= 1
        splitter = re.split(', ', partitions[i])
        if re_linux.match(splitter[2]):
            part_flag = '83'
            start = re.split(r'start=\s*', splitter[0])[1]
            new_size = vdisk_sector_counts - int(start)
            splitter[1] = 'size=%s' % new_size
            partitions[i] = ', '.join(splitter)
            new_table = 'unit: sectors\n\n' + '\n'.join(partitions)
            part_number = 5 + i
            return new_table, part_flag, part_number

        if re_linux_lvm.match(splitter[2]):
            part_flag = '8e'
            start = re.split(r'start=\s*', splitter[0])[1]
            new_size = vdisk_sector_counts - int(start)
            splitter[1] = 'size=%s' % new_size
            partitions[i] = ', '.join(splitter)
            new_table = 'unit: sectors\n\n' + '\n'.join(partitions)
            part_number = 5 + i
            return new_table, part_flag, part_number


def set_loop_device(session, vdisk_abs_path, loopdevice='/dev/loop0'):
    base_shell.run(session, 'losetup %s %s' % (loopdevice, vdisk_abs_path))
    base_shell.run(session, 'kpartx -a %s' % loopdevice)


def unset_loop_device(session, loopdevice='/dev/loop0'):
    base_shell.run(session, 'kpartx -d %s' % loopdevice)
    base_shell.run(session, 'losetup -d %s' % loopdevice)


def growpart(session, disk_dev, partition_number):
    if not base_shell.check_command_exists(session, 'growpart'):
        base_shell.run(session, 'yum install -y cloud-utils-growpart')
    base_shell.run(session, f'growpart {disk_dev} {partition_number}')


def xfs_growfs(session, partition):
    base_shell.run(session, f'xfs_growfs {partition}')


def resize2fs(session, partition):
    base_shell.run(session, '')
    base_shell.run(session, f'e2fsck -f {partition}')
    base_shell.run(session, f'resize2fs {partition}')


def expand_fs(session, disk_dev, partition_number):
    growpart(session, disk_dev, partition_number)

    partition = f'{disk_dev}{partition_number}'
    output = base_shell.run(session, f"df -T {partition} | grep {partition} " + "| awk '{print $2}'")
    for line in output.split('/n'):
        if re.search('xfs', line):
            xfs_growfs(session, partition)
        elif re.search('ext', line):
            resize2fs(session, partition)


def find_vg_name(session):
    found_vg = base_shell.run(session, 'vgscan')
    for line in re.split("\r\n|\n", found_vg):
        if re.match(r"  Found volume group .+", line):
            return re.split('"', line)[1]
    session.close()
    exit(1)


def lvm_resize(session, loop_partition, lv_path, resizefs_func):
    base_shell.run(session, 'pvscan')
    base_shell.run(session, 'pvresize %s' % loop_partition)

    vg_name = lv_path.split('/')[2]
    base_shell.run(session, 'vgchange -a y %s' % vg_name)
    base_shell.run(session, r'lvresize -l +100%FREE ' + lv_path)

    resizefs_func(session)

    base_shell.run(session, 'vgchange -a n %s' % vg_name)


def extract_format_and_size(qemu_img_info):
    re_file_format = re.compile('^file format: ')
    re_virtual_size = re.compile('^virtual size: ')
    file_format = ''
    virtual_size_gigabyte = ''
    for i in re.split('\n|\r\n', qemu_img_info):
        if re_file_format.match(i):
            file_format = i.split(': ')[1]
        if re_virtual_size.match(i):
            size_string = i.split(': ')[1].split('G (')[0]
            virtual_size_gigabyte = int(size_string.split('.')[0])
    return file_format, virtual_size_gigabyte


def get_vdisk_format_and_size(session, vdisk_abs_path):
    vdisk_info = info(session, vdisk_abs_path)
    return extract_format_and_size(vdisk_info)


# expand recipe for raw qemu image
def expand_partition(session, raw_disk_path, expand_size):
    # do expand only if file_format is raw
    file_format, virtual_size_gigabyte = get_vdisk_format_and_size(session, raw_disk_path)
    if file_format == 'raw':
        expand_vdisk_by_qemu(session, raw_disk_path, expand_size, virtual_size_gigabyte)
        sectors = get_partition_sector_counts(session, raw_disk_path)
        new_table, part_flag, part_number = generate_new_partition_table(session, raw_disk_path, sectors)
        base_shell.run(session, '')
        write_partition_table_by_here_docs(session, raw_disk_path, new_table.split('\n'))
        result = part_number, part_flag
    else:
        result = False, False
    return result


def expand(session, raw_disk_path, expand_size, lv_path, fs_type):
    # expand only when file_format is raw
    part_number, part_flag = expand_partition(session, raw_disk_path, expand_size)
    if part_number is False:
        print("Couldn't expand partition")
        exit(1)
    else:
        loop_device = find_unused_loop_dev(session)
        loop = loop_device.split('/')[2]

        mapped_loop_device = f'/dev/mapper/{loop}'
        loop_partition = f'{mapped_loop_device}p{part_number}'
        set_loop_device(session, raw_disk_path, loop_device)
        if part_flag == '83':
            if fs_type == 'ext4':
                resize2fs(session, loop_partition)
            elif fs_type == 'xfs':
                growpart(session, mapped_loop_device, part_number)
                xfs_growfs(session, loop_partition)

        elif part_flag == '8e':
            if fs_type == 'ext4':
                def resize_func(session):
                    resize2fs(session, lv_path)

                lvm_resize(session, loop_partition, lv_path, resize_func)
            elif fs_type == 'xfs':
                def resize_func(session):
                    xfs_growfs(session, lv_path)

                lvm_resize(session, loop_partition, lv_path, resize_func)

        unset_loop_device(session, loop_device)


def select_path_for_qemu_img(session):
    from recipes.ops.fs import catalogue_dir
    selected = menu.select_2nd([
        ['/vm_images', '/vm_images'],
        ['/var/lib/libvirt/images', '/var/lib/libvirt/images'],
        ['other', lambda: menu.get_input('^/.+', 'type abs path: ', 'must start with /')],
    ], 'select raw disk path.', vertical=True)
    if callable(selected):
        raw_disk_dir_path = selected()
    else:
        raw_disk_dir_path = selected

    print('raw_disk_dir_path: ' + raw_disk_dir_path)
    file_list = catalogue_dir(session, raw_disk_dir_path, r'.+\.(qcow2|raw)')
    menu_list = [[n, n] for n in file_list]
    menu_list.append(['other', lambda: menu.get_input('.+', 'input target file name')])
    selected = menu.select_2nd(menu_list, 'select target file name', vertical=True)
    if hasattr(selected, '__call__'):
        raw_disk_path = raw_disk_dir_path + '/' + selected()
    else:
        raw_disk_path = raw_disk_dir_path + '/' + selected
    return raw_disk_path


def select_partition(session, raw_disk_path):
    qemu_img_info = info(session, raw_disk_path)
    vdisk_format, vdisk_size = extract_format_and_size(qemu_img_info)
    # session.child.expect(session.nodes[-1].waitprompt)

    if vdisk_format == 'raw':
        partition_dump = sfdisk(session, raw_disk_path, '-d')

        partitions = []
        i = 0
        for line in re.split('\n', partition_dump):
            if re.search("start=", line):
                partitions.append([line, i])
                print('part ' + str(i) + ': ' + line)
                i += 1
        part_number = menu.select_2nd(partitions, 'select partition: ', vertical=True)
        return partitions[part_number][0], part_number
    else:
        return False, False


def show_partition(session, raw_disk_path, partition, partition_number):
    if partition is False:
        return False, False
    else:
        re_linux_lvm = re.compile('Id=8e')
        loop_device = find_unused_loop_dev(session)
        loop = loop_device.split('/')[2]
        loop_partition = '/dev/mapper/%sp%s' % (loop, partition_number)
        set_loop_device(session, raw_disk_path, loop_device)

        while True:
            action = input('INTERACT: ')
            if action == 'out':
                break
            else:
                base_shell.run(session, action)

        import time
        time.sleep(5)

        unset_loop_device(session, loop_device)


def show_qemu_img(kvm):
    @session_wrap.ssh(kvm)
    def func(session):
        session.sudo_i()
        session.child.delaybeforesend = 1
        raw_disk_path = select_path_for_qemu_img(session)
        partition, partition_number = select_partition(session, raw_disk_path)
        show_partition(session, raw_disk_path, partition, partition_number)
        session.child.delaybeforesend = 0
        session.su_exit()

    func()


def expand_guest_raw_ext4(raw_disk_path, expand_size=20, lv_path='/dev/centos/root'):
    @session_wrap.sudo
    def func(session=None):
        expand(session, raw_disk_path, expand_size, lv_path, 'ext4')

    return func
