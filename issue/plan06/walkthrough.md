# Walkthrough: `--print-xml 1` + `virsh define` / `virsh start` 経路の追加

## 変更内容

1. **XML 出力用 `virt-install` コマンド生成の追加**
   - [virt_install_str.py](../../src/plur_linux/recipes/kvm/virt_install_str.py): `virt_install_define_xml_options`（`--events on_reboot=restart`、`--print-xml 1`）および `virt_install_print_xml_str`（doctest 付き）を追加しました。

2. **`start_domain_by_define_xml` と `do_definexml` 分岐の追加**
   - [spawn.py](../../src/plur_linux/recipes/kvm/spawn.py):
     - `_build_virt_install_option_list` にオプション組み立て処理を共通化しました。
     - `start_domain_by_define_xml` を追加し、`/tmp/{hostname}.xml` への単一 XML 出力 → `sed` による `<on_reboot>restart</on_reboot>` 置換 → `sudo virsh define` → `sudo virsh start` を実行するようにしました。
     - `DEFAULT_DEFINE_XML = True`（および `DEFAULT_RESTART_BEFORE_SETUP = True`）を定義し、`should_define_xml`・`should_restart_before_setup`・`get_vm_boot_mode_label` のデフォルト値をこの定数1箇所から参照するよう集約しました。
     - `create_vm_by_virt_install_cloudinit` に `do_definexml` を追加し、`True`（デフォルト）の場合は `start_domain_by_define_xml` → `on_create_console_with_cloudinit` → `eject_seed_iso` の経路を実行するようにしました。

3. **メニュー選択肢・履歴表示の共通化（`spawn.py` の `DEFAULT_DEFINE_XML` 1行変更で切り替え可能）**
   - [lib.py](../../src/plur_linux/recipes/kvm/kvm_menu/lib.py): `select_define_xml`・`select_restart_before_setup`・`select_vm_boot_options` に集約し、デフォルト値はすべて `spawn.py` の定数を参照する構成にしました。
   - [runner.py](../../src/plur_linux/recipes/kvm/kvm_menu/runner.py)、[create_guest.py](../../src/plur_linux/recipes/kvm/kvm_menu/create_guest.py)、[select_post_run.py](../../src/plur_linux/recipes/kvm/adhoc_setup/select_post_run.py): すべて `select_vm_boot_options` 呼び出し1行に統一しました。
   - [select_post_run.py](../../src/plur_linux/recipes/kvm/adhoc_setup/select_post_run.py)、[adhoc_history.py](../../src/plur_linux/recipes/kvm/adhoc_setup/adhoc_history.py): モードラベル判定も `spawn.get_vm_boot_mode_label` に統一し、メニュー・履歴サマリに `mode:definexml` が表示されるようにしました。

4. **ユニットテストの追加**
   - [test_spawn_define_xml.py](../../tests/test_spawn_define_xml.py): `should_define_xml`、`start_domain_by_define_xml` の実行コマンド列、`create_vm_by_virt_install_cloudinit` の全3分岐、`mode:definexml` 表示、および `DEFAULT_DEFINE_XML` 単一定数による一括切り替えのテストを追加しました。

## テスト・検証結果

- **doctest**: `PYTHONPATH=src .venv/bin/python -m doctest -v src/plur_linux/recipes/kvm/virt_install_str.py` → 全 6 テストパス
- **unittest**: `PYTHONPATH=src .venv/bin/python -m unittest -v tests/test_spawn_define_xml.py` → 全 8 テストパス
- **実機確認**: `definexml` 経路での動作確認完了に伴い、`DEFAULT_DEFINE_XML = True`（`[Y/n]`）をデフォルトに設定しました。
