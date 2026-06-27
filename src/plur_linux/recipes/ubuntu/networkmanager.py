from plur import base_shell
from plur_linux.recipes.ubuntu import ops

def change_netplan_to_networkmanager(session):
    ops.sudo_apt_install_y(['network-manager'])(session)
    oneliner = "sudo sed -i.bak 's/renderer:\s*networkd/renderer: NetworkManager/g' /etc/netplan/*.yaml && sudo netplan apply"
    base_shell.run(session, oneliner)
    # dir_path = '/etc/netplan'
    # base_shell.run(session, 'cd ' + dir_path)
    # tmp_file_list = '/tmp/netplan_file_list.txt'
    # base_shell.run(session, f'ls | grep yaml | cat > {tmp_file_list}')
    #
    # judge_nm = f'cat {tmp_file_list} | ' + 'xargs -I{} '
    # judge_nm += base_shell.grep_exist_pattern_str('{}', 'renderer: networkd')
    # judge_nm += ' && ' + base_shell.sed_replace_str('  renderer: networkd', '  renderer: NetworkManager', '{}')
    #
    # base_shell.run(session, judge_nm)
    # base_shell.run(session, 'netplan apply')
