import unittest
from unittest.mock import patch
from plur_linux.lib.ip_calc import calc_ip, get_segment_network, get_ip_from_segment, IPRangeError


class TestIPCalc(unittest.TestCase):
    def test_calc_ip_slash_22(self):
        net = "172.16.0.0/22"

        # int seed
        self.assertEqual(calc_ip(net, 1), "172.16.0.1")
        self.assertEqual(calc_ip(net, 261), "172.16.1.5")

        # str seed with dot notation
        self.assertEqual(calc_ip(net, "1.5"), "172.16.1.5")
        self.assertEqual(calc_ip(net, "0.1"), "172.16.0.1")
        self.assertEqual(calc_ip(net, "3.254"), "172.16.3.254")

        # Range errors (Option B: network and broadcast addresses are also errors)
        self.assertEqual(calc_ip(net, "4.1"), "IP Range Error")
        self.assertEqual(calc_ip(net, 0), "IP Range Error")
        self.assertEqual(calc_ip(net, "0.0"), "IP Range Error")
        self.assertEqual(calc_ip(net, "3.255"), "IP Range Error")
        self.assertEqual(calc_ip(net, 1023), "IP Range Error")
        self.assertEqual(calc_ip(net, 1024), "IP Range Error")
        self.assertEqual(calc_ip(net, -1), "IP Range Error")

    def test_calc_ip_slash_24(self):
        net = "192.168.122.0/24"

        self.assertEqual(calc_ip(net, 1), "192.168.122.1")
        self.assertEqual(calc_ip(net, 100), "192.168.122.100")
        self.assertEqual(calc_ip(net, "100"), "192.168.122.100")
        self.assertEqual(calc_ip(net, "254"), "192.168.122.254")

        # In /24, '1.5' is out of range
        self.assertEqual(calc_ip(net, "1.5"), "IP Range Error")
        self.assertEqual(calc_ip(net, 0), "IP Range Error")
        self.assertEqual(calc_ip(net, 255), "IP Range Error")

    def test_calc_ip_with_prefix(self):
        net = "172.16.0.0/22"
        self.assertEqual(calc_ip(net, "1.5", with_prefix=True), "172.16.1.5/22")
        self.assertEqual(calc_ip(net, 1, with_prefix=True), "172.16.0.1/22")
        self.assertEqual(calc_ip(net, "4.1", with_prefix=True), "IP Range Error")

    def test_calc_ip_full_ip(self):
        net = "172.16.0.0/22"
        self.assertEqual(calc_ip(net, "172.16.1.5"), "172.16.1.5")
        self.assertEqual(calc_ip(net, "172.16.0.0"), "IP Range Error")  # network address
        self.assertEqual(calc_ip(net, "172.16.3.255"), "IP Range Error")  # broadcast
        self.assertEqual(calc_ip(net, "172.16.4.1"), "IP Range Error")
        self.assertEqual(calc_ip(net, "192.168.1.1"), "IP Range Error")

    def test_calc_ip_dhcp(self):
        net = "172.16.0.0/22"
        self.assertEqual(calc_ip(net, "dhcp"), "dhcp")
        self.assertEqual(calc_ip(net, "DHCP"), "dhcp")
        self.assertEqual(calc_ip(net, "dhcp", with_prefix=True), "dhcp")

    def test_raise_on_error(self):
        net = "172.16.0.0/22"
        with self.assertRaises(IPRangeError):
            calc_ip(net, "4.1", raise_on_error=True)
        with self.assertRaises(IPRangeError):
            calc_ip(net, 0, raise_on_error=True)
        with self.assertRaises(IPRangeError):
            calc_ip(net, "invalid_seed", raise_on_error=True)

    def test_get_segment_network_and_ip(self):
        new_seg = {
            'type': 'default',
            'net_source': 'default',
            'network_with_prefix': '172.16.0.0/22',
            'gateway_seed': '1',
        }
        self.assertEqual(get_segment_network(new_seg), "172.16.0.0/22")
        self.assertEqual(get_ip_from_segment(new_seg, "1.5"), "172.16.1.5")
        self.assertEqual(get_ip_from_segment(new_seg, "1.5", with_prefix=True), "172.16.1.5/22")
        self.assertEqual(get_ip_from_segment(new_seg, new_seg['gateway_seed']), "172.16.0.1")

        # Backward compatibility with legacy segment
        legacy_seg = {
            'type': 'default',
            'net_source': 'default',
            'ip_base_prefix': '192.168.122',
            'prefix': '24',
            'gateway_seed': '1',
        }
        self.assertEqual(get_segment_network(legacy_seg), "192.168.122.0/24")
        self.assertEqual(get_ip_from_segment(legacy_seg, 100), "192.168.122.100")
        self.assertEqual(get_ip_from_segment(legacy_seg, legacy_seg['gateway_seed']), "192.168.122.1")

    @patch('mini.menu.choose_num', return_value=0)
    def test_bind_env_with_slash_22(self, mock_choose):
        from plur_linux.lib.env_ops import EnvSegments
        env_segments = EnvSegments()
        env_segments.env_dict['segments'] = [{
            'type': 'openvswitch',
            'net_source': 'br0',
            'network_with_prefix': '172.16.0.0/22',
            'gateway_seed': '0.1',
            'search': 'test.local',
            'nameservers': '172.16.0.1,8.8.8.8',
        }]
        bound = env_segments.bind_env({
            'ifaces': [{'ip_seed': '1.5'}],
            'vnets': [{'ifname': 'eth0'}]
        })
        self.assertEqual(bound['ifaces'][0]['ip'], '172.16.1.5/22')
        self.assertEqual(bound['ifaces'][0]['gateway'], '172.16.0.1')
        self.assertEqual(bound['ifaces'][0]['search'], 'test.local')
        self.assertEqual(bound['ifaces'][0]['nameservers'], ['172.16.0.1', '8.8.8.8'])
        self.assertEqual(bound['vnets'][0]['type'], 'openvswitch')
        self.assertEqual(bound['vnets'][0]['net_source'], 'br0')

    @patch('mini.menu.choose_num', return_value=0)
    def test_bind_env_legacy_segment_compatibility(self, mock_choose):
        from plur_linux.lib.env_ops import EnvSegments
        env_segments = EnvSegments()
        env_segments.env_dict['segments'] = [{
            'type': 'default',
            'net_source': 'default',
            'ip_base_prefix': '192.168.122',
            'prefix': '24',
            'gateway_seed': '1',
            'search': 'local',
            'nameservers': '192.168.122.1',
        }]
        bound = env_segments.bind_env({
            'ifaces': [{'ip_seed': 100}],
            'vnets': [{'ifname': 'eth0'}]
        })
        self.assertEqual(bound['ifaces'][0]['ip'], '192.168.122.100/24')
        self.assertEqual(bound['ifaces'][0]['gateway'], '192.168.122.1')


if __name__ == '__main__':
    unittest.main()
