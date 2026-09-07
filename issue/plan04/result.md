Ran command: `python3 --version; uv --version`
Ran command: `uv python list`
Viewed pyproject.toml:1-31
Edited pyproject.toml
Ran command: `uv add passlib`
Ran command: `uv python pin 3.13`
Ran command: `uv add passlib`
Ran command: `/home/worker/Documents/antigravity/plur_linux/.venv/bin/python -c "from passlib.hash import sha512_crypt; print(sha512_crypt.hash('p@ssw0rd!'))"`
Ran command: `/home/worker/Documents/antigravity/plur_linux/.venv/bin/python -m unittest discover tests`
Viewed kickstart.py:50-163
Edited kickstart.py
Viewed pxe.py:180-284
Edited pxe.py
Viewed test_kickstart.py:1-77
Edited test_kickstart.py
Ran command: `/home/worker/Documents/antigravity/plur_linux/.venv/bin/python -m unittest tests/test_kickstart.py`

I have executed the unit tests in `tests/test_kickstart.py` and will process the results once the test execution finishes.

Used tool: manage_task
Ran command: `/home/worker/Documents/antigravity/plur_linux/.venv/bin/python -m unittest discover tests`
Ran command: `/home/worker/Documents/antigravity/plur_linux/.venv/bin/python -m doctest src/plur_linux/recipes/pxe/dhcpd.py && /home/worker/Documents/antigravity/plur_linux/.venv/bin/python -m doctest src/plur_linux/recipes/pxe/pxe.py`
Ran command: `git status`
Viewed TODO.md:1-5
Edited TODO.md
Viewed TODO.md:1-5
Edited TODO.md
Viewed walkthrough.md:80-106
Viewed walkthrough.md:107-144
Edited walkthrough.md
Viewed walkthrough.md:1-15
Edited walkthrough.md
Ran command: `git status`

`plur_linux/issue/plan04/TODO.md` の要件、およびいただいたフィードバック（Python >=3.13 への引き上げ、`passlib` の標準使用、`sudoers` のみへの対応）に基づく実装・検証がすべて完了しました。

### 主な実装・修正内容

1. **Python バージョンおよび依存関係の更新**:
   - [`pyproject.toml`](file:///home/worker/Documents/antigravity/plur_linux/pyproject.toml): `requires-python = ">=3.13"` に更新し、`dependencies` に `passlib>=1.7.4` を追加。
   - `.python-version`: `3.13` に固定。
   - `uv` により Python 3.13.14 の仮想環境を再構築し、`passlib` を含む依存パッケージを配備。

2. **パスワード暗号化 (`iscrypted`) の実装 ([`kickstart.py`](file:///home/worker/Documents/antigravity/plur_linux/src/plur_linux/recipes/pxe/kickstart.py))**:
   - `encrypt_password(password: str, rounds: int = None) -> str`:
     - `passlib.hash.sha512_crypt` を標準で使用し、Kickstart 準拠の SHA-512 crypt（`$6$...`）ハッシュを生成。
     - すでに `$` で始まる暗号化済み文字列が渡された場合は二重暗号化を防止しそのまま返却。

3. **ユーザーおよび root パスワードの動的設定 ([`kickstart.py`](file:///home/worker/Documents/antigravity/plur_linux/src/plur_linux/recipes/pxe/kickstart.py))**:
   - `create_account_str(account_set=None) -> str`:
     - `account_set` が指定されていない場合は `env_ops.EnvAccountSet` の現在選択中アカウント（またはデフォルト）を取得。
     - `rootpw --iscrypted <hashed_root_password>` を生成。
     - 一般ユーザー（`username` が指定され、かつ `root` 以外）が存在する場合:
       - `user --name=<username> --password=<hashed_user_password> --iscrypted` を生成。
       - `sudoers=True` の場合に `--groups=wheel` を付加し、sudo 実行権限を付与。
   - `create_ks_str` / `prepare_ks`: 引数 `account_set=None` を追加し、テンプレート内のハードコードされていた固定パスワードを動的な `create_account_str` の出力に置換。

4. **PXE レシピ連携 ([`pxe.py`](file:///home/worker/Documents/antigravity/plur_linux/src/plur_linux/recipes/pxe/pxe.py))**:
   - `setup_a8_pxe_uefi`, `setup_a8_pxe`, `setup_a9_pxe_uefi`, `setup_a9_pxe`, `setup_a10_pxe_uefi`, `setup_a10_pxe` にオプション引数 `account_set=None` を追加し、`kickstart.prepare_ks` へ伝播。

5. **テスト作成と検証 ([`tests/test_kickstart.py`](file:///home/worker/Documents/antigravity/plur_linux/tests/test_kickstart.py))**:
   - 平文パスワードの SHA-512 ハッシュ生成・検証、既暗号化文字列の保持、デフォルトユーザーの wheel グループ付与、`sudoers=False` 時の wheel 付与抑止、`root` 単独時の user 行スキップ、カスタムアカウントセット反映などを含む単体テストを追加。
   - Python 3.13 環境下で全 32 件の単体テストおよび全 doctest が成功することを確認。

詳細な変更内容とテスト実行結果は [walkthrough.md](file:///home/worker/.gemini/antigravity/brain/66f3c248-e369-4159-a457-fce703af6b38/walkthrough.md) に記録しています。
