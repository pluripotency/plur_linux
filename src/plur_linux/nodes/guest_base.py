#! /usr/bin/env python
micro = {
    'vcpu': 1,
    'vmem': 512
}
small = {
    'vcpu': 2,
    'vmem': 1024
}
medium = {
    'vcpu': 2,
    'vmem': 2048
}
kvm = {
    'platform': 'centos7',
}
c7base = {
    'org_xml': 'rhel7.xml',
    'org_hostname': 'localhost',
    'platform': 'centos7',
    'diskformat': 'qcow2',
}

