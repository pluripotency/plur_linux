Viewed kickstart.py:1-122
Created kickstart.py
Created test_kickstart.py
Ran command: `/home/worker/Documents/antigravity/plur_linux/.venv/bin/python -m unittest tests/test_kickstart.py`
Searched for "def del_indent"
Viewed misc.py:100-125
Created kickstart.py
Ran command: `/home/worker/Documents/antigravity/plur_linux/.venv/bin/python -m unittest tests/test_kickstart.py`
Ran command: `/home/worker/Documents/antigravity/plur_linux/.venv/bin/python -m unittest discover tests`
Ran command: `/home/worker/Documents/antigravity/plur_linux/.venv/bin/python -m doctest src/plur_linux/recipes/pxe/pxe.py`
Viewed TODO.md:1-7
Edited TODO.md
Ran command: `git status`
Viewed walkthrough.md:1-60
Created walkthrough.md

ご指示に基づき、[issue/plan02/TODO.md](file:///home/worker/Documents/antigravity/plur_linux/issue/plan02/TODO.md) の要件および承認いただいた方針に従って、実装・テスト・ドキュメント更新を完了しました。

### 成果物のまとめ

1. **実装計画書**:
   - [plur_linux/issue/plan02/implementation_plan.md](file:///home/worker/Documents/antigravity/plur_linux/issue/plan02/implementation_plan.md)
2. **ウォークスルー（変更詳細・検証結果）**:
   - [walkthrough.md](file:///home/worker/.gemini/antigravity/brain/66f3c248-e369-4159-a457-fce703af6b38/walkthrough.md)

---

### 主な実装内容

1. **Kickstart生成処理の共通化**:
   - [`src/plur_linux/recipes/pxe/kickstart.py`](file:///home/worker/Documents/antigravity/plur_linux/src/plur_linux/recipes/pxe/kickstart.py)
   - `create_timezone_str(a10=False)` を新設し、AlmaLinux 8/9 (`--isUtc --nontp`) と AlmaLinux 10 (`--utc` + `timesource --ntp-disable`) の差分を吸収。
   - `create_ks_str` にテンプレートを統合し、引数 `a10=True/False` で指定可能にしました。
   - 既存の `create_a10_ks_str` は後方互換ラッパーとして維持。

2. **ストレージ・ボリューム構成のモジュール化**:
   - `create_standard_volume_str(disk_dev)`: 従来の全容量 `/` 割り当て構成。
   - `create_lvm_data_volume_str(disk_dev, root_size_mb=51200, swap_size_mb=8192, vg_name='vg_system')`:
     - [LVM+xfs_data_on_ks.md](file:///home/worker/Documents/antigravity/plur_linux/issue/plan02/LVM+xfs_data_on_ks.md) 準拠（`/boot/efi` 600MB、`/boot` 1024MB、PV全割り当て、VG `vg_system`、root 50GB固定、swap 8GB、`/data` 残り全容量）。

3. **`prepare_ks` による `phy/vda/sda` 向け LVM Kickstart 生成**:
   - 以下の計6ファイルを生成してPXEサーバーへ配置・メニュー展開するように拡張：
     1. `phy.ks`: sda / コンソール無 / 標準構成
     2. `vda.ks`: vda / コンソール有 / 標準構成
     3. `sda.ks`: sda / コンソール有 / 標準構成
     4. `phy_lvm.ks`: sda / コンソール無 / LVM構成 (50G root + 8G swap + 残り `/data`)
     5. `vda_lvm.ks`: vda / コンソール有 / LVM構成
     6. `sda_lvm.ks`: sda / コンソール有 / LVM構成

4. **TODOの更新**:
   - [plur_linux/issue/plan02/TODO.md](file:///home/worker/Documents/antigravity/plur_linux/issue/plan02/TODO.md) を完了状態に更新。

---

### テスト結果

`plur_linux/.venv/bin/python` による単体テストおよび doctest を実行し、全テストがパスすることを確認しました：
```bash
/home/worker/Documents/antigravity/plur_linux/.venv/bin/python -m unittest discover tests
# Ran 16 tests in 0.004s -> OK

/home/worker/Documents/antigravity/plur_linux/.venv/bin/python -m doctest src/plur_linux/recipes/pxe/pxe.py
# OK (Exit Code 0)
```
