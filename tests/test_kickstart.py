import unittest
from unittest.mock import patch, MagicMock
from plur_linux.recipes.pxe import kickstart


class TestKickstart(unittest.TestCase):
    def test_create_timezone_str_standard(self):
        tz = kickstart.create_timezone_str(new_tz=False)
        self.assertIn("timezone Asia/Tokyo --isUtc --nontp", tz)
        self.assertNotIn("timesource", tz)

    def test_create_timezone_str_a10(self):
        tz = kickstart.create_timezone_str(new_tz=True)
        self.assertIn("timezone Asia/Tokyo --utc", tz)
        self.assertIn("timesource --ntp-disable", tz)

    def test_create_standard_volume_str(self):
        vol_sda = kickstart.create_standard_volume_str('sda')
        self.assertIn('clearpart --all --initlabel', vol_sda)
        self.assertIn('part /boot --fstype="ext4" --ondisk=sda --size=2048', vol_sda)
        self.assertIn('part /boot/efi --fstype="vfat" --ondisk=sda --size=512', vol_sda)
        self.assertIn('part / --fstype xfs --grow --size=1', vol_sda)

        vol_vda = kickstart.create_standard_volume_str('vda')
        self.assertIn('--ondisk=vda', vol_vda)

    def test_create_lvm_data_volume_str(self):
        vol_lvm = kickstart.create_lvm_data_volume_str('sda')
        self.assertIn('clearpart --all --initlabel', vol_lvm)
        self.assertIn('part /boot/efi --fstype="efi" --size=600 --ondisk=sda', vol_lvm)
        self.assertIn('part /boot --fstype="xfs" --size=2048 --ondisk=sda', vol_lvm)
        self.assertIn('part pv.01 --fstype="lvmpv" --size=1 --grow --ondisk=sda', vol_lvm)
        self.assertIn('volgroup vg_system pv.01', vol_lvm)
        self.assertIn('logvol / --fstype="xfs" --size=51200 --name=lv_root --vgname=vg_system', vol_lvm)
        self.assertIn('logvol swap --fstype="swap" --size=8192 --name=lv_swap --vgname=vg_system', vol_lvm)
        self.assertIn('logvol /data --fstype="xfs" --size=1 --grow --name=lv_data --vgname=vg_system', vol_lvm)

        vol_lvm_vda = kickstart.create_lvm_data_volume_str('vda')
        self.assertIn('--ondisk=vda', vol_lvm_vda)

    def test_create_ks_str_unification(self):
        # AlmaLinux 8/9 with standard partition
        ks_a9_std = kickstart.create_ks_str('url --url=http://10.0.0.1/a9/', 'sda', new_tz=False, volume_type='standard')
        self.assertIn('timezone Asia/Tokyo --isUtc --nontp', ks_a9_std)
        self.assertIn('part / --fstype xfs --grow --size=1', ks_a9_std)
        self.assertIn('ignoredisk --only-use=sda', ks_a9_std)

        # AlmaLinux 10 with LVM partition
        ks_a10_lvm = kickstart.create_ks_str('url --url=http://10.0.0.1/a10/', 'vda', new_tz=True, volume_type='lvm_data')
        self.assertIn('timezone Asia/Tokyo --utc', ks_a10_lvm)
        self.assertIn('timesource --ntp-disable', ks_a10_lvm)
        self.assertIn('logvol / --fstype="xfs" --size=51200 --name=lv_root --vgname=vg_system', ks_a10_lvm)
        self.assertIn('logvol /data --fstype="xfs" --size=1 --grow --name=lv_data --vgname=vg_system', ks_a10_lvm)
        self.assertIn('ignoredisk --only-use=vda', ks_a10_lvm)

    def test_create_a10_ks_str_compatibility(self):
        ks = kickstart.create_a10_ks_str('url --url=http://10.0.0.1/a10/', 'sda')
        self.assertIn('timezone Asia/Tokyo --utc', ks)
        self.assertIn('timesource --ntp-disable', ks)

    @patch('plur_linux.recipes.pxe.kickstart.base_shell')
    def test_prepare_ks(self, mock_base_shell):
        session = MagicMock()
        files = kickstart.prepare_ks(session, '192.168.0.10', 'almalinux9', include_lvm=True)
        self.assertEqual(files, ['phy_lvm.ks', 'vda_lvm.ks', 'sda_lvm.ks', 'phy.ks', 'vda.ks', 'sda.ks'])
        self.assertEqual(mock_base_shell.here_doc.call_count, 6)

        # Verify include_lvm=False
        mock_base_shell.reset_mock()
        files_no_lvm = kickstart.prepare_ks(session, '192.168.0.10', 'almalinux9', include_lvm=False)
        self.assertEqual(files_no_lvm, ['phy.ks', 'vda.ks', 'sda.ks'])
        self.assertEqual(mock_base_shell.here_doc.call_count, 3)

    def test_encrypt_password(self):
        # Plaintext password
        hashed = kickstart.encrypt_password('testpass', rounds=5000)
        self.assertTrue(hashed.startswith('$6$'))
        from passlib.hash import sha512_crypt
        self.assertTrue(sha512_crypt.verify('testpass', hashed))

        # Already hashed password
        already_hashed = '$1$v4y/Tz8G$mq2hT5nsuafCpIB7KlQTQ/'
        self.assertEqual(kickstart.encrypt_password(already_hashed), already_hashed)

    @patch('plur_linux.lib.env_ops.EnvAccountSet')
    def test_create_account_str_default(self, mock_env_account_set):
        account_set = {
            'username': 'testuser',
            'password': 'usersecret',
            'sudoers': True,
            'root_password': 'rootsecret',
        }
        mock_env_account_set.return_value.get_current_index_account_set.return_value = account_set
        account_str = kickstart.create_account_str()
        self.assertIn('rootpw --iscrypted $6$', account_str)
        self.assertIn('user --name=testuser', account_str)
        self.assertIn('--password=$6$', account_str)
        self.assertIn('--iscrypted', account_str)
        self.assertIn('--groups=wheel', account_str)

    @patch('plur_linux.lib.env_ops.EnvAccountSet')
    def test_create_account_str_no_sudo(self, mock_env_account_set):
        account_set = {
            'username': 'limiteduser',
            'password': 'usersecret',
            'sudoers': False,
            'root_password': 'rootsecret',
        }
        mock_env_account_set.return_value.get_current_index_account_set.return_value = account_set
        account_str = kickstart.create_account_str()
        self.assertIn('user --name=limiteduser', account_str)
        self.assertNotIn('--groups=wheel', account_str)

    @patch('plur_linux.lib.env_ops.EnvAccountSet')
    def test_create_account_str_root_only(self, mock_env_account_set):
        account_set = {
            'username': 'root',
            'password': 'rootsecret',
            'sudoers': True,
            'root_password': 'rootsecret',
        }
        mock_env_account_set.return_value.get_current_index_account_set.return_value = account_set
        account_str = kickstart.create_account_str()
        self.assertIn('rootpw --iscrypted $6$', account_str)
        self.assertNotIn('user --name=root', account_str)

    @patch('plur_linux.lib.env_ops.EnvAccountSet')
    def test_create_account_str_fallback(self, mock_env_account_set):
        from plur_linux.lib.env_ops import default_account_set
        mock_env_account_set.side_effect = Exception("env config not found")
        account_str = kickstart.create_account_str()
        self.assertIn('rootpw --iscrypted $6$', account_str)
        self.assertIn(f"user --name={default_account_set['username']}", account_str)

    @patch('plur_linux.lib.env_ops.EnvAccountSet')
    def test_create_ks_str_with_custom_account(self, mock_env_account_set):
        custom_account = {
            'username': 'myadmin',
            'password': 'mypassword',
            'sudoers': True,
            'root_password': 'myrootpassword',
        }
        mock_env_account_set.return_value.get_current_index_account_set.return_value = custom_account
        ks = kickstart.create_ks_str('url --url=http://10.0.0.1/a9/', 'sda')
        self.assertIn('user --name=myadmin', ks)
        self.assertIn('--groups=wheel', ks)
        self.assertIn('rootpw --iscrypted $6$', ks)


if __name__ == '__main__':
    unittest.main()
