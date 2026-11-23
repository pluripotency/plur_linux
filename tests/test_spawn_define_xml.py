import types
import unittest
from unittest import mock

from plur_linux.recipes.kvm import spawn
from plur_linux.recipes.kvm.kvm_menu import lib as kvm_menu_lib
from plur_linux.recipes.kvm.adhoc_setup import adhoc_history
from plur_linux.recipes.kvm.adhoc_setup.select_post_run import VmConnect


def _make_vm(**kwargs):
    defaults = {
        "hostname": "testvm",
        "vcpu": 2,
        "vmem": 2048,
        "platform": "almalinux9",
        "vnets": [
            {
                "mac": "52:54:00:11:22:33",
                "type": "bridge",
                "net_source": "br0",
            }
        ],
    }
    defaults.update(kwargs)
    return types.SimpleNamespace(**defaults)


class TestSpawnDefineXml(unittest.TestCase):
    def test_should_define_xml_defaults_to_true_and_respects_precedence(self):
        vm_default = _make_vm()
        self.assertTrue(spawn.should_define_xml(vm_default))

        vm_prepare = _make_vm(prepare_vdisk={"type": "cloud_image", "definexml": False})
        self.assertFalse(spawn.should_define_xml(vm_prepare))

        vm_attr = _make_vm(
            definexml=True,
            prepare_vdisk={"type": "cloud_image", "definexml": False},
        )
        self.assertTrue(spawn.should_define_xml(vm_attr))
        self.assertFalse(spawn.should_define_xml(vm_attr, definexml=False))

    @mock.patch("plur_linux.recipes.kvm.spawn.base_shell.run")
    def test_start_domain_by_define_xml_runs_expected_commands(self, mock_run):
        vm = _make_vm()
        session = object()

        spawn.start_domain_by_define_xml(
            vm, "/tmp/seediso/seed_testvm.iso", "/vm_images"
        )(session)

        cmds = [call.args[1] for call in mock_run.call_args_list]
        self.assertEqual(len(cmds), 5)
        self.assertEqual(cmds[0], "sudo rm -f /tmp/testvm.xml")
        self.assertIn("--events on_reboot=restart", cmds[1])
        self.assertIn("--print-xml 1 > /tmp/testvm.xml", cmds[1])
        self.assertIn("--disk /vm_images/testvm.qcow2,cache=none --cdrom=/tmp/seediso/seed_testvm.iso", cmds[1])
        self.assertNotIn("--noreboot", cmds[1])
        self.assertNotIn("--noautoconsole", cmds[1])
        self.assertEqual(
            cmds[2],
            "sudo sed -i 's|<on_reboot>destroy</on_reboot>|<on_reboot>restart</on_reboot>|g' /tmp/testvm.xml",
        )
        self.assertEqual(cmds[3], "sudo virsh define /tmp/testvm.xml")
        self.assertEqual(cmds[4], "sudo virsh start testvm")

    def _run_cloudinit_flow(self, **kwargs):
        events = []
        vm = _make_vm(**kwargs.pop("vm_kwargs", {}))
        fake_session = types.SimpleNamespace(
            nodes=[types.SimpleNamespace(vdisk_dir="/vm_images")]
        )

        with (
            mock.patch.object(spawn.session_wrap, "sudo", side_effect=lambda f: f),
            mock.patch.object(spawn.base_shell, "work_on"),
            mock.patch.object(spawn.base_shell, "run"),
            mock.patch.object(spawn, "on_kvm_pre_check_files"),
            mock.patch.object(
                spawn,
                "on_kvm_prepare_cloudinit_seed_iso",
                return_value=lambda s: "/tmp/seediso/seed_testvm.iso",
            ),
            mock.patch.object(
                spawn,
                "prepare_cloudinit_vdisk",
                return_value="/tmp/testvm.qcow2",
            ),
            mock.patch.object(
                spawn,
                "start_domain_by_define_xml",
                side_effect=lambda *a: lambda s: events.append("start_define_xml"),
            ),
            mock.patch.object(
                spawn,
                "start_domain_by_virt_install",
                side_effect=lambda *a: lambda s: events.append("start_virt_install"),
            ),
            mock.patch.object(
                spawn,
                "restart_domain",
                side_effect=lambda *a: lambda s: events.append("restart_domain"),
            ),
            mock.patch.object(
                spawn,
                "on_create_console_with_cloudinit",
                side_effect=lambda *a: lambda s: events.append("console_setup"),
            ),
            mock.patch.object(
                spawn,
                "eject_seed_iso",
                side_effect=lambda *a: lambda s: events.append("eject_seed_iso"),
            ),
            mock.patch.object(
                spawn,
                "on_kvm_post",
                side_effect=lambda *a: lambda s: events.append("on_kvm_post"),
            ),
        ):
            spawn.create_vm_by_virt_install_cloudinit(vm, **kwargs)(fake_session)
        return events

    def test_create_vm_cloudinit_default_definexml_branch(self):
        events = self._run_cloudinit_flow()
        self.assertEqual(
            events,
            ["start_define_xml", "console_setup", "eject_seed_iso", "on_kvm_post"],
        )

    def test_create_vm_cloudinit_restart_branch(self):
        events = self._run_cloudinit_flow(definexml=False, restart_before_setup=True)
        self.assertEqual(
            events,
            ["start_virt_install", "restart_domain", "console_setup", "on_kvm_post"],
        )

    def test_create_vm_cloudinit_oneshot_branch(self):
        events = self._run_cloudinit_flow(definexml=False, restart_before_setup=False)
        self.assertEqual(
            events,
            ["start_virt_install", "console_setup", "eject_seed_iso", "on_kvm_post"],
        )


class TestAdhocModeFormatting(unittest.TestCase):
    def test_history_and_vmconnect_format_definexml_mode(self):
        connect_data = {
            "login_method": "create vm",
            "hostname": "vm01",
            "access_ip": "192.168.122.50",
            "size": 20,
            "definexml": True,
            "restart_before_setup": False,
        }
        summary = adhoc_history.format_connect_summary(connect_data)
        self.assertIn("mode:definexml", summary)

        extracted = adhoc_history.extract_connect_dict(connect_data)
        self.assertTrue(extracted["definexml"])

        vm_con = VmConnect({}, None, restored_connect=connect_data)
        self.assertIn("mode:definexml", vm_con.get_format_con())

    @mock.patch("plur_linux.recipes.kvm.kvm_menu.lib.get_y_n", return_value=True)
    def test_select_define_xml_defaults_to_true(self, mock_get_y_n):
        self.assertTrue(kvm_menu_lib.select_define_xml())
        mock_get_y_n.assert_called_once_with(
            "Start VM by virsh define XML (--print-xml 1)", default=True
        )

    def test_single_constant_controls_all_defaults(self):
        with mock.patch.object(spawn, "DEFAULT_DEFINE_XML", False):
            self.assertFalse(spawn.should_define_xml({}))
            self.assertEqual(spawn.get_vm_boot_mode_label({}), "restart")
            with mock.patch(
                "plur_linux.recipes.kvm.kvm_menu.lib.get_y_n",
                side_effect=[False, True],
            ) as mock_y_n:
                definexml, restart = kvm_menu_lib.select_vm_boot_options({})
                self.assertEqual((definexml, restart), (False, True))
                self.assertEqual(mock_y_n.call_args_list[0].kwargs["default"], False)
                self.assertEqual(mock_y_n.call_args_list[1].kwargs["default"], True)

        with mock.patch.object(spawn, "DEFAULT_DEFINE_XML", True):
            self.assertTrue(spawn.should_define_xml({}))
            self.assertEqual(spawn.get_vm_boot_mode_label({}), "definexml")
            with mock.patch(
                "plur_linux.recipes.kvm.kvm_menu.lib.get_y_n",
                return_value=True,
            ) as mock_y_n:
                definexml, restart = kvm_menu_lib.select_vm_boot_options({})
                self.assertEqual((definexml, restart), (True, False))
                self.assertEqual(mock_y_n.call_args_list[0].kwargs["default"], True)


if __name__ == "__main__":
    unittest.main()
