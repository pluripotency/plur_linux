# plur_linux DHCPDセグメント自動連動およびDHCPレンジ計算 実装計画

## 概要

`plur_linux/issue/plan03/TODO.md` の要求に基づき、PXEサーバー用DHCP設定生成（`src/plur_linux/recipes/pxe/dhcpd.py`）およびPXEセットアップ基本処理（`src/plur_linux/recipes/pxe/pxe.py`）を改修します。

### 目的
1. **`env_ops` セグメント設定との自動連動**:
   - PXEセットアップ対象VMのIPアドレス（`pxe_ip`）が属するセグメントを `env_ops.EnvSegments` から自動検出し、そのセグメント情報（ネットワークアドレス、ネットマスク、ゲートウェイ、DNS、ドメイン名）をもとに `dhcpd.conf` を生成します。
   - セットアップ呼び出し時に特定のセグメントが明示指定された場合は、指定されたセグメントを優先して設定を生成します。
2. **仕様通りのDHCP Range自動算出**:
   - セグメント全体の後半1/4（4thクォーター）をDHCPレンジの開始位置とします。
   - 最後の4つのホストIP（およびブロードキャストアドレス）は使用せず、除外します。
   - 例: `192.168.0.0/24` では、開始 `192.168.0.192`、終了 `192.168.0.250` とし、`251, 252, 253, 254`（およびブロードキャスト `255`）は割り当て対象外とします。
3. **`pxe.py` のハードコーディング解消**:
   - `setup_pxe_base` 内にハードコーディングされていた `192.168.0.` / `192.168.10.` の条件分岐を廃止し、`dhcpd` 経由で動的に `subnet_params` および `httpd` 用の `allowed_net` を取得できるようにします。

---

## 現状の課題分析

### 課題1: `pxe.py` におけるネットワーク情報のハードコーディング
現在、`src/plur_linux/recipes/pxe/pxe.py` の `setup_pxe_base` では、以下のように固定IPプレフィックスで分岐しています：
```python
if re.search(r'^192\.168\.0\.', pxe_ip):
    subnet_params = {
        'subnet': '192.168.0.0',
        'netmask': '255.255.255.0',
        'gateway': '192.168.0.1',
        'nameservers': '8.8.8.8',
        'dh_range': '192.168.0.200 192.168.0.250',
        'broadcast': '192.168.0.255',
    }
    allowed_net = '192.168.0.0/24'
else:
    subnet_params = {
        'subnet': '192.168.10.0',
        ...
```
このため、ユーザーが `env_ops` で設定したセグメント（例: `192.168.122.0/24` や `172.16.0.0/22` など）でPXEサーバーを構築しても認識されず、間違ったDHCP設定が生成されてしまいます。

### 課題2: `dhcpd.py` 単体でセグメントから設定を導出する機能がない
`dhcpd.py` は外部から渡された `subnet_params` 辞書をテンプレートに流し込むだけであり、セグメント定義から動的に `dh_range` や `netmask`、`gateway` を算出する関数が存在しません。

---

## 提案する設計方針

### 1. DHCP Range 計算ロジック (`calc_dhcp_range`)

標準ライブラリ `ipaddress.IPv4Network` を利用し、セグメントのCIDRから厳密に計算します：

1. **セグメント後半1/4の開始オフセット**:
   - アドレス総数: `total = net.num_addresses` (例: `/24` なら 256、`/22` なら 1024)
   - クォーターサイズ: `quarter = total // 4` (例: `/24` なら 64、`/22` なら 256)
   - 開始オフセット: `start_offset = total - quarter`（`total * 3 // 4`）
   - 開始IP: `start_ip = net.network_address + start_offset`
     - `/24` の場合: `0 + 192 = 192.168.0.192`
     - `/22` (`172.16.0.0/22`) の場合: `172.16.0.0 + 768 = 172.16.3.0`
2. **最後の4つのホストIPの除外**:
   - ブロードキャストアドレス: `net.broadcast_address`
   - 除外されるホストIP:
     - `net.broadcast_address - 1` (例: 254)
     - `net.broadcast_address - 2` (例: 253)
     - `net.broadcast_address - 3` (例: 252)
     - `net.broadcast_address - 4` (例: 251)
   - 終了IP: `end_ip = net.broadcast_address - 5`
     - `/24` の場合: `255 - 5 = 192.168.0.250`
     - `/22` の場合: `172.16.3.255 - 5 = 172.16.3.250`
3. **レンジ文字列**:
   - `f"{start_ip} {end_ip}"`

### 2. セグメントの自動判定・パラメータ構築 (`get_subnet_params`)

`dhcpd.py` に以下の関数群を追加します：

```python
def find_segment_for_ip(ip_str, segments=None):
    """env_ops のセグメント一覧から、指定された IP が属するセグメントを探索"""
    ...

def create_subnet_params_from_segment(segment):
    """env_ops のセグメント辞書から subnet_params 辞書を生成"""
    ...

def get_subnet_params(pxe_ip=None, segment=None, segments=None):
    """優先順位に基づいて subnet_params を解決:
    1. segment が明示指定されている場合: そのセグメントを使用
    2. pxe_ip が渡された場合: pxe_ip が属するセグメントを探索
    3. フォールバック: env_ops の最初のセグメント、またはデフォルト定義
    """
    ...
```

#### 生成される `subnet_params` の構造
```python
{
    'subnet': str(net.network_address),          # 例: '192.168.0.0'
    'netmask': str(net.netmask),                 # 例: '255.255.255.0'
    'gateway': gateway_ip,                       # 例: '192.168.0.1' (get_ip_from_segment により解決)
    'nameservers': nameservers_str,              # 例: '192.168.0.1' または '8.8.8.8'
    'dh_range': f"{start_ip} {end_ip}",          # 例: '192.168.0.192 192.168.0.250'
    'broadcast': str(net.broadcast_address),     # 例: '192.168.0.255'
    'allowed_net': f"{net.network_address}/{net.prefixlen}", # 例: '192.168.0.0/24' (httpd用)
    'search': segment.get('search', 'local'),    # ドメイン名
    'segment': segment,                          # 元のセグメント辞書
}
```

### 3. `pxe.py` との統合

`src/plur_linux/recipes/pxe/pxe.py` の `setup_pxe_base` を以下のようにリファクタリングします：
```python
def setup_pxe_base(pxe_ip, dist_dir, www_iso_dir, segment=None):
    subnet_params = dhcpd.get_subnet_params(pxe_ip=pxe_ip, segment=segment)
    allowed_net = subnet_params.get('allowed_net', f"{subnet_params['subnet']}/24")
    
    http_params = {
        'file_name': 'pxeboot.conf',
        'alias': f'/{dist_dir}',
        'dir_path': www_iso_dir,
        'allowed_net': allowed_net
    }
    ...
```
また、上位関数 `setup_a8_pxe`, `setup_a9_pxe`, `setup_a10_pxe` 等にオプション引数 `segment=None` を追加し、呼び出し側から明示的にセグメントを指定することも可能とします。

---

## User Review Required

> [!IMPORTANT]
> **ドメイン名 (`option domain-name`) および DNS (`option domain-name-servers`) のグローバル設定**
> 現在の `create_pre_str()` は固定値 (`domain_name = 'local'`, `domain_name_servers = 'a8pxe.local'`) を出力しています。
> 本計画では、セグメントに `search` や `nameservers` が設定されている場合、それらの値を `create_pre_str` や `create_pxe_dhcp_conf_str` に反映できるようにオプション引数を追加・拡張します。
> （引数が渡されない場合は既存のデフォルト値を維持し、既存動作を壊しません）

> [!NOTE]
> **非常に小さいサブネット (/29 以下) での扱い**
> `/24` や `/22`、`/16` などの一般的なサブネットでは後半1/4の範囲から末尾4ホスト除外で問題なく十分なIP数が確保できますが、`/29`（利用可能ホスト6個）のような極端に小さいサブネットでは `start_ip > end_ip` となる場合があります。
> このような境界値では、利用可能なホスト範囲（`network + 1` 〜 `broadcast - 1`）に自動フォールバックする安全ガードを設けます。

---

## Open Questions

1. **`dhcpd.setup()` の呼び出し後方互換性**:
   `dhcpd.setup(subnet_params=None, set_fw=True, pxe_ip=False, segment=None)` のように、`subnet_params` を明示指定された場合はそれをそのまま使い、`None` の場合に `get_subnet_params` で自動解決する方針として問題ないでしょうか？
   （推奨：100% の後方互換性を維持できます）

---

## Proposed Changes

### PXE / DHCP レシピ層

#### [MODIFY] [dhcpd.py](file:///home/worker/Documents/antigravity/plur_linux/src/plur_linux/recipes/pxe/dhcpd.py)
- `calc_dhcp_range(net)`: セグメント後半1/4、末尾4ホスト除外の計算関数を追加
- `find_segment_for_ip(ip_str, segments=None)`: `pxe_ip` からセグメントを探索する関数を追加
- `create_subnet_params_from_segment(segment)`: セグメントから `subnet_params` を構築する関数を追加
- `get_subnet_params(pxe_ip=None, segment=None, segments=None)`: 統一的なパラメータ解決関数を追加
- `create_pre_str` / `create_pxe_pre_str`: `domain_name` / `domain_name_servers` のカスタマイズ引数をサポート
- `create_pxe_dhcp_conf_str` / `setup`: 自動解決に対応
- 既存 doctest の構文エラー修正

#### [MODIFY] [pxe.py](file:///home/worker/Documents/antigravity/plur_linux/src/plur_linux/recipes/pxe/pxe.py)
- `setup_pxe_base`: 固定の `192.168.0.` / `192.168.10.` 分岐を削除し、`dhcpd.get_subnet_params` による自動導出に置き換え
- `setup_a8_pxe`, `setup_a9_pxe`, `setup_a10_pxe` 等に `segment=None` 引数を追加

---

### テストコード

#### [NEW] [test_dhcpd.py](file:///home/worker/Documents/antigravity/plur_linux/tests/test_dhcpd.py)
- `calc_dhcp_range`:
  - `192.168.0.0/24` -> `192.168.0.192 192.168.0.250` (末尾 251, 252, 253, 254 除外) の検証
  - `172.16.0.0/22` -> `172.16.3.0 172.16.3.250` の検証
- `find_segment_for_ip`:
  - 対象IPから該当セグメントを正しく見つけられるか検証
- `get_subnet_params`:
  - 明示指定セグメント、IP自動判定、フォールバックの各動作検証
- `create_pxe_dhcp_conf_str`:
  - 生成された設定ファイル内容の妥当性検証

---

### ドキュメント

#### [MODIFY] [TODO.md](file:///home/worker/Documents/antigravity/plur_linux/issue/plan03/TODO.md)
- 実装完了状態および決定仕様の更新

---

## Verification Plan

### Automated Tests
1. **単体テストの実行**:
   ```bash
   /home/worker/Documents/antigravity/plur_linux/.venv/bin/python -m unittest tests/test_dhcpd.py
   ```
2. **全テストスイートの実行**:
   ```bash
   /home/worker/Documents/antigravity/plur_linux/.venv/bin/python -m unittest discover tests
   ```
3. **doctestの実行**:
   ```bash
   /home/worker/Documents/antigravity/plur_linux/.venv/bin/python -m doctest src/plur_linux/recipes/pxe/dhcpd.py
   /home/worker/Documents/antigravity/plur_linux/.venv/bin/python -m doctest src/plur_linux/recipes/pxe/pxe.py
   ```

### Manual Verification
1. **設定文字列の出力確認**:
   テストスクリプト上で `pxe_ip = '192.168.0.10'` を与えて `get_subnet_params` -> `create_pxe_dhcp_conf_str` を呼び出し、`range dynamic-bootp 192.168.0.192 192.168.0.250;` が出力されることを目視確認。
2. **異なるセグメント (`172.16.0.0/22`) での出力確認**:
   `172.16.0.0/22` のセグメントを指定した場合に、対応するネットマスク `255.255.252.0` と適切なレンジが出力されることを確認。
