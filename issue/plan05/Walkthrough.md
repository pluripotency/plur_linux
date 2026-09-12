# plur_linux 実装完了ウォークスルー

## 目次
- [Plan 01: セグメント仕様変更およびIP計算ロジック集約](#plan-01-セグメント仕様変更およびip計算ロジック集約)
- [Plan 02: Kickstart共通化およびLVM+dataボリューム指定](#plan-02-kickstart共通化およびlvmdataボリューム指定)
- [Plan 03: env_opsセグメントに基づくdhcpd.conf動的生成およびDHCP範囲計算](#plan-03-env_opsセグメントに基づくdhcpdconf動的生成およびdhcp範囲計算)
- [Plan 04: Kickstartにおけるenv_opsユーザー設定・iscryptedパスワード・sudo(wheel)連携](#plan-04-kickstartにおけるenv_opsユーザー設定iscryptedパスワードsudowheel連携)
- [Plan 05: Docker Compose による PXE ベースサービス (Nginx, Kea DHCP, TFTP) 構築](#plan-05-docker-compose-による-pxe-ベースサービス-nginx-kea-dhcp-tftp-構築)

---

## Plan 01: セグメント仕様変更およびIP計算ロジック集約

### 概要
従来の `/24` 前提の `ip_base_prefix` + `prefix` 方式から、CIDRプレフィックス（`/22` や `/16` など）に対応した `network_with_prefix` 方式への移行と、コード内に散在していたIP計算ロジックの集約を完了しました。

### 変更内容のまとめ
1. **コアIP計算モジュール**: [`src/plur_linux/lib/ip_calc.py`](file:///home/worker/Documents/antigravity/plur_linux/src/plur_linux/lib/ip_calc.py)
   - `calc_ip`: `1` (int) で `172.16.0.1`、`'1.5'` (str) で `172.16.1.5`、`'4.1'` で `'IP Range Error'` を返却。
   - オプションBの要件（有効ホスト範囲のみ正常、ネットワークアドレス・ブロードキャストアドレスは `'IP Range Error'`）を準拠。
   - `get_segment_network`: 旧環境辞書 (`ip_base_prefix` / `prefix`) からの自動フォールバック。
   - `get_ip_from_segment`: 統一されたセグメントIP導出インターフェース。
2. **セグメント管理層**: [`src/plur_linux/lib/env_ops.py`](file:///home/worker/Documents/antigravity/plur_linux/src/plur_linux/lib/env_ops.py)
   - TOML定義を `network_with_prefix` に更新し、`bind_env` を改修。
3. **ノード生成 & レシピ層**:
   - [`new_node.py`](file:///home/worker/Documents/antigravity/plur_linux/src/plur_linux/nodes/new_node.py): ドット記法IPシードの入力を許可。
   - [`kubeadm_a9.py`](file:///home/worker/Documents/antigravity/plur_linux/src/plur_linux/nodes/guests/kubeadm_a9.py), [`gluster.py`](file:///home/worker/Documents/antigravity/plur_linux/src/plur_linux/nodes/guests/gluster.py): 文字列結合を `get_ip_from_segment` に置換。

---

## Plan 02: Kickstart共通化およびLVM+dataボリューム指定

### 概要
`src/plur_linux/recipes/pxe/kickstart.py` において、AlmaLinux 8/9 と AlmaLinux 10 で重複していたKickstartテンプレートを共通化し、さらにハードコードされていたストレージ設定をモジュール化して、`LVM+xfs_data_on_ks.md` に準拠した「LVM + 50GB root + 8GB swap + 残り /data」の構成を `phy/vda/sda` で利用できるように拡張しました。

### 変更内容のまとめ

#### 1. タイムゾーン・タイムソース設定の分離
- **関数**: `create_timezone_str(a10=False)`
  - `a10=False`: `timezone Asia/Tokyo --isUtc --nontp` (AlmaLinux 8/9 用)
  - `a10=True`: `timezone Asia/Tokyo --utc\ntimesource --ntp-disable` (AlmaLinux 10 用)

#### 2. ボリューム・パーティション構成のモジュール化
- **通常パーティション**: `create_standard_volume_str(disk_dev='sda')`
  - `/boot` (2GB ext4), `/boot/efi` (512MB vfat), `/` (残り全容量 xfs --grow)
- **LVM + /data パーティション**: `create_lvm_data_volume_str(disk_dev='sda', root_size_mb=51200, swap_size_mb=8192, vg_name='vg_system')`
  - `/boot/efi`: 600MB efi
  - `/boot`: 1024MB xfs
  - `pv.01`: 残り全容量 (`--size=1 --grow`)
  - `volgroup vg_system pv.01`
  - `logvol /`: 50GB固定 (51200MB, lv_root, xfs)
  - `logvol swap`: 8GB固定 (8192MB, lv_swap, swap)
  - `logvol /data`: 残り全容量自動割り当て (`--size=1 --grow`, lv_data, xfs)

#### 3. Kickstart生成関数の統合
- **関数**: `create_ks_str(...)`
  - 引数 `a10=True/False`、`volume_type='standard'/'lvm_data'`、`volume_str=None`、`disk_dev='sda'`、`with_console=True/False` をサポート。
  - テンプレートのインデント処理を最適化し、安全に各セクションを合成。
- **互換ラッパー**: `create_a10_ks_str(...)`
  - 既存の外部呼び出し元への後方互換性を保持。

#### 4. `prepare_ks` による phy/vda/sda の標準および LVM Kickstart 生成
- **関数**: `prepare_ks(session, pxe_ip, dist_dir, a10=False, include_lvm=True)`
  - 生成対象ファイル一覧（計6ファイル）:
    1. `phy.ks`: sda, コンソール無, standard
    2. `vda.ks`: vda, コンソール有, standard
    3. `sda.ks`: sda, コンソール有, standard
    4. `phy_lvm.ks`: sda, コンソール無, lvm_data (50G root + 8G swap + 残り /data)
    5. `vda_lvm.ks`: vda, コンソール有, lvm_data
    6. `sda_lvm.ks`: sda, コンソール有, lvm_data
  - PXEサーバー（BIOSメニューおよびUEFI GRUBメニュー）から6つのエントリーが即座に選択可能。

---

## Plan 03: env_opsセグメントに基づくdhcpd.conf動的生成およびDHCP範囲計算

### 概要
`src/plur_linux/recipes/pxe/dhcpd.py` および `src/plur_linux/recipes/pxe/pxe.py` において、`env_ops` で定義されたセグメント情報（または明示指定されたセグメント）に基づいて `dhcpd.conf` および PXE/HTTP 許可設定を動的に生成する機能を追加しました。
DHCPレンジはセグメント後半の4分の1とし、末尾4つの使用可能ホストIP（およびブロードキャスト）を除外して安全に割り当てます。また、従来の `192.168.0.` / `192.168.10.` のハードコード分岐を解消しました。

### 変更内容のまとめ

#### 1. DHCPレンジ計算ロジック
- **関数**: `calc_dhcp_range(net: ipaddress.IPv4Network)`
  - セグメント全体の 3/4 地点を開始IPとし、末尾（ブロードキャスト - 5）を終了IPとして計算。
  - 例 (`192.168.0.0/24` の場合):
    - `total = 256`
    - `start_ip = 192.168.0.192`
    - `end_ip = 192.168.0.250`
    - 末尾4つのホストIP (`.251`, `.252`, `.253`, `.254`) およびブロードキャスト (`.255`) を確実に除外。
  - `/29` などの小規模サブネットでは、自動的に使用可能なホスト範囲（`network + 1` 〜 `broadcast - 1`）に安全にフォールバック。

#### 2. セグメント検索およびパラメータ生成
- **関数**: `find_segment_for_ip(ip_str, segments=None)`
  - 指定されたIP（またはCIDR付きIP）が `env_ops` のセグメントに含まれているかを判定。
- **関数**: `create_subnet_params_from_segment(segment)`
  - セグメント定義から `subnet`, `netmask`, `gateway`, `nameservers`, `dh_range`, `broadcast`, `domain_name`, `domain_name_servers`, `allowed_net` を生成。
- **関数**: `get_subnet_params(pxe_ip=None, segment=None, segments=None)`
  - セグメント指定時、または `pxe_ip` による自動判定により最適な `subnet_params` を導出。未登録IP時は `/24` 動的フォールバックを実施。

#### 3. PXE / HTTP設定との連携
- [`dhcpd.py`](file:///home/worker/Documents/antigravity/plur_linux/src/plur_linux/recipes/pxe/dhcpd.py):
  - `create_pre_str` および `create_pxe_pre_str` で動的 `domain_name` / `domain_name_servers` をサポートし、既存の doctest エラーを修正。
  - `dhcpd.setup(subnet_params=None, set_fw=True, pxe_ip=False, segment=None)` で `segment` の直接指定または `pxe_ip` からの自動導出に対応。
- [`pxe.py`](file:///home/worker/Documents/antigravity/plur_linux/src/plur_linux/recipes/pxe/pxe.py):
  - `setup_pxe_base(pxe_ip, dist_dir, www_iso_dir, segment=None)` でハードコード分岐を `dhcpd.get_subnet_params` に置換。
  - `setup_a8_pxe_uefi`, `setup_a8_pxe`, `setup_a9_pxe_uefi`, `setup_a9_pxe`, `setup_a10_pxe_uefi`, `setup_a10_pxe` に `segment=None` 引数を追加。

---

## 検証結果

### 1. 単体テスト (`tests/test_dhcpd.py`)
DHCPレンジ計算、末尾4IP除外、小規模サブネットフォールバック、セグメント検索、各種パラメータ生成を検証する11件のテストを作成・実行：
```bash
/home/worker/Documents/antigravity/plur_linux/.venv/bin/python -m unittest tests/test_dhcpd.py
```
**結果**:
```
...........
----------------------------------------------------------------------
Ran 11 tests in 0.001s

OK
```

### 2. 全テストスイート実行
```bash
/home/worker/Documents/antigravity/plur_linux/.venv/bin/python -m unittest discover tests
```
**結果**: 全27件の単体テストすべて成功
```
...........................
----------------------------------------------------------------------
Ran 27 tests in 0.005s

OK
```

### 3. Doctest 実行
```bash
/home/worker/Documents/antigravity/plur_linux/.venv/bin/python -m doctest src/plur_linux/recipes/pxe/dhcpd.py
/home/worker/Documents/antigravity/plur_linux/.venv/bin/python -m doctest src/plur_linux/recipes/pxe/pxe.py
```
**結果**: 既存の doctest 不備も解消され、すべて成功（Exit Code 0）

---

## Plan 04: Kickstartにおけるenv_opsユーザー設定・iscryptedパスワード・sudo(wheel)連携

### 概要
`src/plur_linux/recipes/pxe/kickstart.py` において、`env_ops` で定義された `account_set`（または引数で明示指定された `account_set`）を参照し、`root` パスワードおよび一般ユーザー（`user`）を動的に Kickstart 設定へ反映する機能を実装しました。
また、Python 依存関係を `>=3.13`（CPython 3.13.14）に引き上げ、標準の SHA-512 crypt パスワード生成として `passlib`（`sha512_crypt`）を導入しました。

### 変更内容のまとめ

#### 1. Python バージョンおよび依存パッケージ更新
- [`pyproject.toml`](file:///home/worker/Documents/antigravity/plur_linux/pyproject.toml):
  - `requires-python = ">=3.13"` に更新。
  - `passlib>=1.7.4` を `dependencies` に追加。
- `.python-version`: `3.13` に固定。
- 仮想環境（`.venv`）を CPython 3.13.14 で再構築し、`passlib` 等の全パッケージを導入。

#### 2. パスワード暗号化 (`iscrypted`)
- **関数**: `encrypt_password(password: str, rounds: int = None) -> str`
  - パスワードを SHA-512 crypt 形式（`$6$...`）でハッシュ化。
  - すでに `$` から始まる暗号化済み文字列（例: `$1$...`, `$6$...`）が渡された場合はそのまま保持し、二重暗号化を防止。
  - `passlib.hash.sha512_crypt` を標準使用（未導入環境用のフォールバックも保持）。

#### 3. Kickstart ユーザーおよび rootpw 生成
- **関数**: `create_account_str(account_set=None) -> str`
  - `account_set` が未指定の場合、`env_ops.EnvAccountSet` のカレントアカウント設定（または `default_account_set`）から自動取得。
  - `rootpw --iscrypted <hashed_root_password>` を生成。
  - 一般ユーザー（`username` が指定され、かつ `root` 以外）が存在する場合:
    - `user --name=<username> --password=<hashed_user_password> --iscrypted` を生成。
    - `sudoers=True` の場合は `--groups=wheel` を付加し、sudo 実行権限を付与。
    - `sudoers=False` の場合は `--groups=wheel` を付加しない。

#### 4. PXE レシピ連携
- [`kickstart.py`](file:///home/worker/Documents/antigravity/plur_linux/src/plur_linux/recipes/pxe/kickstart.py):
  - `create_ks_str` に `account_set=None` 引数を追加し、ハードコードされていた旧 MD5 パスワードを `create_account_str` の出力に置換。
  - `prepare_ks` に `account_set=None` 引数を追加し、各 `.ks` ファイル生成に伝播。
- [`pxe.py`](file:///home/worker/Documents/antigravity/plur_linux/src/plur_linux/recipes/pxe/pxe.py):
  - `setup_a8_pxe_uefi`, `setup_a8_pxe`, `setup_a9_pxe_uefi`, `setup_a9_pxe`, `setup_a10_pxe_uefi`, `setup_a10_pxe` に `account_set=None` を追加。

---

## 検証結果 (Plan 04)

### 1. 単体テスト (`tests/test_kickstart.py`)
暗号化パスワード生成、平文ハッシュ検証、暗号化済み文字列の非重複暗号化、デフォルトユーザー/wheel付与、sudoers=False時のwheel除外、root単独時のuser行スキップ、カスタムアカウントセット反映を含む計12件のテストを実行：
```bash
/home/worker/Documents/antigravity/plur_linux/.venv/bin/python -m unittest tests/test_kickstart.py
```
**結果**: 12件すべてパス
```
............
----------------------------------------------------------------------
Ran 12 tests in 5.974s

OK
```

### 2. 全テストスイート実行
```bash
/home/worker/Documents/antigravity/plur_linux/.venv/bin/python -m unittest discover tests
```
**結果**: 全32件の単体テストすべて成功 (Python 3.13)
```
................................
----------------------------------------------------------------------
Ran 32 tests in 6.024s

OK
```

### 3. Doctest 実行
```bash
/home/worker/Documents/antigravity/plur_linux/.venv/bin/python -m doctest src/plur_linux/recipes/pxe/dhcpd.py
/home/worker/Documents/antigravity/plur_linux/.venv/bin/python -m doctest src/plur_linux/recipes/pxe/pxe.py
```
**結果**: すべて成功（Exit Code 0）

---

## Plan 05: Docker Compose による PXE ベースサービス (Nginx, Kea DHCP, TFTP) 構築

### 概要
`src/plur_linux/recipes/pxe/compose.py` を新規作成し、従来のホスト常駐型サービス（Apache httpd、ISC dhcpd、tftp-server）による `setup_pxe_base` を、Docker Compose 上のコンテナ（Nginx, ISC Kea DHCP, TFTP-HPA）として一括デプロイ・管理可能にしました。
また、`src/plur_linux/recipes/pxe/pxe.py` に `setup_pxe_base_by_docker` を新設し、各ディストリビューション設定関数から `use_docker=True` で呼び出せるようにしました。

### 変更内容のまとめ

#### 1. 新規モジュール: `src/plur_linux/recipes/pxe/compose.py`
- **`create_nginx_conf_str(alias, dir_path, allowed_net=None) -> str`**:
  - Nginx（`nginx:alpine`）用設定を生成。
  - ルート `/var/www/html`、Kickstart 用 `/ks` エイリアス、ISO 用 `/{dist_dir}` エイリアス、`autoindex on` を設定。
  - `allowed_net` 指定時は `allow 127.0.0.1; allow {allowed_net}; deny all;` によるアクセス制御を設定。
- **`create_kea_conf_str(pxe_ip, subnet_params) -> str`**:
  - ISC Kea DHCPv4（`isc/kea-dhcp4:latest`）用 JSON 設定を生成。
  - `interfaces: ["*"]`、スタンドアロン `memfile` リースDB、サブネット・プール（`start - end`）、ルーター、DNS、`next-server` を設定。
  - クライアントクラス判定（Option 93 による UEFI 0x0007/0x0009 は `BOOTX64.EFI`、BIOS は `pxelinux.0`）による起動ファイル自動切替を設定。
- **`create_docker_compose_str(...) -> str`**:
  - `nginx`, `kea`, `tftpd`（`ghcr.io/linuxserver/tftp-hpa:latest`）の 3 サービスを含む `docker-compose.yml` を生成。
  - ブロードキャスト UDP および HTTP を直接処理するため、全サービスに `network_mode: host` を適用。
  - ホスト側の `/var/www/html`, `/var/lib/tftpboot`, `www_iso_dir` および設定ファイルをコンテナへマウント。
- **`prepare_compose_files(...)`**:
  - 指定ディレクトリ（デフォルト `/etc/pxe-docker`）に設定ファイル群を配置。
- **`setup_pxe_compose(...)`**:
  - firewalld 設定、ディレクトリ作成、設定ファイル配置、`docker compose up -d` による起動を行う関数を生成。

#### 2. PXE オーケストレーション連携: `src/plur_linux/recipes/pxe/pxe.py`
- **`setup_pxe_base_by_docker(pxe_ip, dist_dir, www_iso_dir, segment=None, compose_dir='/etc/pxe-docker')`**:
  - `compose.setup_pxe_compose` を呼び出す互換関数を新設。
- **ディストリビューション設定関数の拡張**:
  - `setup_a8_pxe_uefi`, `setup_a8_pxe`, `setup_a9_pxe_uefi`, `setup_a9_pxe`, `setup_a10_pxe_uefi`, `setup_a10_pxe` にオプション引数 `use_docker=False`, `compose_dir='/etc/pxe-docker'` を追加し、`use_docker=True` で Docker Compose ベースの起動を実行可能に拡張。

---

## 検証結果 (Plan 05)

### 1. 単体テスト (`tests/test_compose.py`)
Nginx 設定構文・アクセス制御、Kea JSON 構文・プール・Option 93 クライアントクラス、docker-compose YAML 構文・host ネットワークモード・マウント、`prepare_compose_files` モックフロー、`setup_pxe_compose` 実行フロー、`pxe.setup_pxe_base_by_docker` 委譲をカバーする計 7 件のテストを作成・実行：
```bash
/home/worker/Documents/antigravity/plur_linux/.venv/bin/python -m unittest tests/test_compose.py
```
**結果**: 7 件すべて成功
```
.......
----------------------------------------------------------------------
Ran 7 tests in 0.002s

OK
```

### 2. 全テストスイート実行
```bash
/home/worker/Documents/antigravity/plur_linux/.venv/bin/python -m unittest discover tests
```
**結果**: 全 39 件の単体テストすべて成功
```
.......................................
----------------------------------------------------------------------
Ran 39 tests in 6.196s

OK
```

### 3. Doctest 実行
```bash
/home/worker/Documents/antigravity/plur_linux/.venv/bin/python -m doctest src/plur_linux/recipes/pxe/compose.py
/home/worker/Documents/antigravity/plur_linux/.venv/bin/python -m doctest src/plur_linux/recipes/pxe/dhcpd.py
/home/worker/Documents/antigravity/plur_linux/.venv/bin/python -m doctest src/plur_linux/recipes/pxe/pxe.py
```
**結果**: すべて成功（Exit Code 0）

