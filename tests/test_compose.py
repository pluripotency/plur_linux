import json
import unittest
from unittest.mock import patch, MagicMock
from plur_linux.recipes.pxe import compose
from plur_linux.recipes.pxe import pxe


class TestCompose(unittest.TestCase):

    def test_create_nginx_conf_str_with_allowed_net(self):
        conf = compose.create_nginx_conf_str(
            alias='/almalinux9',
            dir_path='/var/pxe/almalinux9',
            allowed_net='192.168.10.0/24'
        )
        self.assertIn('listen 80 default_server;', conf)
        self.assertIn('root /var/www/html;', conf)
        self.assertIn('autoindex on;', conf)
        self.assertIn('location /ks {', conf)
        self.assertIn('alias /var/www/html/ks;', conf)
        self.assertIn('location /almalinux9/ {', conf)
        self.assertIn('alias /var/pxe/almalinux9/;', conf)
        self.assertIn('allow 127.0.0.1;', conf)
        self.assertIn('allow 192.168.10.0/24;', conf)
        self.assertIn('deny all;', conf)

    def test_create_nginx_conf_str_without_allowed_net(self):
        conf = compose.create_nginx_conf_str(
            alias='almalinux8',
            dir_path='/var/pxe/almalinux8'
        )
        self.assertIn('location /almalinux8/ {', conf)
        self.assertNotIn('deny all;', conf)

    def test_create_kea_conf_str(self):
        subnet_params = {
            'subnet': '192.168.10.0',
            'netmask': '255.255.255.0',
            'gateway': '192.168.10.62',
            'nameservers': '192.168.10.1',
            'dh_range': '192.168.10.192 192.168.10.250',
            'broadcast': '192.168.10.255',
            'domain_name': 'test.local',
            'allowed_net': '192.168.10.0/24',
        }
        kea_json_str = compose.create_kea_conf_str('192.168.10.154', subnet_params)
        data = json.loads(kea_json_str)

        self.assertIn('Dhcp4', data)
        dhcp4 = data['Dhcp4']

        self.assertEqual(dhcp4['interfaces-config']['interfaces'], ['*'])
        self.assertEqual(dhcp4['lease-database']['type'], 'memfile')

        # Check client classes
        classes = {c['name']: c for c in dhcp4['client-classes']}
        self.assertIn('UEFI-64', classes)
        self.assertEqual(classes['UEFI-64']['boot-file-name'], 'BOOTX64.EFI')
        self.assertIn('BIOS-x86', classes)
        self.assertEqual(classes['BIOS-x86']['boot-file-name'], 'pxelinux.0')

        # Check subnet
        self.assertEqual(len(dhcp4['subnet4']), 1)
        sub = dhcp4['subnet4'][0]
        self.assertEqual(sub['subnet'], '192.168.10.0/24')
        self.assertEqual(sub['pools'], [{'pool': '192.168.10.192 - 192.168.10.250'}])
        self.assertEqual(sub['next-server'], '192.168.10.154')
        self.assertEqual(sub['boot-file-name'], 'pxelinux.0')

        # Check options
        options = {opt['name']: opt['data'] for opt in sub['option-data']}
        self.assertEqual(options['routers'], '192.168.10.62')
        self.assertEqual(options['domain-name-servers'], '192.168.10.1')

    def test_create_docker_compose_str(self):
        compose_yaml = compose.create_docker_compose_str(
            compose_dir='/etc/pxe-docker',
            www_iso_dir='/var/pxe'
        )
        self.assertIn('services:', compose_yaml)
        self.assertIn('nginx:', compose_yaml)
        self.assertIn('image: nginx:alpine', compose_yaml)
        self.assertIn('container_name: pxe-nginx', compose_yaml)

        self.assertIn('kea:', compose_yaml)
        self.assertIn('image: isc/kea-dhcp4:latest', compose_yaml)
        self.assertIn('container_name: pxe-kea', compose_yaml)

        self.assertIn('tftpd:', compose_yaml)
        self.assertIn('image: ghcr.io/linuxserver/tftp-hpa:latest', compose_yaml)
        self.assertIn('container_name: pxe-tftp', compose_yaml)

        # Ensure network_mode: host for all services
        self.assertEqual(compose_yaml.count('network_mode: host'), 3)

        # Check volumes
        self.assertIn('/etc/pxe-docker/nginx.conf:/etc/nginx/conf.d/default.conf:ro', compose_yaml)
        self.assertIn('/etc/pxe-docker/kea-dhcp4.conf:/etc/kea/kea-dhcp4.conf:ro', compose_yaml)
        self.assertIn('/var/lib/tftpboot:/tftpboot:ro', compose_yaml)

    @patch('plur_linux.recipes.pxe.compose.base_shell')
    def test_prepare_compose_files(self, mock_base_shell):
        session = MagicMock()
        subnet_params = {
            'subnet': '192.168.0.0',
            'netmask': '255.255.255.0',
            'gateway': '192.168.0.1',
            'nameservers': '8.8.8.8',
            'dh_range': '192.168.0.192 192.168.0.250',
            'broadcast': '192.168.0.255',
            'allowed_net': '192.168.0.0/24',
        }
        compose.prepare_compose_files(
            session=session,
            pxe_ip='192.168.0.10',
            dist_dir='almalinux9',
            www_iso_dir='/var/pxe/almalinux9',
            subnet_params=subnet_params,
            compose_dir='/etc/pxe-docker'
        )
        self.assertTrue(mock_base_shell.run.called)
        self.assertEqual(mock_base_shell.here_doc.call_count, 3)

    @patch('plur_linux.recipes.pxe.compose.firewalld')
    @patch('plur_linux.recipes.pxe.compose.base_shell')
    def test_setup_pxe_compose(self, mock_base_shell, mock_firewalld):
        session = MagicMock()
        mock_fw_func = MagicMock()
        mock_firewalld.configure.return_value = mock_fw_func

        func = compose.setup_pxe_compose(
            pxe_ip='192.168.0.10',
            dist_dir='almalinux9',
            www_iso_dir='/var/pxe/almalinux9',
            set_fw=True,
            compose_dir='/etc/pxe-docker'
        )
        func(session)

        mock_firewalld.configure.assert_called_with(services=['dhcp', 'tftp', 'http'], add=True)
        mock_fw_func.assert_called_with(session)
        self.assertEqual(mock_base_shell.here_doc.call_count, 3)
        mock_base_shell.run.assert_any_call(session, 'docker compose -f /etc/pxe-docker/docker-compose.yml up -d')

    @patch('plur_linux.recipes.pxe.compose.setup_pxe_compose')
    def test_setup_pxe_base_by_docker(self, mock_setup_compose):
        mock_func = MagicMock()
        mock_setup_compose.return_value = mock_func

        res = pxe.setup_pxe_base_by_docker(
            pxe_ip='192.168.0.10',
            dist_dir='almalinux9',
            www_iso_dir='/var/pxe/almalinux9'
        )
        mock_setup_compose.assert_called_with(
            pxe_ip='192.168.0.10',
            dist_dir='almalinux9',
            www_iso_dir='/var/pxe/almalinux9',
            segment=None,
            compose_dir='/etc/pxe-docker',
            set_fw=True,
        )
        self.assertEqual(res, mock_func)


if __name__ == '__main__':
    unittest.main()
