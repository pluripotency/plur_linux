import re


ex_disp_vlan_all = """

 VLAN ID: 1
 VLAN Type: static              
 Route Interface: n/a    
 Description: VLAN 0001
 Name: DEFAULT_VLAN                    
 Tagged   Ports: none                    
 Untagged Ports: 
    1         2         3         
    4         5         6         
    7         8         9         
    10        11        12        
    13        14        15        
    16        17        18        
    19        20        21        
    22        23        24        
    25        26        27        
    28        Trk1                          

 VLAN ID: 777
 VLAN Type: static              
 Route Interface: n/a    
 Description: VLAN 0777
 Name: VLAN777                    
 Tagged   Ports: none                    
 Untagged Ports: none                    

 VLAN ID: 999
 VLAN Type: static              
 Route Interface: n/a    
 Description: VLAN 0999
 Name: VLAN999                    
 Tagged   Ports: none                    
 Untagged Ports: none                    

 VLAN ID: 4084
 VLAN Type: static              
 Route Interface: n/a    
 IP Address: 192.168.10.63       
 Subnet Mask: 255.255.255.0       
 Description: VLAN 4084
 Name: VLAN4084                    
 Tagged   Ports: 
    1                             
 Untagged Ports: none                    



"""


def parse_disp_vlan_all(output, simple=True):
    """
    >>> parse_disp_vlan_all(ex_disp_vlan_all, False)
    [{'vlan_id': '1', 'vlan_type': 'static', 'route_interface': 'n/a', 'tag_ports': [], 'unt_ports': ['1', '2', '3', '4', '5', '6', '7', '8', '9', '10', '11', '12', '13', '14', '15', '16', '17', '18', '19', '20', '21', '22', '23', '24', '25', '26', '27', '28', 'Trk1'], 'name': 'DEFAULT_VLAN', 'description': 'VLAN 0001'}, {'vlan_id': '777', 'vlan_type': 'static', 'route_interface': 'n/a', 'tag_ports': [], 'unt_ports': [], 'name': 'VLAN777', 'description': 'VLAN 0777'}, {'vlan_id': '999', 'vlan_type': 'static', 'route_interface': 'n/a', 'tag_ports': [], 'unt_ports': [], 'name': 'VLAN999', 'description': 'VLAN 0999'}, {'vlan_id': '4084', 'vlan_type': 'static', 'route_interface': 'n/a', 'tag_ports': ['1'], 'unt_ports': [], 'name': 'VLAN4084', 'description': 'VLAN 4084', 'ip_address': '192.168.10.63', 'subnet_mask': '255.255.255.0'}]

    """
    in_conf = False
    in_tag = False
    in_unt = False

    vlan_id = None
    vlan_type = None
    route_interface = None
    ip_address = None
    subnet_mask = None
    description = None
    name = None
    tagged = []
    untagged = []

    if isinstance(output, str) and len(output) > 1:
        conf_list = []
        for line in re.split('\r\n|\n', output):
            if line == '':
                if in_conf:
                    if simple:
                        obj = {
                            'vlan_id': vlan_id,
                            'tag_ports': tagged,
                            'unt_ports': untagged,
                        }
                    else:
                        obj = {
                            'vlan_id': vlan_id,
                            'vlan_type': vlan_type,
                            'route_interface': route_interface,
                            'tag_ports': tagged,
                            'unt_ports': untagged,
                            'name': name,
                            'description': description,
                        }
                    if ip_address:
                        obj['ip_address'] = ip_address
                        obj['subnet_mask'] = subnet_mask

                    conf_list += [obj]
                    in_conf = False
                    in_tag = False
                    in_unt = False

                    vlan_id = None
                    vlan_type = None
                    route_interface = None
                    ip_address = None
                    subnet_mask = None
                    description = None
                    name = None
                    tagged = []
                    untagged = []

            elif re.search('^ VLAN ID: ', line):
                vlan_id = line.split('ID: ')[1].strip()
                in_conf = True
            elif re.search('^ VLAN Type: ', line):
                vlan_type = line.split('Type: ')[1].strip()
            elif re.search('^ Route Interface: ', line):
                route_interface = line.split('face: ')[1].strip()
            elif re.search('^ Description: ', line):
                description = line.split('Description: ')[1].strip()
            elif re.search('^ Name: ', line):
                name = line.split('Name: ')[1].strip()
            elif re.search('^ IP Address: ', line):
                ip_address = line.split('Address: ')[1].strip()
            elif re.search('^ Subnet Mask: ', line):
                subnet_mask = line.split('Mask: ')[1].strip()
            elif re.search('^ Tagged   Ports: ', line):
                in_tag = True
                in_unt = False
            elif re.search('^ Untagged Ports: ', line):
                in_tag = False
                in_unt = True
            elif line.startswith('  '):
                sp = line.split()
                if in_unt:
                    untagged += sp
                elif in_tag:
                    tagged += sp

        return conf_list


