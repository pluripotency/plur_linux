# plur_linux Kickstart共通化およびLVM+dataボリューム指定 実装計画

## 概要

`plur_linux/issue/plan02/TODO.md` および `plur_linux/issue/plan02/LVM+xfs_data_on_ks.md` の要求に基づき、PXEインストール用Kickstart生成処理（`src/plur_linux/recipes/pxe/kickstart.py`）のリファクタリングおよび機能拡張を行います。

### 目的
1. **AlmaLinux 8/9 と AlmaLinux 10 の Kickstart 生成ロジックの統合**:
   `create_a10_ks_str` と `create_ks_str` の差分は `timezone` / `timesource` の構文のみであるため、共通部分を抽出し、引数 `a10=True/False` 等で切り替え可能にします。
2. **ストレージ・ボリューム構成のモジュール化**:
   固定化されていたパーティション設定を切り出し、通常パーティション（全容量 `/` 割り当て）に加えて、`LVM+xfs_data_on_ks.md` に記載の「LVM + 50GB root + 8GB swap + 残り全容量 `/data`」構成を生成可能にします。
3. **`phy/vda/sda` の LVM Kickstart ファイル生成**:
   `prepare_ks` において、従来の `phy.ks`, `vda.ks`, `sda.ks` に加え、LVM構成の `phy_lvm.ks`, `vda_lvm.ks`, `sda_lvm.ks` を生成できるようにします。

---

## 現状の課題分析

### 課題1: コードの重複 (`create_a10_ks_str` vs `create_ks_str`)
`src/plur_linux/recipes/pxe/kickstart.py` において、`create_a10_ks_str` と `create_ks_str` は約40行のテンプレート文字列がほぼ同一であり、以下の2行のみが異なっています：
- AlmaLinux 8/9 (`create_ks_str`):
  ```kickstart
  timezone Asia/Tokyo --isUtc --nontp
  ```
- AlmaLinux 10 (`create_a10_ks_str`):
  ```kickstart
  timezone Asia/Tokyo --utc
  timesource --ntp-disable
  ```
この重複により、パッケージ定義やネットワーク設定、ブートローダー設定を変更する際に両方を二重修正する必要があり、保守性の低下を招いています。

### 課題2: パーティション設定が固定化されている
現在、Kickstartテンプレート内に以下のパーティション設定がハードコーディングされています：
```kickstart
zerombr
clearpart --all --initlabel
part /boot --fstype="ext4" --ondisk={disk_dev} --size=2048
part /boot/efi --fstype="vfat" --ondisk={disk_dev} --size=512
part / --fstype xfs --grow --size=1
```
ディスク全体を単一の `/` に割り当てる設定しか存在せず、LVM構成や `/data` 分割を必要とするサーバー要件（`LVM+xfs_data_on_ks.md`）に対応できません。

---

## 提案する設計方針

### 1. タイムゾーン／タイムソース設定の分離 (`create_timezone_str`)
ディストリビューションバージョンに応じた設定行を生成する小さな関数として切り出します。
```python
def create_timezone_str(a10=False) -> str:
    if a10:
        return misc.del_indent("""
        timezone Asia/Tokyo --utc
        timesource --ntp-disable
        """).strip()
    else:
        return "timezone Asia/Tokyo --isUtc --nontp"
```

### 2. ボリューム／パーティション生成関数の分離
ボリューム構成を独立したビルダー関数として定義します。

#### A. 通常パーティション構成 (`create_standard_volume_str`)
従来の構成を維持（後方互換性）：
```python
def create_standard_volume_str(disk_dev='sda') -> str:
    return misc.del_indent(f"""
    # パーティションテーブルは全て初期化
    zerombr
    clearpart --all --initlabel
    part /boot --fstype="ext4" --ondisk={disk_dev} --size=2048
    part /boot/efi --fstype="vfat" --ondisk={disk_dev} --size=512
    part / --fstype xfs --grow --size=1
    """).strip()
```

#### B. LVM + data ボリューム構成 (`create_lvm_data_volume_str`)
`LVM+xfs_data_on_ks.md` の仕様に準拠した構成：
- `/boot/efi`: 600MB (`--fstype="efi" --ondisk={disk_dev}`)
- `/boot`: 1024MB (`--fstype="xfs" --ondisk={disk_dev}`)
- `pv.01`: 残り全容量を PV に割り当て (`--fstype="lvmpv" --size=1 --grow --ondisk={disk_dev}`)
- `volgroup vg_system pv.01`
- `logvol /`: 50GB固定 (51200MB, `--name=lv_root --vgname=vg_system`)
- `logvol swap`: 8GB固定 (8192MB, `--name=lv_swap --vgname=vg_system`)
- `logvol /data`: 残り全容量 (`--size=1 --grow --name=lv_data --vgname=vg_system`)
```python
def create_lvm_data_volume_str(
    disk_dev='sda',
    root_size_mb=51200,
    swap_size_mb=8192,
    vg_name='vg_system',
) -> str:
    return misc.del_indent(f"""
    # ストレージ・パーティション設定 (UEFI / LVM + XFS)
    zerombr
    clearpart --all --initlabel

    # 1. UEFI ブート用必須パーティション (/boot/efi)
    part /boot/efi --fstype="efi" --size=600 --ondisk={disk_dev}

    # 2. ブートパーティション (/boot)
    part /boot --fstype="xfs" --size=1024 --ondisk={disk_dev}

    # 3. LVM 物理ボリューム (PV) の作成 (残りを全割り当て)
    part pv.01 --fstype="lvmpv" --size=1 --grow --ondisk={disk_dev}

    # 4. ボリュームグループ (VG) の構築
    volgroup {vg_name} pv.01

    # 5. 論理ボリューム (LV) の切り分け
    logvol / --fstype="xfs" --size={root_size_mb} --name=lv_root --vgname={vg_name}
    logvol swap --fstype="swap" --size={swap_size_mb} --name=lv_swap --vgname={vg_name}
    logvol /data --fstype="xfs" --size=1 --grow --name=lv_data --vgname={vg_name}
    """).strip()
```

### 3. 統合 `create_ks_str` 関数の定義
共通テンプレートを1箇所に集約し、`a10` フラグおよび `volume_type` を受け取るシグネチャとします：
```python
def create_ks_str(
    dist_url='',
    disk_dev='sda',
    with_console=True,
    a10=False,
    volume_type='standard',
    volume_str=None,
    root_size_mb=51200,
    swap_size_mb=8192,
) -> str:
    ...
```
- `volume_str` が直接渡された場合はそれを優先。
- `volume_type in ('lvm', 'lvm_data')` の場合は `create_lvm_data_volume_str` を使用。
- デフォルトは `create_standard_volume_str`。

#### 既存関数 `create_a10_ks_str` の互換ラッパー
外部から `create_a10_ks_str(...)` を呼び出しているコードがあっても破損しないよう、引数を透過的に渡すラッパーとして残します：
```python
def create_a10_ks_str(dist_url='', disk_dev='sda', with_console=True, volume_type='standard', **kwargs):
    return create_ks_str(dist_url=dist_url, disk_dev=disk_dev, with_console=with_console, a10=True, volume_type=volume_type, **kwargs)
```

### 4. `prepare_ks` による `phy/vda/sda` の LVM Kickstart 生成
`prepare_ks` を改修し、標準構成（`phy.ks`, `vda.ks`, `sda.ks`）に加えて LVM構成のファイルも生成して返却します：
- `phy_lvm.ks` (`sda`, `with_console=False`, `volume_type='lvm_data'`)
- `vda_lvm.ks` (`vda`, `with_console=True`, `volume_type='lvm_data'`)
- `sda_lvm.ks` (`sda`, `with_console=True`, `volume_type='lvm_data'`)

`pxe.py` の `create_pxe_menu_str` および `create_grub_cfg_str` は `prepare_ks` の戻り値リストをそのまま反復処理するため、PXEブートメニュー（BIOS / UEFI GRUB）に自動的に各エントリーが反映されます：
- `Install AlmaLinux with phy.ks`
- `Install AlmaLinux with vda.ks`
- `Install AlmaLinux with sda.ks`
- `Install AlmaLinux with phy_lvm.ks`
- `Install AlmaLinux with vda_lvm.ks`
- `Install AlmaLinux with sda_lvm.ks`

---

## User Review Required

> [!IMPORTANT]
> **Kickstartファイル名に関する確認**
> LVM構成用のKickstartファイル名として、既存の命名規則（`phy.ks`, `vda.ks`, `sda.ks`）に合わせ、
> - `phy_lvm.ks`
> - `vda_lvm.ks`
> - `sda_lvm.ks`
> 
> を提案しています。もし `phy_data.ks` や `phy-lvm.ks` などの別名のご希望があればご指定ください。

> [!NOTE]
> **パーティションサイズおよびディスク要件**
> LVM構成では `/boot` (1GB) + `/boot/efi` (600MB) + `root` (50GB) + `swap` (8GB) で合計約60GBを初期消費します。
> そのため、対象ストレージの総容量が64GB以上必要となります。小容量の仮想マシン等では引き続き標準構成（`vda.ks` 等）を選択可能です。

---

## Open Questions

1. **`prepare_ks` の生成対象について**:
   標準構成（3種）とLVM構成（3種）の計6ファイルを常に生成する方針（推奨）でよいでしょうか？
   （オプション引数 `include_lvm=True` を設け、必要に応じて制御可能とします）

---

## Proposed Changes

### PXE レシピ層

#### [MODIFY] [kickstart.py](file:///home/worker/Documents/antigravity/plur_linux/src/plur_linux/recipes/pxe/kickstart.py)
- `create_timezone_str(a10=False)` を追加
- `create_standard_volume_str(disk_dev='sda')` を追加
- `create_lvm_data_volume_str(disk_dev='sda', root_size_mb=51200, swap_size_mb=8192, vg_name='vg_system')` を追加
- `create_ks_str` を統合し、`a10`, `volume_type`, `volume_str` 引数をサポート
- `create_a10_ks_str` を後方互換ラッパーに変更
- `prepare_ks` を更新し、`phy_lvm.ks`, `vda_lvm.ks`, `sda_lvm.ks` を生成リストに追加

---

### テストコード

#### [NEW] [test_kickstart.py](file:///home/worker/Documents/antigravity/plur_linux/tests/test_kickstart.py)
- `create_timezone_str` の出力検証（a10=True vs a10=False）
- `create_standard_volume_str` および `create_lvm_data_volume_str` の構文・ディスク名展開の検証
- `create_ks_str` の統合動作検証（AlmaLinux 8/9/10, standard/lvm_data, 各ディスク種別）
- `prepare_ks` の戻り値リストおよびファイル内容の単体テスト（モックセッション使用）

---

### ドキュメント

#### [MODIFY] [TODO.md](file:///home/worker/Documents/antigravity/plur_linux/issue/plan02/TODO.md)
- 実装完了状態および決定仕様の更新

---

## Verification Plan

### Automated Tests
1. **単体テストの実行**:
   ```bash
   /home/worker/Documents/antigravity/plur_linux/.venv/bin/python -m unittest tests/test_kickstart.py
   ```
2. **全テストスイートの実行**:
   ```bash
   /home/worker/Documents/antigravity/plur_linux/.venv/bin/python -m unittest discover tests
   ```
3. **モジュールインポート検証**:
   ```bash
   /home/worker/Documents/antigravity/plur_linux/.venv/bin/python -c "from plur_linux.recipes.pxe import kickstart, pxe; print('Kickstart & PXE modules imported successfully')"
   ```

### Manual Verification
1. **Kickstart構文の出力確認**:
   テストスクリプト上で `create_ks_str(dist_url='http://192.168.0.10/almalinux10', disk_dev='vda', a10=True, volume_type='lvm_data')` を呼び出し、期待通りのKickstart定義テキストが出力されることを目視確認。
2. **PXEメニュー連動の確認**:
   `pxe.create_pxe_menu_str` および `pxe.create_grub_cfg_str` に `ks_filename_list`（6件）を渡し、メニューエントリーが崩れず正しく生成されることを確認。
