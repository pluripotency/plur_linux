import os
import shutil
import tempfile
import unittest
from unittest.mock import patch

from mini import misc
from plur_linux.lib.history import TomlHistory, get_plur_env_dir
from plur_linux.recipes.kvm.adhoc_setup import adhoc_history, almalinux9, select_post_run
from plur_linux.recipes.kvm.kvm_menu import runner


class TestTomlHistory(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.old_env = os.environ.get("PLUR_ENV_DIR")
        os.environ["PLUR_ENV_DIR"] = self.temp_dir

    def tearDown(self):
        if self.old_env is None:
            os.environ.pop("PLUR_ENV_DIR", None)
        else:
            os.environ["PLUR_ENV_DIR"] = self.old_env
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_respects_plur_env_dir(self):
        self.assertEqual(get_plur_env_dir(), self.temp_dir)
        hist = TomlHistory("adhoc_history.toml")
        self.assertEqual(hist.file_path, os.path.join(self.temp_dir, "adhoc_history.toml"))

    def test_sanitizes_none_and_caps_at_10_entries_newest_first(self):
        hist = TomlHistory("adhoc_history.toml", max_entries=10)
        for i in range(12):
            hist.add_entry(
                {
                    "os_label": f"OS-{i}",
                    "optional_none": None,
                    "nested": {"keep": i, "drop": None},
                }
            )

        loaded = hist.load_entries()
        self.assertEqual(len(loaded), 10)
        # Newest (OS-11) is first, oldest kept is OS-2 (OS-0 and OS-1 dropped)
        self.assertEqual(loaded[0]["os_label"], "OS-11")
        self.assertEqual(loaded[-1]["os_label"], "OS-2")
        self.assertNotIn("optional_none", loaded[0])
        self.assertEqual(loaded[0]["nested"], {"keep": 11})
        self.assertTrue(loaded[0]["created_at"])


class TestAdhocHistoryFlow(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.old_env = os.environ.get("PLUR_ENV_DIR")
        os.environ["PLUR_ENV_DIR"] = self.temp_dir
        self.history_store = adhoc_history.AdhocHistory(env_dir=self.temp_dir)

    def tearDown(self):
        if self.old_env is None:
            os.environ.pop("PLUR_ENV_DIR", None)
        else:
            os.environ["PLUR_ENV_DIR"] = self.old_env
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_select_menu_roundtrip_with_extra_params_and_custom_attrs(self):
        _vm, post_run_list = almalinux9.get_selection()
        by_title = {item.menu_title: item for item in post_run_list}

        # Toggle Docker + portainer
        by_title["Docker"].enable = True
        by_title["Docker"].selection["portainer"] = True

        # Toggle Languages with uv extra_params and nodejs custom_attrs
        lang = by_title["Languages"]
        lang.enable = True
        lang.selection["python(uv)"] = True
        lang.python_version = "3.13"
        lang.extra_params["python(uv)"] = {"version": "3.13"}
        lang.selection["node"] = True
        lang.node_installer = "nvm"
        lang.node_version = "v24"

        # Toggle Base Apps with nvim custom version
        base_apps = by_title["Base Apps"]
        base_apps.enable = True
        base_apps.selection["nvim"] = True
        base_apps.nvim_version = "v0.10.4"
        base_apps.extra_params["nvim"] = {"version": "v0.10.4", "arch": "linux-x86_64"}

        vm_dict = {
            "hostname": "a9hist",
            "platform": "almalinux9",
            "vcpu": 4,
            "vmem": 8192,
            "username": "worker",
            "password": "SUPER_SECRET_PASSWORD",
            "root_password": "SUPER_SECRET_ROOT_PASSWORD",
            "offline_setups": {"users": [{"username": "worker", "password": "SUPER_SECRET_PASSWORD"}]},
            "login_method": "create vm",
            "size": 20,
            "access_ip": "192.168.122.55",
            "restart_before_setup": False,
            "prepare_vdisk": {"type": "cloud_image", "size": 20, "partition": ["/dev/vda", 2]},
            "ifaces": [{"con_name": "eth0", "ip": "192.168.122.55/24"}],
            "vnets": [{"ifname": "eth0", "mac": "52:54:00:aa:bb:cc", "type": "default", "net_source": "default"}],
        }

        self.history_store.save_selection("AlmaLinux9", vm_dict, post_run_list)

        # Ensure plaintext passwords are NOT written to adhoc_history.toml
        raw_toml = misc.open_read(self.history_store.file_path)
        self.assertNotIn("SUPER_SECRET_PASSWORD", raw_toml)
        self.assertNotIn("SUPER_SECRET_ROOT_PASSWORD", raw_toml)

        loaded_entry = self.history_store.get_entry(0)
        self.assertEqual(loaded_entry["os_label"], "AlmaLinux9")
        self.assertEqual(loaded_entry["resource"], {"vcpu": 4, "vmem": 8192})
        self.assertEqual(loaded_entry["account"], {"username": "worker"})

        # Restore onto fresh AlmaLinux9 post_run_list
        _fresh_vm, fresh_post_run = almalinux9.get_selection()
        adhoc_history.apply_history_to_post_run_list(fresh_post_run, loaded_entry)
        restored_by_title = {item.menu_title: item for item in fresh_post_run}

        self.assertTrue(restored_by_title["Docker"].enable)
        self.assertTrue(restored_by_title["Docker"].selection["portainer"])
        self.assertFalse(restored_by_title["Docker"].selection["cadvisor"])

        restored_lang = restored_by_title["Languages"]
        self.assertTrue(restored_lang.enable)
        self.assertEqual(restored_lang.python_version, "3.13")
        self.assertEqual(restored_lang.extra_params["python(uv)"], {"version": "3.13"})
        self.assertEqual(restored_lang.node_installer, "nvm")
        self.assertEqual(restored_lang.node_version, "v24")

        restored_base = restored_by_title["Base Apps"]
        self.assertTrue(restored_base.enable)
        self.assertEqual(restored_base.nvim_version, "v0.10.4")

        # Restore connect dict and verify MAC address is regenerated
        with patch("plur_linux.recipes.kvm.adhoc_setup.adhoc_history.new_node.random_mac", return_value="52:54:00:11:22:33"):
            con_method, restored_con = adhoc_history.restore_connect_node_dict(
                loaded_entry["connect"], connect_method_list=None
            )
        self.assertEqual(con_method, "create vm")
        self.assertEqual(restored_con["hostname"], "a9hist")
        self.assertFalse(restored_con["restart_before_setup"])
        self.assertEqual(restored_con["vnets"][0]["mac"], "52:54:00:11:22:33")

    def test_incompatible_connect_method_falls_back_cleanly(self):
        ssh_connect = {
            "login_method": "ssh",
            "hostname": "remote1",
            "access_ip": "10.0.0.10",
        }
        vm_con = select_post_run.VmConnect(
            {"hostname": "localhost", "size": 10, "platform": "almalinux9", "username": "worker"},
            connect_method_list=["create vm"],
            restored_connect=ssh_connect,
        )
        self.assertIsNone(vm_con.selected_con)
        self.assertIsNone(vm_con.node_dict)
        # Hostname carried over as default for when user configures 'create vm'
        self.assertEqual(vm_con.initial_node_dict["hostname"], "remote1")

    def test_select_adhoc_saves_history_and_restores_for_editing(self):
        # 1st run: Select AlmaLinux9 (index 1 since index 0 is "History"),
        # configure SSH connection, enable Docker, then click Next.
        choose_responses_run1 = iter([
            1,   # Top menu: "AlmaLinux9" (0="History", 1="AlmaLinux9")
            2,   # Select menu (AlmaLinux9): "Connect Method(...)"
            0,   # VmConnect: "ssh"
            6,   # Select menu (AlmaLinux9): "Docker(No, ...)"
            3,   # Docker submenu: "back" (leaves Docker enabled)
            10,  # Select menu (AlmaLinux9): "Next"
        ])
        with (
            patch("plur_linux.recipes.kvm.kvm_menu.runner.choose_num", side_effect=lambda *a, **kw: next(choose_responses_run1)),
            patch("plur_linux.recipes.kvm.adhoc_setup.select_post_run.choose_num", side_effect=lambda *a, **kw: next(choose_responses_run1)),
            patch("plur_linux.recipes.kvm.adhoc_setup.generic.choose_num", side_effect=lambda *a, **kw: next(choose_responses_run1)),
            patch("plur_linux.recipes.kvm.adhoc_setup.generic.get_y_n", return_value=True),
            patch("plur_linux.recipes.kvm.adhoc_setup.select_post_run.get_input", side_effect=["web01", "192.168.122.80"]),
        ):
            vm_dict_1, post_run_1 = runner.select_adhoc(None, history_store=self.history_store)

        self.assertEqual(vm_dict_1["hostname"], "web01")
        self.assertEqual(vm_dict_1["access_ip"], "192.168.122.80")
        docker_1 = [p for p in post_run_1 if p.menu_title == "Docker"][0]
        self.assertTrue(docker_1.enable)

        entries_after_1 = self.history_store.load_entries()
        self.assertEqual(len(entries_after_1), 1)
        self.assertIn("AlmaLinux9", adhoc_history.format_history_entry(entries_after_1[0]))

        # 2nd run: Choose "History" (index 0) -> pick entry 0 ->
        # edit Resource to 4 vcpu / 8192 vmem (index 0 -> option 3),
        # verify Connect Method is already restored so "Next" (index 10) is immediately available!
        captured_menu_messages = []

        def fake_select_post_run_choose(items, message="Select menu", **_kwargs):
            captured_menu_messages.append((message, list(items)))
            if len(captured_menu_messages) == 1:
                return 0  # Select Resource(...)
            if len(captured_menu_messages) == 2:
                return 3  # Select vcpu:4 vmem:8192
            return len(items) - 1  # Select "Next"

        runner_choices_run2 = iter([
            0,  # Top menu: "History"
            0,  # History menu: 1st (latest) entry
        ])
        with (
            patch("plur_linux.recipes.kvm.kvm_menu.runner.choose_num", side_effect=lambda *a, **kw: next(runner_choices_run2)),
            patch("plur_linux.recipes.kvm.adhoc_setup.select_post_run.choose_num", side_effect=fake_select_post_run_choose),
        ):
            vm_dict_2, post_run_2 = runner.select_adhoc(None, history_store=self.history_store)

        # OS title was shown on editable menu and Next was available immediately
        self.assertEqual(captured_menu_messages[0][0], "Select menu (AlmaLinux9)")
        self.assertEqual(captured_menu_messages[0][1][-1], "Next")

        # Previous SSH connection & Docker enable were preserved, Resource edit applied
        self.assertEqual(vm_dict_2["hostname"], "web01")
        self.assertEqual(vm_dict_2["access_ip"], "192.168.122.80")
        self.assertEqual(vm_dict_2["vcpu"], 4)
        self.assertEqual(vm_dict_2["vmem"], 8192)
        docker_2 = [p for p in post_run_2 if p.menu_title == "Docker"][0]
        self.assertTrue(docker_2.enable)

        # History now has 2 entries, newest has vcpu=4, vmem=8192
        entries_after_2 = self.history_store.load_entries()
        self.assertEqual(len(entries_after_2), 2)
        self.assertEqual(entries_after_2[0]["resource"], {"vcpu": 4, "vmem": 8192})


if __name__ == "__main__":
    unittest.main()
