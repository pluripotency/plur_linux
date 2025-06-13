from plur.base_shell import *
from plur import session_wrap
from plur_linux.recipes import ipv4
from . import ldap_server


def create_f5_subnets(subnet_list):
    translated_subnet_list = []
    for subnet in subnet_list:
        sp = subnet.split('/')
        translated = sp[0] + '/' + ipv4.prefix_to_netmask(sp[1])
        translated_subnet_list.append(translated)
    return ' '.join(translated_subnet_list)


def create_dns_xml(dns_list):
    """
    vpnDns
    >>> create_dns_xml(['192.168.10.1', '8.8.8.8'])
    '<dns><dns_primary>192.168.10.1</dns_primary><dns_secondary>8.8.8.8</dns_secondary></dns>'
    """
    xml = ''
    if isinstance(dns_list, list) and 1 <= len(dns_list) <= 3:
        xml += '<dns>'
        for i, dns in enumerate(dns_list):
            if i == 0:
                xml += f'<dns_primary>{dns}</dns_primary>'
            elif i == 1:
                xml += f'<dns_secondary>{dns}</dns_secondary>'
        xml += '</dns>'
    return xml


def create_include_dns_name_xml(dns_name_list):
    """
    vpnAddressSpaceIncludeDnsName
    >>> create_include_dns_name_xml(['*.vpn.local', '*.vpn.go.local'])
    '<address_space_include_dns_name><item><dnsname>*.vpn.local</dnsname></item><item><dnsname>*.vpn.go.local</dnsname></item></address_space_include_dns_name>'
    """
    xml = ''
    if isinstance(dns_name_list, list) and 1 <= len(dns_name_list):
        xml += '<address_space_include_dns_name>'
        for i, dns_name in enumerate(dns_name_list):
            xml += f'<item><dnsname>{dns_name}</dnsname></item>'
        xml += '</address_space_include_dns_name>'
    return xml


def create_vpn_group_dict(gid_number, vpn_name, leasepool_name, subnet_list, dns_list, dns_suffix, include_dnsname_list, split_tunnel, snat, route_domain):
    if split_tunnel == 'true':
        ldif_dict = {
            'cn': vpn_name,
            'gidNumber': gid_number,
            'vpnName': vpn_name,
            'vpnLeasePoolName': '/Common/' + leasepool_name,
            'vpnAddressSpaceIncludeSubnet': create_f5_subnets(subnet_list),
            'vpnDns': create_dns_xml(dns_list),
            'vpnDnsSuffix': dns_suffix,
            'vpnAddressSpaceIncludeDnsName': create_include_dns_name_xml(include_dnsname_list),
            'vpnSplitTunneling': '1',
            'vpnSnatType': snat,
            'vpnRouteDomain': route_domain,
        }
    else:
        ldif_dict = {
            'cn': vpn_name,
            'gidNumber': gid_number,
            'vpnName': vpn_name,
            'vpnLeasePoolName': '/Common/' + leasepool_name,
            'vpnAddressSpaceIncludeSubnet': '128.0.0.0/128.0.0.0 0.0.0.0/128.0.0.0',
            'vpnAddressSpaceExcludeSubnet': '',
            'vpnDns': create_dns_xml(dns_list),
            'vpnDnsSuffix': dns_suffix,
            'vpnAddressSpaceIncludeDnsName': '',
            'vpnSplitTunneling': '0',
            'vpnSnatType': snat,
            'vpnRouteDomain': route_domain,
        }
    return ldif_dict


def create_vpn_group_ldif_lines(olc_suffix, group, member_list, group_ou='Group'):
    cn = group['cn']
    gid_number = group['gidNumber']
    contents = [
        f'dn: cn={cn},ou={group_ou},{olc_suffix}',
        'objectClass: posixGroup',
        'objectClass: vpnprofile',
    ]
    contents += [
        f'cn: {cn}',
        f'gidNumber: {gid_number}',

        f'vpnName: {group["vpnName"]}',
        f'vpnAddressSpaceIncludeDnsName: {group["vpnAddressSpaceIncludeDnsName"]}',
        f'vpnAddressSpaceIncludeSubnet: {group["vpnAddressSpaceIncludeSubnet"]}',
        f'vpnSplitTunneling: {group["vpnSplitTunneling"]}',
        f'vpnSnatType: {group["vpnSnatType"]}',
        f'vpnLeasePoolName: {group["vpnLeasePoolName"]}',
        f'vpnDns: {group["vpnDns"]}',
        f'vpnDnsSuffix: {group["vpnDnsSuffix"]}',
        f'vpnRouteDomain: {group["vpnRouteDomain"]}',
    ]
    if 'vpnAddressSpaceExcludeSubnet' in group:
        contents += [
            f'vpnAddressSpaceExcludeSubnet: {group["vpnAddressSpaceExcludeSubnet"]}',
        ]
    for member in member_list:
        contents += [f'memberUid: {member}']
    contents += ['']
    return contents


def create_all_delete_ldif_sh_lines(bind_dn, bind_dn_credential, olc_suffix):
    # create ldif for deleting all ou=Group,{olc_suffix} children
    return [
        '#! /bin/sh',
        '# Usage: sh create_all_delete_ldif.sh [all delete ldif file path]',
        f'ldapsearch -LLL -b "ou=Group,{olc_suffix}" -D "{bind_dn}" -w {bind_dn_credential} "(cn=*)" attribute dn \\',
        r"    | grep Group | sed '/^dn: cn=.*,ou=Group,.*/a changetype:delete\n' > ${1}",
        ''
    ]


def create_register_sh_lines(bind_dn, bind_dn_credential):
    return [
        '#! /bin/sh',
        '# Usage: sh register.sh [adding ldif file path]',
        f'ldapadd -x -D "{bind_dn}" -w {bind_dn_credential} -f $1',
        ''
    ]


def ldapadd_ldif(bind_dn, bind_dn_credential, ldif_path):
    def func(session):
        run(session, f'ldapadd -x -D "{bind_dn}" -w {bind_dn_credential} -f {ldif_path}')
    return func


def add_vpn_group(bind_dn, bind_dn_credential, olc_suffix, group, member_list):
    def func(session):
        gid_number = group['gidNumber']
        contents = create_vpn_group_ldif_lines(olc_suffix, group, member_list)
        ldif = f'{gid_number}.ldif'
        here_doc(session, ldif, contents, eof='EOF')
        run(session, f'ldapadd -x -D "{bind_dn}" -w {bind_dn_credential} -f {ldif}')
    return func


def check_vpn_group(bind_dn, bind_dn_credential, olc_suffix, member_list, enable_ssl, group_ou='Group'):
    """
    example:
    ldapsearch -LLL -x -D "cn=manager,dc=example,dc=org" -b "dc=example,dc=org" -w managerpass "memberUid=user001"
    """
    actions = []
    for member in member_list:
        action = f'ldapsearch -LLL -x -D "{bind_dn}" -b "ou={group_ou},{olc_suffix}" "memberUid={member}" -w {bind_dn_credential}'
        action += ' -H ldaps:///' if enable_ssl else ''
        actions += [action]

    def func(session):
        [run(session, a) for a in actions]
    return func


@session_wrap.sudo
def register_vpn_schema(session):
    cwd = os.path.dirname(__file__)
    profile = 'vpnprofile.ldif'
    heredoc_from_local(f'{cwd}/{profile}', f'/tmp/{profile}')(session)

    [run(session, a) for a in [
        f'ldapadd -Y EXTERNAL -H ldapi:/// -f /tmp/{profile}'
    ]]


olc_suffix_example = 'dc=test,dc=vpn'
vpn_ldap_params_example = {
    'organization': 'TED',
    'bindDN': 'cn=manager,' + olc_suffix_example,
    'bindDNCredential': 'managerpass',
    'olcRootPW': 'managerpass',
    'olcSuffix': olc_suffix_example,
    'enable_ssl': True,
    # 'enable_ssl': False,
}
vpn_cert_params = {
    'country_name': 'JP',
    'state': 'Tokyo',
    'city': 'Shinjuku',
    'organization': 'TED',
    'org_unit': 'std',
    'common_name': 'ldaps.local',
    'email': '',
}
vpn_group_list = [
    { # split-tunnel
        'gid_number': '1001',
        'vpn_name': 'vpn_1001',
        'leasepool_name': 'test_lp',
        'subnet_list': ['172.31.0.0/18'],
        'dns_list': ['172.31.63.53', '8.8.4.4'],
        'dns_suffix': 'v1001.vpn.local',
        'include_dnsname_list': ['*.vpn.local', '*.vpn.go.local'],
        'split_tunnel': 'true',  # enable
        'snat': '3',  # auto

        'route_domain': '1',
    },
    { # no split-tunnel
        'gid_number': '1002',
        'vpn_name': 'vpn_1002',
        # 'leasepool_name': 'NetAccess-000_lp',
        'leasepool_name': 'test2_lp',
        'subnet_list': ['0.0.0.0/1', '128.0.0.0/1'],
        'dns_list': ['192.168.10.1', '8.8.8.8'],
        'dns_suffix': 'v1002.vpn.local',
        'include_dnsname_list': ['*'],
        'split_tunnel': '', # disable
        'snat': '3', # auto

        'route_domain': '2',
    },
]


def setup(ldap_params=None, cert_params=None, enable_syslog=True, check=True):
    if ldap_params is None:
        ldap_params = vpn_ldap_params_example

    bind_dn = ldap_params['bindDN']
    bind_dn_credential = ldap_params['bindDNCredential']
    olc_suffix = ldap_params['olcSuffix'] if 'olcSuffix' in ldap_params else ','.join(bind_dn.split(',')[1:])
    enable_ssl = ldap_params['enable_ssl'] if 'enable_ssl' in ldap_params else False
    if enable_ssl and cert_params == None:
        cert_params = vpn_cert_params

    def func(session):
        ldap_server.setup(ldap_params, cert_params, [], enable_syslog)(session)
        register_vpn_schema(session)
        if check:
            group1 = vpn_group_list[0]
            ldif_dict1 = create_vpn_group_dict(**group1)
            add_vpn_group(bind_dn, bind_dn_credential, olc_suffix, ldif_dict1, ['user001', 'user003'])(session)

            group2 = vpn_group_list[1]
            ldif_dict2 = create_vpn_group_dict(**group2)
            add_vpn_group(bind_dn, bind_dn_credential, olc_suffix, ldif_dict2, ['user002', 'user004', 'ted'])(session)

            check_vpn_group(bind_dn, bind_dn_credential, olc_suffix, ['user001', 'user002'], enable_ssl)(session)

    return func




