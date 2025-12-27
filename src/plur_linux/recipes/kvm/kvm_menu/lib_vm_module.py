from mini.ansi_colors import blue, green
from mini.menu import choose_num
from plur_linux.nodes.guests import dock, a8images, a9images, gluster, kubeadm_a9, images_ubu
vm_nodes = [
    ['a8images', a8images],
    ['a9images', a9images],
    # ['ubu_images', images_ubu],
    ['dock', dock],
    ['gluster', gluster],
    ['kubeadm_a9', kubeadm_a9],
]


def select_vm_history(selection):
    num = choose_num([vm[0] for vm in vm_nodes], blue("Please select VM"))
    selected_module = vm_nodes[num]
    selected_module_list = selected_module[1].create_nodes()
    vm_num = choose_num([mod[0] for mod in selected_module_list])
    selected_vm_module = selected_module_list[vm_num]
    print(green(f'vm: VM module: {selected_module[0]} > {selected_vm_module[0]}'))
    selection.append({'key': 'vm_module', 'index': [num, vm_num]})
    return selected_vm_module[1]()


def extract_vm(vm_module):
    index = vm_module['index']
    num = index[0]
    selected_module = vm_nodes[num]
    selected_vm_module = selected_module[1].create_nodes()[index[1]]
    print(green(f'vm: VM module: {selected_module[0]} > {selected_vm_module[0]}'))
    return selected_vm_module[1]()
