import os
import re
from mini.ansi_colors import cyan, yellow, green, red, rm_color
from mini.menu import choose_num, get_input
from plur import base_shell
from plur_linux.recipes.kvm.spawn import xml_dir


def mib_to_kib(memory_mb):
    return int(memory_mb) * 1024


def kib_to_mib(memory_kib):
    return int(memory_kib) // 1024


def parse_xml_list(capture, target_xml_dir=xml_dir):
    xml_files = []
    base_dir = target_xml_dir.rstrip("/")
    for line in capture.splitlines():
        s = rm_color(line).strip()
        if not s or " " in s or "*" in s:
            continue
        filename = os.path.basename(s)
        if re.match(r"^[a-zA-Z0-9_.-]+\.xml$", filename):
            full_path = f"{base_dir}/{filename}"
            if full_path not in xml_files:
                xml_files.append(full_path)
    return sorted(xml_files)


def list_xml_files(session, target_xml_dir=xml_dir, sudo=True):
    sudo_prefix = "sudo " if sudo else ""
    capture = base_shell.run(
        session, f"{sudo_prefix}ls --color=never -1 {target_xml_dir}/*.xml 2>/dev/null | cat"
    )
    return parse_xml_list(capture, target_xml_dir=target_xml_dir)


def parse_vcpu_and_memory(xml_content):
    vcpu_match = re.search(r"<vcpu[^>]*>\s*(\d+)\s*</vcpu>", xml_content)
    mem_match = re.search(r"<memory[^>]*>\s*(\d+)\s*</memory>", xml_content)
    cur_mem_match = re.search(r"<currentMemory[^>]*>\s*(\d+)\s*</currentMemory>", xml_content)

    vcpu = int(vcpu_match.group(1)) if vcpu_match else None
    memory_kib = int(mem_match.group(1)) if mem_match else None
    current_memory_kib = int(cur_mem_match.group(1)) if cur_mem_match else None
    memory_mb = kib_to_mib(memory_kib) if memory_kib is not None else None

    return {
        "vcpu": vcpu,
        "memory_kib": memory_kib,
        "memory_mb": memory_mb,
        "current_memory_kib": current_memory_kib,
    }


def get_vcpu_and_memory(session, xml_path, sudo=True):
    sudo_prefix = "sudo " if sudo else ""
    capture = base_shell.run(session, f"{sudo_prefix}cat {xml_path}")
    return parse_vcpu_and_memory(capture)


def update_memory(session, xml_path, memory_mb, sudo=True):
    sudo_prefix = "sudo " if sudo else ""
    memory_kib = mib_to_kib(memory_mb)
    base_shell.run(
        session,
        f'{sudo_prefix}sed -i -E '
        f'-e "s|(<memory[^>]*>)[0-9]+(</memory>)|\\1{memory_kib}\\2|g" '
        f'-e "s|(<currentMemory[^>]*>)[0-9]+(</currentMemory>)|\\1{memory_kib}\\2|g" '
        f'{xml_path}',
    )
    return memory_kib


def update_vcpu(session, xml_path, vcpu, sudo=True):
    sudo_prefix = "sudo " if sudo else ""
    base_shell.run(
        session,
        f'{sudo_prefix}sed -i -E '
        f'"s|(<vcpu[^>]*>)[0-9]+(</vcpu>)|\\1{int(vcpu)}\\2|g" '
        f'{xml_path}',
    )
    return int(vcpu)


def edit_vm_xml(session, xml_path, vcpu=None, memory_mb=None, define=True, sudo=True):
    sudo_prefix = "sudo " if sudo else ""
    if vcpu is not None:
        update_vcpu(session, xml_path, vcpu, sudo=sudo)
    if memory_mb is not None:
        update_memory(session, xml_path, memory_mb, sudo=sudo)
    if define:
        base_shell.run(session, f"{sudo_prefix}virsh define {xml_path}")


def select_xml_file(session, target_xml_dir=xml_dir, sudo=True):
    xml_files = list_xml_files(session, target_xml_dir=target_xml_dir, sudo=sudo)
    if not xml_files:
        print(red(f"No XML files found in {target_xml_dir}"))
        return None
    menu_items = [os.path.basename(p) for p in xml_files] + ["Back"]
    num = choose_num(menu_items, yellow(f"Please select XML in {target_xml_dir}"))
    if num is None or num == len(xml_files):
        return None
    return xml_files[num]


def menu_on_kvm(session, target_xml_dir=xml_dir, sudo=True):
    xml_path = select_xml_file(session, target_xml_dir=target_xml_dir, sudo=sudo)
    if not xml_path:
        return

    info = get_vcpu_and_memory(session, xml_path, sudo=sudo)
    cur_vcpu = info["vcpu"]
    cur_mem_mb = info["memory_mb"]
    cur_mem_kib = info["memory_kib"]

    print(cyan(f"\nSelected: {xml_path}"))
    print(green(f"Current vcpu: {cur_vcpu}"))
    print(green(f"Current memory: {cur_mem_mb} MB ({cur_mem_kib} KiB)"))

    default_vcpu = str(cur_vcpu) if cur_vcpu is not None else "2"
    default_mem_mb = str(cur_mem_mb) if cur_mem_mb is not None else "2048"

    new_vcpu = int(
        get_input(
            r"^\d+$",
            f"vcpu count (Default: {default_vcpu}): ",
            "invalid format",
            default_vcpu,
        )
    )
    new_memory_mb = int(
        get_input(
            r"^\d+$",
            f"Memory in MByte (Default: {default_mem_mb} MB): ",
            "invalid format",
            default_mem_mb,
        )
    )

    edit_vm_xml(
        session,
        xml_path,
        vcpu=new_vcpu,
        memory_mb=new_memory_mb,
        define=True,
        sudo=sudo,
    )

    updated = get_vcpu_and_memory(session, xml_path, sudo=sudo)
    print(
        cyan(
            f"Updated {os.path.basename(xml_path)}: "
            f"vcpu={updated['vcpu']}, memory={updated['memory_mb']} MB ({updated['memory_kib']} KiB)"
        )
    )
