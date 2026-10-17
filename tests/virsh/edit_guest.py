import os
import shutil
import tempfile
import unittest
from unittest.mock import MagicMock, patch

from plur import log_param_templates, session_wrap
from plur_linux.recipes.kvm import spawn
from plur_linux.recipes.kvm.kvm_menu import edit_guest

SAMPLE_XML_PATH = os.path.join(os.path.dirname(__file__), "a9test.xml")


class TestEditGuest(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.test_xml_path = os.path.join(self.temp_dir, "a9test.xml")
        shutil.copy2(SAMPLE_XML_PATH, self.test_xml_path)

    def tearDown(self):
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_uses_spawn_xml_dir(self):
        self.assertEqual(edit_guest.xml_dir, spawn.xml_dir)
        self.assertEqual(edit_guest.xml_dir, "/etc/libvirt/qemu")

    def test_unit_conversion(self):
        self.assertEqual(edit_guest.mib_to_kib(2048), 2097152)
        self.assertEqual(edit_guest.mib_to_kib(4096), 4194304)
        self.assertEqual(edit_guest.kib_to_mib(2097152), 2048)
        self.assertEqual(edit_guest.kib_to_mib(4194304), 4096)

    def test_parse_vcpu_and_memory_from_a9test_xml(self):
        with open(self.test_xml_path, "r", encoding="utf-8") as f:
            xml_content = f.read()
        info = edit_guest.parse_vcpu_and_memory(xml_content)
        self.assertEqual(info["vcpu"], 2)
        self.assertEqual(info["memory_kib"], 2097152)
        self.assertEqual(info["memory_mb"], 2048)
        self.assertEqual(info["current_memory_kib"], 2097152)

    def test_parse_xml_list(self):
        capture = (
            "sudo ls -1 /etc/libvirt/qemu/*.xml 2>/dev/null | cat\r\n"
            "\x1b[0m\x1b[00m/etc/libvirt/qemu/b_vm.xml\x1b[0m\r\n"
            "/etc/libvirt/qemu/a9test.xml\r\n"
            "a10desk.xml\r\n"
        )
        self.assertEqual(
            edit_guest.parse_xml_list(capture),
            [
                "/etc/libvirt/qemu/a10desk.xml",
                "/etc/libvirt/qemu/a9test.xml",
                "/etc/libvirt/qemu/b_vm.xml",
            ],
        )

    def test_sed_update_memory_and_vcpu_via_bash_session(self):
        def run_in_session(session):
            xml_files = edit_guest.list_xml_files(session, target_xml_dir=self.temp_dir, sudo=False)
            self.assertEqual(xml_files, [self.test_xml_path])

            initial = edit_guest.get_vcpu_and_memory(session, self.test_xml_path, sudo=False)
            self.assertEqual(initial["vcpu"], 2)
            self.assertEqual(initial["memory_kib"], 2097152)
            self.assertEqual(initial["current_memory_kib"], 2097152)

            # Update memory to 4096 MB (4194304 KiB) and vcpu to 4 using sed in edit_guest
            edit_guest.edit_vm_xml(
                session,
                self.test_xml_path,
                vcpu=4,
                memory_mb=4096,
                define=False,
                sudo=False,
            )

            updated = edit_guest.get_vcpu_and_memory(session, self.test_xml_path, sudo=False)
            self.assertEqual(updated["vcpu"], 4)
            self.assertEqual(updated["memory_mb"], 4096)
            self.assertEqual(updated["memory_kib"], 4194304)
            self.assertEqual(updated["current_memory_kib"], 4194304)

        session_wrap.bash(log_params=log_param_templates.silent())(run_in_session)()

        with open(self.test_xml_path, "r", encoding="utf-8") as f:
            updated_xml = f.read()

        self.assertIn("<memory unit='KiB'>4194304</memory>", updated_xml)
        self.assertIn("<currentMemory unit='KiB'>4194304</currentMemory>", updated_xml)
        self.assertIn("<vcpu placement='static'>4</vcpu>", updated_xml)

    @patch("plur_linux.recipes.kvm.kvm_menu.edit_guest.get_input")
    @patch("plur_linux.recipes.kvm.kvm_menu.edit_guest.choose_num")
    @patch("plur_linux.recipes.kvm.kvm_menu.edit_guest.base_shell.run")
    def test_menu_on_kvm_flow(self, mock_run, mock_choose_num, mock_get_input):
        with open(self.test_xml_path, "r", encoding="utf-8") as f:
            initial_xml = f.read()

        session = MagicMock()
        mock_run.side_effect = [
            f"{self.test_xml_path}\n",  # ls -1
            initial_xml,                # cat (before edit)
            "",                         # sed vcpu
            "",                         # sed memory
            "",                         # virsh define
            initial_xml.replace(">2<", ">8<").replace("2097152", "8388608"),  # cat (after edit)
        ]
        mock_choose_num.return_value = 0
        mock_get_input.side_effect = ["8", "8192"]

        edit_guest.menu_on_kvm(session, target_xml_dir=self.temp_dir, sudo=True)

        mock_run.assert_any_call(
            session,
            f'sudo sed -i -E "s|(<vcpu[^>]*>)[0-9]+(</vcpu>)|\\18\\2|g" {self.test_xml_path}',
        )
        mock_run.assert_any_call(
            session,
            f'sudo sed -i -E '
            f'-e "s|(<memory[^>]*>)[0-9]+(</memory>)|\\18388608\\2|g" '
            f'-e "s|(<currentMemory[^>]*>)[0-9]+(</currentMemory>)|\\18388608\\2|g" '
            f'{self.test_xml_path}',
        )
        mock_run.assert_any_call(session, f"sudo virsh define {self.test_xml_path}")

    @patch("plur_linux.recipes.kvm.kvm_menu.runner.run_on")
    @patch("plur_linux.recipes.kvm.kvm_menu.runner.lib_kvm_module.select_kvm")
    @patch("plur_linux.recipes.kvm.kvm_menu.runner.choose_num")
    @patch("plur_linux.recipes.kvm.kvm_menu.runner.lib.list_kvm_guests")
    def test_runner_menu_on_kvm_has_edit_vm_after_ops(
        self, _mock_list_guests, mock_choose_num, mock_select_kvm, mock_run_on
    ):
        from plur_linux.recipes.kvm.kvm_menu import runner

        mock_select_kvm.return_value = MagicMock()
        captured_menus = []

        def fake_choose_num(items, *args, **kwargs):
            captured_menus.append(items)
            return len(items) - 1  # Select "Back"

        mock_choose_num.side_effect = fake_choose_num
        mock_run_on.side_effect = lambda _kvm, fn: fn(MagicMock())

        runner.menu_on_kvm()

        self.assertEqual(len(captured_menus), 1)
        menu_titles = captured_menus[0]
        ops_idx = menu_titles.index("Ops")
        self.assertEqual(menu_titles[ops_idx + 1], "Edit VM")


if __name__ == "__main__":
    unittest.main()
