import unittest
from unittest.mock import MagicMock, patch

from plur import base_node
from plur_linux.recipes.kvm import spawn
from plur_linux.recipes.kvm.adhoc_setup import select_post_run
from plur_linux.recipes.kvm.kvm_menu import create_guest, lib, runner


class TestSpawnVmRoutes(unittest.TestCase):
    def _make_vm(self, extra=None):
        vm_dict = {
            "hostname": "testvm",
            "platform": "almalinux9",
            "username": "worker",
            "password": "password",
            "waitprompt": r"\[?worker@testvm .+\]\$ ",
            "vcpu": 2,
            "vmem": 2048,
            "prepare_vdisk": {
                "type": "cloud_image",
                "size": 10,
            },
        }
        if extra:
            vm_dict.update(extra)
        return base_node.Node(vm_dict)

    def _make_session(self, vdisk_dir="/vm_images"):
        session = MagicMock()
        kvm_node = MagicMock()
        kvm_node.vdisk_dir = vdisk_dir
        session.nodes = [kvm_node]
        return session

    def test_should_restart_before_setup_precedence(self):
        vm_default = self._make_vm()
        self.assertTrue(spawn.should_restart_before_setup(vm_default))

        vm_attr_false = self._make_vm({"restart_before_setup": False})
        self.assertFalse(spawn.should_restart_before_setup(vm_attr_false))

        vm_vdisk_false = self._make_vm(
            {
                "prepare_vdisk": {
                    "type": "cloud_image",
                    "size": 10,
                    "restart_before_setup": False,
                }
            }
        )
        self.assertFalse(spawn.should_restart_before_setup(vm_vdisk_false))

        # Explicit argument overrides vm attribute in both directions
        self.assertTrue(
            spawn.should_restart_before_setup(vm_attr_false, restart_before_setup=True)
        )
        self.assertFalse(
            spawn.should_restart_before_setup(vm_default, restart_before_setup=False)
        )

    @patch("plur_linux.recipes.kvm.spawn.base_shell.run")
    @patch("plur_linux.recipes.kvm.spawn.virsh.is_running")
    def test_eject_seed_iso_when_running_and_when_shutoff(
        self, mock_is_running, mock_run
    ):
        vm = self._make_vm()
        session = self._make_session()
        seed_iso = "/tmp/seediso/seed_testvm.iso"

        mock_is_running.return_value = True
        spawn.eject_seed_iso(vm, seed_iso)(session)
        mock_run.assert_any_call(
            session,
            "virsh change-media testvm --path sda --eject --force --live --config",
        )
        mock_run.assert_any_call(session, f"sudo rm -f {seed_iso}")

        mock_run.reset_mock()
        mock_is_running.return_value = False
        spawn.eject_seed_iso(vm, seed_iso)(session)
        mock_run.assert_any_call(
            session,
            "virsh change-media testvm --path sda --eject --config",
        )
        mock_run.assert_any_call(session, f"sudo rm -f {seed_iso}")

    def _run_create_vm_with_mocks(self, vm, restart_before_setup=None):
        events = []
        session = self._make_session()

        def record_step(name):
            def factory(*_args, **_kwargs):
                def step(_sess):
                    events.append(name)

                return step

            return factory

        with (
            patch(
                "plur_linux.recipes.kvm.spawn.session_wrap.sudo",
                side_effect=lambda fn: fn,
            ),
            patch("plur_linux.recipes.kvm.spawn.base_shell.work_on"),
            patch("plur_linux.recipes.kvm.spawn.base_shell.run"),
            patch("plur_linux.recipes.kvm.spawn.on_kvm_pre_check_files"),
            patch(
                "plur_linux.recipes.kvm.spawn.on_kvm_prepare_cloudinit_seed_iso",
                side_effect=lambda _vm: lambda _sess: "/tmp/seediso/seed_testvm.iso",
            ),
            patch(
                "plur_linux.recipes.kvm.spawn.prepare_cloudinit_vdisk",
                return_value="/tmp/testvm.qcow2",
            ),
            patch(
                "plur_linux.recipes.kvm.spawn.start_domain_by_virt_install",
                side_effect=record_step("start_domain_by_virt_install"),
            ),
            patch(
                "plur_linux.recipes.kvm.spawn.restart_domain",
                side_effect=record_step("restart_domain"),
            ),
            patch(
                "plur_linux.recipes.kvm.spawn.on_create_console_with_cloudinit",
                side_effect=record_step("on_create_console_with_cloudinit"),
            ),
            patch(
                "plur_linux.recipes.kvm.spawn.eject_seed_iso",
                side_effect=record_step("eject_seed_iso"),
            ),
            patch(
                "plur_linux.recipes.kvm.spawn.on_kvm_post",
                side_effect=record_step("on_kvm_post"),
            ),
        ):
            spawn.create_vm_by_virt_install_cloudinit(
                vm, restart_before_setup=restart_before_setup
            )(session)

        return events

    def test_create_vm_default_route_restarts_before_setup(self):
        vm = self._make_vm()
        events = self._run_create_vm_with_mocks(vm)
        self.assertEqual(
            events,
            [
                "start_domain_by_virt_install",
                "restart_domain",
                "on_create_console_with_cloudinit",
                "on_kvm_post",
            ],
        )

    def test_create_vm_one_shot_route_via_vm_attr_and_arg(self):
        vm_attr = self._make_vm({"restart_before_setup": False})
        events_attr = self._run_create_vm_with_mocks(vm_attr)
        self.assertEqual(
            events_attr,
            [
                "start_domain_by_virt_install",
                "on_create_console_with_cloudinit",
                "eject_seed_iso",
                "on_kvm_post",
            ],
        )

        vm_default = self._make_vm()
        events_arg = self._run_create_vm_with_mocks(
            vm_default, restart_before_setup=False
        )
        self.assertEqual(
            events_arg,
            [
                "start_domain_by_virt_install",
                "on_create_console_with_cloudinit",
                "eject_seed_iso",
                "on_kvm_post",
            ],
        )

    @patch("plur_linux.recipes.kvm.kvm_menu.lib.get_y_n", return_value=False)
    def test_select_restart_before_setup_helper(self, mock_get_y_n):
        result = lib.select_restart_before_setup()
        self.assertFalse(result)
        mock_get_y_n.assert_called_once_with(
            "Restart VM before setup (safe reboot)", default=True
        )

    @patch(
        "plur_linux.recipes.kvm.adhoc_setup.select_post_run.new_node.create_single_iface_node_dict"
    )
    @patch(
        "plur_linux.recipes.kvm.kvm_menu.lib.select_restart_before_setup",
        return_value=False,
    )
    @patch(
        "plur_linux.recipes.kvm.adhoc_setup.select_post_run.get_input",
        return_value="20",
    )
    @patch(
        "plur_linux.recipes.kvm.adhoc_setup.select_post_run.set_hostname",
        side_effect=lambda d: {**d, "hostname": "adhocvm"},
    )
    def test_adhoc_create_vm_params_and_format_con(
        self, _mock_hostname, _mock_input, mock_select_restart, mock_single_iface
    ):
        mock_single_iface.side_effect = lambda hostname, _ip, opt, login_user=None: {
            **opt,
            "hostname": hostname,
            "access_ip": "192.168.1.50",
        }
        initial = {
            "hostname": "localhost",
            "size": 10,
            "username": "worker",
            "platform": "almalinux9",
        }
        vm_con = select_post_run.VmConnect(initial, ["create vm"])
        vm_con.select_con_menu()

        mock_select_restart.assert_called_once_with(default=True)
        self.assertFalse(vm_con.node_dict["restart_before_setup"])
        self.assertIn("mode:one-shot", vm_con.get_format_con())

    @patch(
        "plur_linux.recipes.kvm.adhoc_setup.select_post_run.new_node.create_single_iface_node_dict"
    )
    @patch(
        "plur_linux.recipes.kvm.kvm_menu.lib.select_restart_before_setup",
        return_value=True,
    )
    @patch(
        "plur_linux.recipes.kvm.adhoc_setup.select_post_run.set_hostname",
        side_effect=lambda d: {**d, "hostname": "copyvm"},
    )
    def test_adhoc_create_vm_by_copy_params_and_format_con(
        self, _mock_hostname, mock_select_restart, mock_single_iface
    ):
        mock_single_iface.side_effect = lambda hostname, _ip, opt, login_user=None: {
            **opt,
            "hostname": hostname,
        }
        initial = {
            "hostname": "localhost",
            "username": "worker",
            "platform": "almalinux9",
        }
        vm_con = select_post_run.VmConnect(initial, ["create vm by copy"])
        vm_con.select_con_menu()

        mock_select_restart.assert_called_once_with(default=True)
        self.assertTrue(vm_con.node_dict["restart_before_setup"])
        self.assertIn("mode:restart", vm_con.get_format_con())

    @patch("plur_linux.recipes.kvm.kvm_menu.runner.spawn.create_vm_by_virt_install_cloudinit")
    @patch(
        "plur_linux.recipes.kvm.kvm_menu.create_guest.lib.select_restart_before_setup",
        return_value=False,
    )
    @patch("plur_linux.recipes.kvm.kvm_menu.create_guest.lib_vm_module.select_vm_history")
    @patch("plur_linux.recipes.kvm.kvm_menu.create_guest.Selection")
    def test_create_guest_by_select_passes_one_shot(
        self,
        _mock_selection,
        mock_select_vm,
        mock_select_restart,
        mock_create_vm,
    ):
        mock_select_vm.return_value = {
            "hostname": "dock101",
            "platform": "almalinux9",
            "prepare_vdisk": {"type": "copy", "org_file": "a9.qcow2"},
        }
        inner_fn = MagicMock()
        mock_create_vm.return_value = inner_fn
        session = self._make_session()

        create_guest.create_guest_by_select(session)

        mock_select_restart.assert_called_once_with(default=True)
        self.assertEqual(mock_create_vm.call_count, 1)
        _, kwargs = mock_create_vm.call_args
        self.assertFalse(kwargs["restart_before_setup"])
        inner_fn.assert_called_once_with(session)

    @patch("plur_linux.recipes.kvm.kvm_menu.runner.run_on")
    @patch("plur_linux.recipes.kvm.kvm_menu.runner.spawn.create_vm_by_virt_install_cloudinit")
    @patch(
        "plur_linux.recipes.kvm.kvm_menu.runner.lib.select_restart_before_setup",
        return_value=False,
    )
    @patch("plur_linux.recipes.kvm.kvm_menu.runner.lib_kvm_module.select_kvm_history")
    @patch("plur_linux.recipes.kvm.kvm_menu.runner.lib_vm_module.select_vm_history")
    @patch("plur_linux.recipes.kvm.kvm_menu.runner.Selection")
    def test_runner_create_defined_guest_passes_one_shot(
        self,
        mock_selection_cls,
        mock_select_vm,
        mock_select_kvm,
        mock_select_restart,
        mock_create_vm,
        mock_run_on,
    ):
        selection_inst = MagicMock()
        mock_selection_cls.return_value = selection_inst
        mock_select_vm.return_value = {
            "hostname": "a9baseimage",
            "platform": "almalinux9",
            "prepare_vdisk": {"type": "cloud_image", "size": 10},
        }
        kvm = MagicMock()
        mock_select_kvm.return_value = kvm
        session = self._make_session()
        inner_fn = MagicMock()
        mock_create_vm.return_value = inner_fn
        mock_run_on.side_effect = lambda _kvm, fn, log_params=None: fn(session)

        runner.create_defined_guest()

        mock_select_restart.assert_called_once_with(default=True)
        selection_inst.append.assert_called_with(
            {"key": "restart_before_setup", "value": False}
        )
        selection_inst.save.assert_called_once()
        _, kwargs = mock_create_vm.call_args
        self.assertFalse(kwargs["restart_before_setup"])
        inner_fn.assert_called_once_with(session)


if __name__ == "__main__":
    unittest.main()
