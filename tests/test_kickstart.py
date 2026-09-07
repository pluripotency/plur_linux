import unittest
from unittest.mock import patch, MagicMock
from plur_linux.recipes.pxe import kickstart


class TestKickstart(unittest.TestCase):
    def test_create_timezone_str_standard(self):
        tz = kickstart.create_timezone_str(a10=False)
        self.assertIn("timezone Asia/Tokyo --isUtc --nontp", tz)
        self.assertNotIn("timesource", tz)

    def test_create_timezone_str_a10(self):
        tz = kickstart.create_timezone_str(a10=True)
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
        self.assertIn('part /boot --fstype="xfs" --size=1024 --ondisk=sda', vol_lvm)
        self.assertIn('part pv.01 --fstype="lvmpv" --size=1 --grow --ondisk=sda', vol_lvm)
        self.assertIn('volgroup vg_system pv.01', vol_lvm)
        self.assertIn('logvol / --fstype="xfs" --size=51200 --name=lv_root --vgname=vg_system', vol_lvm)
        self.assertIn('logvol swap --fstype="swap" --size=8192 --name=lv_swap --vgname=vg_system', vol_lvm)
        self.assertIn('logvol /data --fstype="xfs" --size=1 --grow --name=lv_data --vgname=vg_system', vol_lvm)

        vol_lvm_vda = kickstart.create_lvm_data_volume_str('vda')
        self.assertIn('--ondisk=vda', vol_lvm_vda)

    def test_create_ks_str_unification(self):
        # AlmaLinux 8/9 with standard partition
        ks_a9_std = kickstart.create_ks_str('url --url=http://10.0.0.1/a9/', 'sda', a10=False, volume_type='standard')
        self.assertIn('timezone Asia/Tokyo --isUtc --nontp', ks_a9_std)
        self.assertIn('part / --fstype xfs --grow --size=1', ks_a9_std)
        self.assertIn('ignoredisk --only-use=sda', ks_a9_std)

        # AlmaLinux 10 with LVM partition
        ks_a10_lvm = kickstart.create_ks_str('url --url=http://10.0.0.1/a10/', 'vda', a10=True, volume_type='lvm_data')
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
        files = kickstart.prepare_ks(session, '192.168.0.10', 'almalinux9', a10=False, include_lvm=True)
        self.assertEqual(files, ['phy.ks', 'vda.ks', 'sda.ks', 'phy_lvm.ks', 'vda_lvm.ks', 'sda_lvm.ks'])
        self.assertEqual(mock_base_shell.here_doc.call_count, 6)

        # Verify include_lvm=False
        mock_base_shell.reset_mock()
        files_no_lvm = kickstart.prepare_ks(session, '192.168.0.10', 'almalinux9', a10=False, include_lvm=False)
        self.assertEqual(files_no_lvm, ['phy.ks', 'vda.ks', 'sda.ks'])
        self.assertEqual(mock_base_shell.here_doc.call_count, 3)


if __name__ == '__main__':
    unittest.main()
