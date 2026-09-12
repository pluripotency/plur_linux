# 実装計画: Docker Compose による PXE ベースサービス (Nginx, Kea DHCP, TFTP) 構築

## 概要
`plur_linux/issue/plan05/TODO.md` の要求に基づき、従来のホスト常駐型サービス（Apache httpd、ISC dhcpd、tftp-server）による `setup_pxe_base` の構成を、Docker Compose 上のコンテナ（Nginx, ISC Kea DHCP, TFTP）として一括デプロイ・管理可能にする `src/plur_linux/recipes/pxe/compose.py` を実装します。
また、`src/plur_linux/recipes/pxe/pxe.py` に `setup_pxe_base_by_docker` を追加し、Docker Compose ベースのセットアップを選択できるようにします。（Docker Engine 自体のセットアップはユーザー側で行われます）。

### 主な要件
1. **HTTP サーバーのコンテナ化 (Nginx)**:
   - Apache httpd の代わりに Nginx (`nginx:alpine`) を使用。
   - `/var/www/html`（Kickstart ファイル `/ks` を含む）および `/var/pxe/{dist_dir}`（ISO マウント先）をボリュームマウントし、ディレクトリインデックス（`autoindex on`）および `allowed_net` によるアクセス制御を設定。
2. **DHCP サーバーのコンテナ化 (ISC Kea)**:
   - 旧 ISC dhcpd の代わりに ISC Kea DHCPv4 (`isc/kea-dhcp4:latest`) を使用。
   - `env_ops` セグメントまたは `pxe_ip` から計算された DHCP レンジ、サブネット、ゲートウェイ、DNS、`next-server` を設定。
   - クライアントアーキテクチャ（Option 93: UEFI 0x0007/0x0009 は `BOOTX64.EFI`、BIOS は `pxelinux.0`）による起動ファイル自動切替を設定。
3. **TFTP サーバーのコンテナ化 (TFTP-HPA)**:
   - ホスト側の `/var/lib/tftpboot`（`pxelinux.0`, `BOOTX64.EFI`, カーネル/initrd, GRUB 設定）をマウントしてブートローダーを配信。
4. **ネットワークモード (`network_mode: host`)**:
   - ブロードキャスト UDP（DHCP ポート 67、TFTP ポート 69）および HTTP ポート 80 を直接受信・処理するため、全サービスに `network_mode: host` を適用。
5. **`pxe.py` 連携 (`setup_pxe_base_by_docker`)**:
   - `pxe.py` に `setup_pxe_base_by_docker` を新設し、各ディストリビューション設定関数（`setup_a8_pxe_uefi` 等）から `use_docker=True` で呼び出し可能にする。

---

## ユーザー確認事項 (User Review Required)

> [!NOTE]
> **コンテナイメージの選定**
> - Nginx: `nginx:alpine`
> - Kea DHCP: `isc/kea-dhcp4:latest` (ISC 公式イメージ)
> - TFTP: `ghcr.io/linuxserver/tftp-hpa:latest` (LinuxServer.io 公式、Linux 標準 tftp-hpa)
> 各イメージ名は `compose.py` の引数・定数としてカスタマイズ可能にします。

> [!NOTE]
> **ポート競合防止**
> ホスト側で `httpd`、`dhcpd`、`tftp.socket` が既に常駐起動している場合、ポート 80, 67, 69 で競合するため、`setup_pxe_compose` 実行時にこれらホストサービスを自動的に停止・無効化（`systemctl stop ...`）します。

---

## 変更予定ファイル一覧

### 1. 新規モジュール: PXE Docker Compose
#### [NEW] [`src/plur_linux/recipes/pxe/compose.py`](file:///home/worker/Documents/antigravity/plur_linux/src/plur_linux/recipes/pxe/compose.py)
- **`create_nginx_conf_str(alias, dir_path, allowed_net=None) -> str`**:
  - Nginx 用設定ファイル（`default.conf`）文字列を生成。
  - ルート `/var/www/html`、`/ks` エイリアス、`/{dist_dir}` エイリアス、`autoindex on`、アクセス許可（`allow {allowed_net}; deny all;`）を設定。
- **`create_kea_conf_str(pxe_ip, subnet_params) -> str`**:
  - ISC Kea DHCP4 用設定ファイル（JSON）文字列を生成。
  - `interfaces: ["*"]`、`memfile` リースDB、サブネット・プール（`start - end`）、ゲートウェイ、DNS、`next-server` を設定。
  - `client-classes`（Option 93 による UEFI / BIOS 判定と `boot-file-name` 切替）を定義。
- **`create_docker_compose_str(...) -> str`**:
  - `nginx`, `kea`, `tftpd` の 3 サービスを含む `docker-compose.yml` 文字列を生成。
  - 全サービス `network_mode: host`、`restart: unless-stopped`、必要なホストディレクトリ（`/var/www/html`, `/var/lib/tftpboot`, `www_iso_dir`, 設定ファイル）のマウントを指定。
- **`prepare_compose_files(...)`**:
  - 指定ディレクトリ（デフォルト `/etc/pxe-docker`）に `nginx.conf`, `kea-dhcp4.conf`, `docker-compose.yml` を配置。
- **`start_containers(...)` / `stop_containers(...)` / `status_containers(...)`**:
  - `docker compose up -d`, `down`, `ps` 実行用ラッパー関数。
- **`setup_pxe_compose(...)`**:
  - firewalld 設定、ホストディレクトリ作成、ホスト常駐サービス停止、設定ファイル配置、コンテナ起動を実行するセッション用関数を返却。

---

### 2. PXE オーケストレーション連携
#### [MODIFY] [`src/plur_linux/recipes/pxe/pxe.py`](file:///home/worker/Documents/antigravity/plur_linux/src/plur_linux/recipes/pxe/pxe.py)
- **`setup_pxe_base_by_docker(pxe_ip, dist_dir, www_iso_dir, segment=None, compose_dir='/etc/pxe-docker')`**:
  - `compose.setup_pxe_compose` をラップし、`setup_pxe_base` と同一シグネチャ・互換インターフェースを提供。
- **`setup_a8_pxe_uefi`, `setup_a8_pxe`, `setup_a9_pxe_uefi`, `setup_a9_pxe`, `setup_a10_pxe_uefi`, `setup_a10_pxe`**:
  - 引数 `use_docker=False`, `compose_dir='/etc/pxe-docker'` を追加し、`use_docker=True` 指定時に `setup_pxe_base_by_docker` を実行。

---

### 3. テストコード
#### [NEW] [`tests/test_compose.py`](file:///home/worker/Documents/antigravity/plur_linux/tests/test_compose.py)
- `test_create_nginx_conf_str`: Nginx 構文、エイリアス、`autoindex`、アクセス許可ルールの検証。
- `test_create_kea_conf_str`: 生成された Kea JSON の構文解析、サブネット・プール、next-server、UEFI/BIOS クライアントクラスの検証。
- `test_create_docker_compose_str`: docker-compose YAML の構文解析、全サービス定義、`network_mode: host`、ボリュームマウントの検証。
- `test_setup_pxe_compose_mocked`: `base_shell` モックによるファイル生成と `docker compose up -d` 実行フローの検証。
- `test_setup_pxe_base_by_docker_in_pxe`: `pxe.py` の `setup_pxe_base_by_docker` 委譲の検証。

---

## 検証手順 (Verification Plan)

### 自動テスト
1. **新規単体テスト実行**:
   ```bash
   /home/worker/Documents/antigravity/plur_linux/.venv/bin/python -m unittest tests/test_compose.py
   ```
2. **全単体テストスイート実行**:
   ```bash
   /home/worker/Documents/antigravity/plur_linux/.venv/bin/python -m unittest discover tests
   ```
3. **Doctest 実行**:
   ```bash
   /home/worker/Documents/antigravity/plur_linux/.venv/bin/python -m doctest src/plur_linux/recipes/pxe/compose.py
   /home/worker/Documents/antigravity/plur_linux/.venv/bin/python -m doctest src/plur_linux/recipes/pxe/pxe.py
   ```
