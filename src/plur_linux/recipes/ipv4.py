import re
mask_list = [
    '0',  # 0
    '128',  # 1
    '192',  # 2
    '224',  # 3
    '240',  # 4
    '248',  # 5
    '252',  # 6
    '254',  # 7
    '255',  # 8
]
ipv4_exp_str = '((1[0-9][0-9]|[1-9]?[0-9]|2[0-4][0-9]|25[0-5])\.){3}(1[0-9][0-9]|[1-9]?[0-9]|2[0-4][0-9]|25[0-5])'
ipv4_with_prefix_exp_str = ipv4_exp_str + '/(1[0-9]|2[0-9]|3[0-2]|[0-9])'


def is_ipv4(may_ipv4_str):
    return re.search('^' + ipv4_exp_str + '$', may_ipv4_str)


def is_ipv4_with_prefix(may_ipv4_with_prefix_str):
    return re.search('^' + ipv4_with_prefix_exp_str + '$', may_ipv4_with_prefix_str)


def prefix_to_netmask(prefix):
    """
    >>> prefix_to_netmask('16')
    '255.255.0.0'
    >>> prefix_to_netmask('20')
    '255.255.240.0'
    >>> prefix_to_netmask('1')
    '128.0.0.0'
    >>> prefix_to_netmask('0')
    '0.0.0.0'
    >>> prefix_to_netmask('32')
    '255.255.255.255'
    """
    if re.match('\d{1,2}', prefix):
        int_prefix = int(prefix)
        if 0 <= int_prefix <= 32:
            sho = int_prefix // 8
            mod = int_prefix % 8
            subnet_mask = ''
            for i in range(sho):
                subnet_mask += '.255'
            for j, k in enumerate(range(4-sho)):
                if j == 0:
                    subnet_mask += f'.{mask_list[mod]}'
                else:
                    subnet_mask += '.0'
            return subnet_mask[1:]
    print(f'err invalid prefix: {prefix}')
    exit(1)


def find_index(value_list, value):
    for index, item in enumerate(value_list):
        if item == value:
            return index
    print(f'err could not find index from value_list')
    exit(1)


def netmask_to_prefix(netmask):
    """
    >>> netmask_to_prefix('255.255.255.248')
    '29'
    >>> netmask_to_prefix('255.255.192.0')
    '18'
    """
    if re.match(r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}', netmask):
        adder = 0
        for seg in  netmask.split('.'):
            adder += find_index(mask_list, seg)
        return str(adder)


