# plur_linux セグメント仕様変更およびIP計算ロジック集約 実装計画

## 概要

`plur_linux` ではこれまで、KVM仮想マシンのネットワークセグメントを `ip_base_prefix` (例: `192.168.122`) と `prefix` (例: `24`) で保持し、仮想マシンのIPを `ip_base_prefix + f".{ip_seed}/{prefix}"` という文字列結合で決定していました。
しかしこの方式では、`/24` より大きいサブネット（`/22` や `/16` など、プレフィックス長が小さいネットワーク）において第3オクテットに跨るIPアドレスの割り当てができません。

本計画では、以下の要件を満たす設計・移行方針を提案・定義します：
1. `ip_base_prefix` + `prefix` 方式を廃止し、`network_with_prefix` (例: `172.16.0.0/22`) によるCIDR表現へ移行する。
2. `seed` として `int` の `1` を指定すると `172.16.0.1`、`str` の `'1.5'` を指定すると `172.16.1.5` を取得でき、範囲外の `'4.1'` を指定した場合は `'IP Range Error'` を返す堅牢な計算ロジックを実装する。
3. レシピやノード構築コードなど複数箇所に散らばっている `ip_seed` / `ip_base_prefix` の直接参照・直接結合を解消し、統一されたヘルパーインターフェースへ集約する。
4. 既存の `~/.plur/env.toml` との後方互換性を保ち、移行による既存環境の破損を防止する。

---

## 現状の課題分析

### 課題1: 文字列結合による /24 固定前提のIP生成
`src/plur_linux/lib/env_ops.py` や各種レシピで、IPアドレスの導出が以下のようにハードコーディングされています：
```python
# env_ops.py
iface['ip'] = segment['ip_base_prefix'] + f".{iface['ip_seed']}/{segment['prefix']}"
iface['gateway'] = segment['ip_base_prefix'] + '.' + segment['gateway_seed']

# gluster.py
hosts = [[segment['ip_base_prefix'] + f'.{host[1]}', host[0]] for host in host_list]

# kubeadm_a9.py
host_lines = [f'{segment["ip_base_prefix"]}.{host[1]} {host[0]}' for host in host_list]
mgr_ip = f'{segment["ip_base_prefix"]}.{host_list[0][1]}'
ctl_ip = f'{segment["ip_base_prefix"]}.{host_list[1][1]}'
```
このため、第4オクテットしか可変にできず、`/22` や `/16` で複数のオクテットに跨るアドレス表現が不可能です。

### 課題2: 入力バリデーションの制限
`src/plur_linux/nodes/new_node.py` の `create_single_iface_node_dict` では、入力正規表現が以下のように指定されています：
```python
ip_seed = menu.get_input(r'(dhcp|\d+)', 'IP seed(Default: dhcp): ', 'invalid format', 'dhcp')
```
正規表現が `(dhcp|\d+)` に限定されているため、ユーザーが `'1.5'` などのドット付きオフセットを入力することができません。

### 課題3: 責務の漏れ出し（カプセル化の欠如）
各レシピ（`gluster.py`, `kubeadm_a9.py` など）が `segment` 辞書の内部構造（`ip_base_prefix` というキーの存在と意味）を直接知る必要があり、「セグメント情報からIPを導出する」という責務がコード全体に散散しています。

---

## 提案する解決アプローチ

### アーキテクチャ構成

保守性・テスタビリティ・移行の容易さを最大化するため、以下の3層構造を提案します。

```
+-------------------------------------------------------------+
| レシピ層 (gluster.py, kubeadm_a9.py, dock.py など)          |
|  - get_ip_from_segment(segment, host[1]) を呼び出すのみ     |
+-------------------------------------------------------------+
                              |
                              v
+-------------------------------------------------------------+
| セグメント管理層 (env_ops.py)                               |
|  - network_with_prefix の保持・TOML定義                     |
|  - bind_env() での iface['ip'], iface['gateway'] の導出   |
|  - 既存 ip_base_prefix からの後方互換変換                   |
+-------------------------------------------------------------+
                              |
                              v
+-------------------------------------------------------------+
| コアIP計算モジュール (lib/ip_calc.py)                       |
|  - calc_ip(network_with_prefix, seed)                       |
|  - 標準ライブラリ ipaddress による厳密なネットワーク計算   |
|  - int / str (ドット記法) / 完全IP / dhcp のパース・検証   |
+-------------------------------------------------------------+
```

### IP導出ロジックの仕様 (`calc_ip`)

標準ライブラリ `ipaddress` を活用し、以下のルールに従って計算します：

1. **入力 `seed` の種別に応じたオフセット計算**:
   - `int` (例: `1`):
     ネットワークアドレスの整数値にそのまま加算。
     例: `172.16.0.0/22` + `1` = `172.16.0.1`
     例: `172.16.0.0/22` + `261` = `172.16.1.5`
   - `str` (数字のみ, 例: `'1'`):
     整数に変換して `int` と同様に計算。
   - `str` (ドット区切り2要素, 例: `'1.5'`):
     `上位オクテット * 256 + 下位オクテット` をオフセットとして計算。
     `1 * 256 + 5 = 261`。
     例: `172.16.0.0/22` + `261` = `172.16.1.5`
   - `str` (ドット区切り4要素, 例: `'172.16.1.5'`):
     完全なIPv4アドレスが直接指定されたとみなし、対象ネットワークに含まれるか判定。
   - `str` (`'dhcp'`):
     そのまま `'dhcp'` を返却。

2. **範囲チェックとエラー返却**:
   - 計算されたIPアドレスが `ipaddress.IPv4Network(network_with_prefix)` の範囲外になる場合、`'IP Range Error'` を返却します。
     例: `'4.1'` の場合、`4 * 256 + 1 = 1025` 加算となり、`172.16.4.1` が算出されますが、これは `172.16.0.0/22`（最大 `172.16.3.255`）の範囲外となるため `'IP Range Error'` を返却。
     例: `/24` ネットワークに対して `'1.5'` を指定した場合も、`/24` の範囲を超えるため `'IP Range Error'` を返却。
   - Python例外として扱いたい呼び出し元のために、`raise_on_error=True` オプション（例外 `IPRangeError` を送出）もサポートします。

3. **プレフィックス付加オプション (`with_prefix`)**:
   - `with_prefix=False`（デフォルト）: `172.16.1.5`（`/etc/hosts` やゲートウェイ用）
   - `with_prefix=True`: `172.16.1.5/22`（インターフェースIP設定 `iface['ip']` 用）

---

## コード散在箇所の集約・移行計画

### 1. `src/plur_linux/lib/ip_calc.py` の新設
純粋関数群として切り出すことで、単体テストを容易にします。
- `class IPRangeError(ValueError)`: 範囲外例外
- `calc_ip(network_with_prefix, seed, with_prefix=False, raise_on_error=False)`
- `get_segment_network(segment)`: 辞書から `network_with_prefix` を安全に取得（旧キー互換対応）
- `get_ip_from_segment(segment, seed, with_prefix=False, raise_on_error=False)`

### 2. `src/plur_linux/lib/env_ops.py` の修正
- **TOML定義の更新**:
  `ip_base_prefix`, `prefix` を削除し、`network_with_prefix` を追加。
  `gateway_seed` の正規表現を拡張（`\d+(\.\d+)*`）。
- **デフォルト値の更新**:
  `'network_with_prefix': '192.168.122.0/24'`
- **`format_segment_list`**:
  `f"{get_segment_network(s)} {s['net_source']}(type: {s['type']})"` を表示。
- **`bind_env`**:
  ```python
  if iface['ip_seed'] == 'dhcp':
      iface['ip'] = 'dhcp'
  else:
      res_ip = get_ip_from_segment(segment, iface['ip_seed'], with_prefix=True)
      if res_ip == 'IP Range Error':
          raise IPRangeError(f"IP Seed {iface['ip_seed']} is out of range for {get_segment_network(segment)}")
      iface['ip'] = res_ip
      iface['gateway'] = get_ip_from_segment(segment, segment['gateway_seed'])
      iface['search'] = segment['search']
      iface['nameservers'] = segment['nameservers'].split(',')
      iface['segment'] = segment
  ```
- **後方互換性 (Backward Compatibility)**:
  ユーザーの `~/.plur/env.toml` に `ip_base_prefix` と `prefix` が残っている場合でも、`get_segment_network` により自動で `f"{ip_base_prefix}.0/{prefix}"` と解釈して無停止で動作を継続できるようにします。

### 3. `src/plur_linux/nodes/new_node.py` の修正
- `create_single_iface_node_dict` の対話型入力正規表現を更新：
  `r'^(dhcp|\d+(\.\d+)*)$'` により、`'1.5'` や `'100'`、`'dhcp'` を受け付けられるようにします。

### 4. レシピコードの改修
- **`src/plur_linux/nodes/guests/kubeadm_a9.py`**:
  `segment["ip_base_prefix"] + ...` の直接結合を `get_ip_from_segment(segment, host[1])` に置換。
- **`src/plur_linux/nodes/guests/gluster.py`**:
  `segment['ip_base_prefix'] + f'.{host[1]}'` を `get_ip_from_segment(segment, host[1])` に置換。

---

## User Review Decisions

- **エラー時の返却形式**: 
  - `calc_ip(..., raise_on_error=False)`: 文字列 `'IP Range Error'` を返す（TODOの文面通りの動作）
  - `calc_ip(..., raise_on_error=True)`: `IPRangeError` 例外をスローする（バッチ処理やbind_env時の不正IP検知向け）
- **ネットワークアドレスおよびブロードキャストアドレスの扱い**:
  - **オプションBを採用**: 有効ホスト範囲（Network Address < IP < Broadcast Address）のみを正常とし、両端（ネットワークアドレスおよびブロードキャストアドレス）も `'IP Range Error'` を返却する。
    - 例: `172.16.0.0/22` の場合、`172.16.0.0` (offset 0) および `172.16.3.255` (offset 1023 / '3.255') は `'IP Range Error'`。
    - 有効範囲は `172.16.0.1` 〜 `172.16.3.254`。
- **`gateway_seed` の指定方法**:
  - `calc_ip` と同一ロジックを使用し、シード値（例: `'1'`, `'0.1'`, `'3.254'`）および完全なIPアドレス（例: `'172.16.0.1'`）の両方を受け付け可能とする。

---

## Proposed Changes

### 共通ネットワーク計算モジュール

#### [NEW] [ip_calc.py](file:///home/worker/Documents/antigravity/plur_linux/src/plur_linux/lib/ip_calc.py)
- `IPRangeError` 例外クラスの定義
- `calc_ip(network_with_prefix, seed, with_prefix=False, raise_on_error=False)` 関数の実装
- `get_segment_network(segment)` 関数の実装（後方互換ハンドリング含む）
- `get_ip_from_segment(segment, seed, with_prefix=False, raise_on_error=False)` 関数の実装

---

### 環境・セグメント定義層

#### [MODIFY] [env_ops.py](file:///home/worker/Documents/antigravity/plur_linux/src/plur_linux/lib/env_ops.py)
- `SEGMENT_DEFINITION_TOML_STR`: `ip_base_prefix` / `prefix` を削除し、`network_with_prefix` を追加
- `default_segment`: `'network_with_prefix': '192.168.122.0/24'` に変更
- `EnvSegments.format_segment_list`: `get_segment_network` を用いた一覧表示に変更
- `EnvSegments.bind_env`: `get_ip_from_segment` を使って `iface['ip']` および `iface['gateway']` を生成
- `get_ip_from_segment` / `calc_ip` をモジュールレベルでもエクスポート

---

### ノード生成・レシピ層

#### [MODIFY] [new_node.py](file:///home/worker/Documents/antigravity/plur_linux/src/plur_linux/nodes/new_node.py)
- `create_single_iface_node_dict`: `ip_seed` の入力バリデーション正規表現を `r'^(dhcp|\d+(\.\d+)*)$'` に更新

#### [MODIFY] [kubeadm_a9.py](file:///home/worker/Documents/antigravity/plur_linux/src/plur_linux/nodes/guests/kubeadm_a9.py)
- `choose_host`:
  - `mgr_ip`, `ctl_ip`, `host_lines` の生成箇所を `env_ops.get_ip_from_segment(segment, ...)` に書き換え

#### [MODIFY] [gluster.py](file:///home/worker/Documents/antigravity/plur_linux/src/plur_linux/nodes/guests/gluster.py)
- `create_gluster_dict`:
  - `hosts` 生成箇所を `env_ops.get_ip_from_segment(segment, host[1])` に書き換え

---

### ドキュメント & テスト

#### [MODIFY] [TODO.md](file:///home/worker/Documents/antigravity/plur_linux/TODO.md)
- 実装完了チェックボックスの更新と、決定した設計仕様の追記

#### [NEW] [test_ip_calc.py](file:///home/worker/Documents/antigravity/plur_linux/tests/test_ip_calc.py)
- `unittest` による単体テストスイートを作成：
  - `172.16.0.0/22` に対して `1` -> `172.16.0.1`
  - `172.16.0.0/22` に対して `'1.5'` -> `172.16.1.5`
  - `172.16.0.0/22` に対して `'4.1'` -> `'IP Range Error'`
  - `192.168.122.0/24` に対して `'1.5'` -> `'IP Range Error'`
  - `with_prefix=True` 時の挙動 (`172.16.1.5/22`)
  - 完全IP指定・dhcp指定の挙動
  - 後方互換辞書のフォールバック挙動

---

## Verification Plan

### Automated Tests
1. **単体テストの実行**:
   ```bash
   /home/worker/Documents/antigravity/plur_linux/.venv/bin/python -m unittest tests/test_ip_calc.py
   ```
   全テストケース（正常系・境界値・異常系・後方互換系）がパスすることを確認。

2. **既存モジュールのインポート検証**:
   ```bash
   /home/worker/Documents/antigravity/plur_linux/.venv/bin/python -c "import plur_linux.lib.env_ops; import plur_linux.nodes.new_node; import plur_linux.nodes.guests.kubeadm_a9; import plur_linux.nodes.guests.gluster; print('All modules imported successfully')"
   ```

### Manual Verification
1. **ダミー環境での `bind_env` 動作確認**:
   テストスクリプト上で `network_with_prefix = '172.16.0.0/22'` を設定したセグメントを作成し、`ip_seed='1.5'` で `bind_env` を呼び出して `iface['ip'] == '172.16.1.5/22'`、`iface['gateway'] == '172.16.0.1'` が正しく設定されることを確認。
2. **旧形式セグメントでの互換性確認**:
   `ip_base_prefix='192.168.122'`, `prefix='24'` の辞書を渡してもエラーにならず透過的に計算されることを確認。
