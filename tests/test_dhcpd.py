import ipaddress
import unittest
from plur_linux.recipes.pxe import dhcpd


class TestDhcpd(unittest.TestCase):

    def test_calc_dhcp_range_24(self):
        net = ipaddress.IPv4Network('192.168.0.0/24')
        start_ip, end_ip = dhcpd.calc_dhcp_range(net)
        self.assertEqual(start_ip, '192.168.0.192')
        self.assertEqual(end_ip, '192.168.0.250')

        # Check exclusion of last 4 host IPs and broadcast
        start_addr = ipaddress.IPv4Address(start_ip)
        end_addr = ipaddress.IPv4Address(end_ip)
        for excluded in ['192.168.0.251', '192.168.0.252', '192.168.0.253', '192.168.0.254', '192.168.0.255']:
            excluded_addr = ipaddress.IPv4Address(excluded)
            self.assertFalse(start_addr <= excluded_addr <= end_addr)

    def test_calc_dhcp_range_22(self):
        net = ipaddress.IPv4Network('172.16.0.0/22')
        start_ip, end_ip = dhcpd.calc_dhcp_range(net)
        self.assertEqual(start_ip, '172.16.3.0')
        self.assertEqual(end_ip, '172.16.3.250')

    def test_calc_dhcp_range_16(self):
        net = ipaddress.IPv4Network('10.0.0.0/16')
        start_ip, end_ip = dhcpd.calc_dhcp_range(net)
        self.assertEqual(start_ip, '10.0.192.0')
        self.assertEqual(end_ip, '10.0.255.250')

    def test_calc_dhcp_range_small_subnet_fallback(self):
        # /29 subnet has only 8 addresses
        net = ipaddress.IPv4Network('192.168.1.0/29')
        start_ip, end_ip = dhcpd.calc_dhcp_range(net)
        # Should fallback to usable range
        self.assertEqual(start_ip, '192.168.1.1')
        self.assertEqual(end_ip, '192.168.1.6')

    def test_find_segment_for_ip(self):
        mock_segments = [
            {
                'type': 'default',
                'net_source': 'default',
                'network_with_prefix': '192.168.122.0/24',
                'gateway_seed': '1',
                'search': 'local',
                'nameservers': '192.168.122.1',
            },
            {
                'type': 'bridge',
                'net_source': 'br0',
                'network_with_prefix': '10.20.0.0/16',
                'gateway_seed': '1',
                'search': 'corp.local',
                'nameservers': '10.20.0.1, 8.8.8.8',
            }
        ]
        # IP in segment 1
        seg = dhcpd.find_segment_for_ip('192.168.122.50', segments=mock_segments)
        self.assertIsNotNone(seg)
        self.assertEqual(seg['net_source'], 'default')

        # IP with prefix
        seg_prefix = dhcpd.find_segment_for_ip('192.168.122.50/24', segments=mock_segments)
        self.assertEqual(seg_prefix, seg)

        # IP in segment 2
        seg2 = dhcpd.find_segment_for_ip('10.20.5.10', segments=mock_segments)
        self.assertIsNotNone(seg2)
        self.assertEqual(seg2['net_source'], 'br0')

        # IP not in any segment
        seg_none = dhcpd.find_segment_for_ip('172.16.1.1', segments=mock_segments)
        self.assertIsNone(seg_none)

        # Invalid IP
        seg_invalid = dhcpd.find_segment_for_ip('invalid-ip', segments=mock_segments)
        self.assertIsNone(seg_invalid)

    def test_create_subnet_params_from_segment(self):
        segment = {
            'type': 'bridge',
            'net_source': 'br0',
            'network_with_prefix': '192.168.50.0/24',
            'gateway_seed': '1',
            'search': 'lab.local',
            'nameservers': '192.168.50.1',
        }
        params = dhcpd.create_subnet_params_from_segment(segment)
        self.assertEqual(params['subnet'], '192.168.50.0')
        self.assertEqual(params['netmask'], '255.255.255.0')
        self.assertEqual(params['gateway'], '192.168.50.1')
        self.assertEqual(params['nameservers'], '192.168.50.1')
        self.assertEqual(params['dh_range'], '192.168.50.192 192.168.50.250')
        self.assertEqual(params['broadcast'], '192.168.50.255')
        self.assertEqual(params['domain_name'], 'lab.local')
        self.assertEqual(params['domain_name_servers'], '192.168.50.1')
        self.assertEqual(params['allowed_net'], '192.168.50.0/24')

    def test_get_subnet_params_with_dict(self):
        segment = {
            'type': 'default',
            'net_source': 'default',
            'network_with_prefix': '192.168.122.0/24',
            'gateway_seed': '1',
            'search': 'local',
            'nameservers': '192.168.122.1',
        }
        params = dhcpd.get_subnet_params(segment=segment)
        self.assertEqual(params['subnet'], '192.168.122.0')
        self.assertEqual(params['dh_range'], '192.168.122.192 192.168.122.250')

    def test_get_subnet_params_with_str(self):
        mock_segments = [
            {
                'type': 'bridge',
                'net_source': 'br0',
                'network_with_prefix': '10.0.0.0/24',
                'gateway_seed': '1',
                'search': 'local',
                'nameservers': '10.0.0.1',
            }
        ]
        params = dhcpd.get_subnet_params(segment='br0', segments=mock_segments)
        self.assertEqual(params['subnet'], '10.0.0.0')
        self.assertEqual(params['dh_range'], '10.0.0.192 10.0.0.250')

    def test_get_subnet_params_by_matching_pxe_ip(self):
        mock_segments = [
            {
                'type': 'bridge',
                'net_source': 'br0',
                'network_with_prefix': '172.25.0.0/24',
                'gateway_seed': '1',
                'search': 'local',
                'nameservers': '172.25.0.1',
            }
        ]
        params = dhcpd.get_subnet_params(pxe_ip='172.25.0.100', segments=mock_segments)
        self.assertEqual(params['subnet'], '172.25.0.0')
        self.assertEqual(params['dh_range'], '172.25.0.192 172.25.0.250')

    def test_get_subnet_params_fallback(self):
        # Fallback for 192.168.0.x
        params0 = dhcpd.get_subnet_params(pxe_ip='192.168.0.150', segments=[])
        self.assertEqual(params0['subnet'], '192.168.0.0')
        self.assertEqual(params0['dh_range'], '192.168.0.192 192.168.0.250')

        # Fallback for 192.168.10.x
        params10 = dhcpd.get_subnet_params(pxe_ip='192.168.10.150', segments=[])
        self.assertEqual(params10['subnet'], '192.168.10.0')
        self.assertEqual(params10['dh_range'], '192.168.10.192 192.168.10.250')

        # Dynamic fallback for arbitrary IP
        params_custom = dhcpd.get_subnet_params(pxe_ip='10.50.60.70', segments=[])
        self.assertEqual(params_custom['subnet'], '10.50.60.0')
        self.assertEqual(params_custom['dh_range'], '10.50.60.192 10.50.60.250')

    def test_create_pxe_dhcp_conf_str_content(self):
        segment = {
            'type': 'bridge',
            'net_source': 'br0',
            'network_with_prefix': '192.168.100.0/24',
            'gateway_seed': '1',
            'search': 'custom.domain',
            'nameservers': '192.168.100.1',
        }
        params = dhcpd.create_subnet_params_from_segment(segment)
        conf = dhcpd.create_pxe_dhcp_conf_str('192.168.100.10', params)

        self.assertIn('option domain-name     "custom.domain";', conf)
        self.assertIn('option domain-name-servers     192.168.100.1;', conf)
        self.assertIn('subnet 192.168.100.0 netmask 255.255.255.0 {', conf)
        self.assertIn('range dynamic-bootp        192.168.100.192 192.168.100.250;', conf)
        self.assertIn('option routers             192.168.100.1;', conf)
        self.assertIn('next-server 192.168.100.10;', conf)
        self.assertIn('filename "BOOTX64.EFI";', conf)
        self.assertIn('filename "pxelinux.0";', conf)


if __name__ == '__main__':
    unittest.main()
