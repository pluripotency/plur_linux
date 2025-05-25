import json
from misc import misc
from plur import base_shell
from plur import ansi_colors
from .esx_cli_str import *
from recipes.vmware import parser
from recipes import ipv4


def add_vswitch_obj_str_list(vswitch_dict):
    vswitch = vswitch_dict['vswitch']
    pgroup_list = vswitch_dict['portgroup-list']
    vmnic_list =vswitch_dict['vmnic-list']
    actions = [
        add_standard_vswitch_str(vswitch),
    ]
    for pgroup in pgroup_list:
        actions += [add_portgroup_str(pgroup, vswitch)]
    for vmnic in vmnic_list:
        actions += [add_vmnic_str(vmnic, vswitch)]
    return actions


def remove_vsitch_obj_str(vswitch_dict):
    vswitch = vswitch_dict['vswitch']
    return remove_standard_vswitch_str(vswitch)


def create_from_summary(summary_json):
    """
    >>> import json
    >>> create_from_summary(json.loads(ex_summary_json))

    :param summary_json:
    :return:
    """
    commands = []
    for vswitch_obj in summary_json:
        vswitch_name = vswitch_obj['vswitch_name']
        commands += [
            remove_standard_vswitch_str(vswitch_name),
            add_standard_vswitch_str(vswitch_name),
            set_starndard_vswitch_policy_security_str(vswitch_name)
        ]
        if 'portgroup_list' in vswitch_obj:
            for portgroup_line in vswitch_obj['portgroup_list']:
                sp = re.split(' vid:', portgroup_line)
                portgroup = sp[0]
                vid = sp[1]
                commands += [
                    add_portgroup_str(portgroup, vswitch_name),
                    set_vid_to_portgroup_str(vid, portgroup),
                ]
        if 'vmnic_list' in vswitch_obj:
            for vmnic_line in vswitch_obj['vmnic_list']:
                sp = re.split(' ', vmnic_line)
                vmnic = sp[0]
                commands += [
                    add_vmnic_str(vmnic, vswitch_name)
                ]
    return commands


def create_vswitch_list_from_vswitch_obj_list(vswitch_obj_list):
    return [obj['vswitch_name'] for obj in vswitch_obj_list]


def get_current_configured_vswitch_list(session):
    vswitch_list_output = base_shell.run(session, show_vswitch_standard_list_str())
    vswitch_obj_list = parser.parse_list_standard_switch(vswitch_list_output)
    return create_vswitch_list_from_vswitch_obj_list(vswitch_obj_list)


def configure_vswitch_from_conf_json(conf_json, overwrite=False):
    def func(session):
        current_configured_vswitch_list = get_current_configured_vswitch_list(session)
        conf_vswitch_list = create_vswitch_list_from_vswitch_obj_list(conf_json)
        found = misc.find(conf_vswitch_list, lambda conf_vsw: conf_vsw in current_configured_vswitch_list)
        if found and not overwrite:
            print(ansi_colors.red('err: abort by found configured vswitch in conf.json'))
            return
        commands = []
        for vswitch_obj in conf_json:
            vswitch_name = vswitch_obj['vswitch_name']
            if overwrite:
                commands += [
                    remove_standard_vswitch_str(vswitch_name),
                ]
            commands += [
                add_standard_vswitch_str(vswitch_name),
                set_starndard_vswitch_policy_security_str(vswitch_name)
            ]
            if 'portgroup_list' in vswitch_obj:
                for portgroup_line in vswitch_obj['portgroup_list']:
                    [
                        portgroup
                        , vid
                        , vmk
                    ] = parser.parse_vswitch_obj_portgroup(portgroup_line)
                    commands += [
                        add_portgroup_str(portgroup, vswitch_name),
                        set_vid_to_portgroup_str(vid, portgroup),
                    ]
                    if vmk:
                        vmk_name = vmk['name']
                        sp = vmk['ip'].split('/')
                        vmk_ip = sp[0]
                        vmk_netmask = ipv4.prefix_to_netmask(sp[1])
                        commands += add_vmkernel_to_portgroup_str_list(portgroup, vmk_name, vmk_ip, vmk_netmask)

            if 'vmnic_list' in vswitch_obj:
                for vmnic_line in vswitch_obj['vmnic_list']:
                    sp = re.split(' ', vmnic_line)
                    vmnic = sp[0]
                    commands += [
                        add_vmnic_str(vmnic, vswitch_name)
                    ]
        [base_shell.run(session, cmd) for cmd in commands]

    return func


def capture_configred_vswitch(local_save_dir):
    def func(session):
        misc.prepare_clean_dir(local_save_dir)
        output_dir = f'{local_save_dir}/output'
        misc.prepare_clean_dir(output_dir)
        summary_dir = f'{local_save_dir}/summary'
        misc.prepare_clean_dir(summary_dir)

        vswitch_list_output = base_shell.run(session, show_vswitch_standard_list_str())
        misc.open_write(f'{output_dir}/vswitch_list.txt', vswitch_list_output)
        list_switch = parser.parse_list_standard_switch(vswitch_list_output)
        misc.open_write(f'{summary_dir}/vswitch_list.json', json.dumps(list_switch, indent=2))

        vswitch_obj_list = parser.parse_list_standard_switch(vswitch_list_output)
        for vswitch_obj in vswitch_obj_list:
            vswitch_name = vswitch_obj['vswitch_name']
            vswitch_security_output = base_shell.run(session, show_standard_vswitch_policy_security_str(vswitch_name))
            misc.open_write(f'{output_dir}/vswitch_security_{misc.sanitize_to_file_name(vswitch_name)}.txt', vswitch_security_output)

        ip_interface_list_output = base_shell.run(session, show_ip_interface_list_str())
        misc.open_write(f'{output_dir}/ip_interface_list.txt', ip_interface_list_output)
        list_ip_interface = parser.parse_list_ip_interface(ip_interface_list_output)
        misc.open_write(f'{summary_dir}/ip_interface_list.json', json.dumps(list_ip_interface, indent=2))

        vmk_ip_list_output = base_shell.run(session, show_vmk_ip_list_str())
        misc.open_write(f'{output_dir}/vmk_ip_list.txt', vmk_ip_list_output)
        list_vmk_ip = parser.parse_list_vmk_ip(vmk_ip_list_output)
        misc.open_write(f'{summary_dir}/vmk_ip_list.json', json.dumps(list_vmk_ip, indent=2))

        portgroup_list_output = base_shell.run(session, show_portgroup_list_str())
        misc.open_write(f'{output_dir}/portgroup_list.txt', portgroup_list_output)
        list_portgroup = parser.parse_list_portgroup(portgroup_list_output)
        misc.open_write(f'{summary_dir}/portgroup_list.json', json.dumps(list_portgroup, indent=2))

        vmnic_list_output = base_shell.run(session, show_vmnic_list_str())
        misc.open_write(f'{output_dir}/vmnic_list.txt', vmnic_list_output)
        list_vmnic = parser.parse_list_vmnic(vmnic_list_output)
        misc.open_write(f'{summary_dir}/vmnic_list.json', json.dumps(list_vmnic, indent=2))

        vm_list_output = base_shell.run(session, show_vm_list_str())
        misc.open_write(f'{output_dir}/vm_list.txt', vm_list_output)

        conf_result = parser.summary_parsed(list_switch, list_portgroup, list_vmnic, list_ip_interface, list_vmk_ip)
        misc.open_write(f'{summary_dir}/conf_result.json', json.dumps(conf_result, indent=2))
    return func



