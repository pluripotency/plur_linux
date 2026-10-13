# 実装計画: Kickstartにおけるenv_opsユーザー設定・iscryptedパスワード・sudo連携

## 概要
`plur_linux/issue/plan04/TODO.md` の要求に基づき、`src/plur_linux/recipes/pxe/kickstart.py` で生成する Kickstart 設定において、`env_ops` に定義されたユーザー情報（`root` / 一般ユーザー、パスワード、sudo権限）を動的に参照・反映できるように改修します。

### 主な要件
1. **ユーザー情報の参照**: `env_ops` の `EnvAccountSet`（現在選択されている `account_set`）または引数で渡された `account_set` から `root_password`, `username`, `password`, `sudoers`（または `sudo`）を取得する。
2. **パスワード暗号化 (`iscrypted`)**: パスワードを SHA-512 crypt（`$6$...`）形式でハッシュ化し、`rootpw --iscrypted <hash>` および `user --password=<hash> --iscrypted` に指定する。平文が渡された場合は自動的にハッシュ化し、既にハッシュ化されている文字列（`$` で始まる値）は二重ハッシュ化を防止する。
3. **sudo権限の付与**: `sudo=True`（または `sudoers=True`）の場合、`user` コマンドに `--groups=wheel` を付加し、管理権限（sudo）を付与する。
4. **依存関係管理**: パスワードハッシュ生成ライブラリ（`passlib`）を `uv add` により導入し、`pyproject.toml` の `dependencies` を更新する。標準 `crypt` モジュールへの安全なフォールバックも備える。

---

## ユーザー確認事項 (User Review Required)

> [!NOTE]
> **依存ライブラリ (`passlib`) の追加**
> Python 3.11 の標準 `crypt` モジュールは非推奨（3.13 で削除予定）のため、Kickstart 用の SHA-512 crypt パスワード生成用として `passlib` を `uv add passlib` により追加します。また、環境依存を避けるため、万一 `passlib` 未導入環境でも標準 `crypt` にフォールバックする二重構造とします。

> [!NOTE]
> **sudo権限の判定キー**
> `env_ops` の既存定義ではキー名が `sudoers`（bool）となっていますが、TODOの記述にある `sudo=True` にも柔軟に対応できるよう、`account_set.get('sudoers', account_set.get('sudo', True))` で両方のキーを参照可能にします。

---

## 変更予定ファイル一覧

### 1. 依存関係管理
#### [MODIFY] [`pyproject.toml`](file:///home/worker/Documents/antigravity/plur_linux/pyproject.toml)
- `uv add passlib` を実行し、`dependencies` に `passlib>=1.7.4` を追加。

---

### 2. Kickstart 生成層
#### [MODIFY] [`src/plur_linux/recipes/pxe/kickstart.py`](file:///home/worker/Documents/antigravity/plur_linux/src/plur_linux/recipes/pxe/kickstart.py)
- **`encrypt_password(password: str, salt: str = None) -> str`**:
  - パスワードを Kickstart 用 SHA-512 crypt 形式（`$6$...`）にハッシュ化。
  - すでに `$` から始まるハッシュ値の場合はそのまま返却（二重暗号化防止）。
  - `passlib.hash.sha512_crypt` を優先使用し、未インストール時は `crypt.crypt` にフォールバック。
- **`create_account_str(account_set=None) -> str`**:
  - `account_set` が `None` の場合、`EnvAccountSet().get_current_index_account_set()` から動的取得（取得不可時は `default_account_set` を使用）。
  - `rootpw --iscrypted <crypted_root_password>` を生成。
  - 一般ユーザー（`username` が指定され、かつ `root` 以外の場合）に対して:
    `user --name=<username> --password=<crypted_user_password> --iscrypted` を生成。
    `sudoers` または `sudo` が `True` の場合、`--groups=wheel` を付与。
- **`create_ks_str(...)`**:
  - ハードコードされていた `rootpw = 'rootpw  --iscrypted $1$v4y/Tz8G$mq2hT5nsuafCpIB7KlQTQ/'` を `create_account_str(account_set=account_set)` の出力に置換。
  - 引数に `account_set=None` を追加。
- **`prepare_ks(...)`**:
  - 引数に `account_set=None` を追加し、各 Kickstart 生成呼び出しに伝播。

---

### 3. PXE レシピ連携
#### [MODIFY] [`src/plur_linux/recipes/pxe/pxe.py`](file:///home/worker/Documents/antigravity/plur_linux/src/plur_linux/recipes/pxe/pxe.py)
- `setup_a8_pxe_uefi`, `setup_a8_pxe`, `setup_a9_pxe_uefi`, `setup_a9_pxe`, `setup_a10_pxe_uefi`, `setup_a10_pxe` にオプション引数 `account_set=None` を追加し、`kickstart.prepare_ks` に渡す。

---

### 4. テストコード
#### [MODIFY] [`tests/test_kickstart.py`](file:///home/worker/Documents/antigravity/plur_linux/tests/test_kickstart.py)
- `test_encrypt_password`: 平文からの SHA-512 ハッシュ生成、既暗号化文字列の保持。
- `test_create_account_str_default`: デフォルトアカウント設定（worker, wheel付き, rootpw）の生成検証。
- `test_create_account_str_no_sudo`: `sudoers=False` 時に `--groups=wheel` が付加されないことの検証。
- `test_create_account_str_root_only`: 一般ユーザーが指定されていない場合の検証。
- `test_create_ks_str_with_custom_account`: `create_ks_str` にカスタム `account_set` を渡した際の完全な Kickstart 出力検証。

---

## 検証手順 (Verification Plan)

### 自動テスト
1. **ライブラリ追加と依存関係確認**:
   ```bash
   uv add passlib
   git diff pyproject.toml
   ```
2. **Kickstart 単体テスト**:
   ```bash
   /home/worker/Documents/antigravity/plur_linux/.venv/bin/python -m unittest tests/test_kickstart.py
   ```
3. **全単体テストスイート実行**:
   ```bash
   /home/worker/Documents/antigravity/plur_linux/.venv/bin/python -m unittest discover tests
   ```
4. **Doctest 実行**:
   ```bash
   /home/worker/Documents/antigravity/plur_linux/.venv/bin/python -m doctest src/plur_linux/recipes/pxe/dhcpd.py
   /home/worker/Documents/antigravity/plur_linux/.venv/bin/python -m doctest src/plur_linux/recipes/pxe/pxe.py
   ```
