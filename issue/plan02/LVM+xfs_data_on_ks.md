
### 1. Kickstartの設定例
```
# 1. ディスク初期化設定（既存パーティションを全て消去）
clearpart --all --initlabel

# 2. UEFI ブートおよびシステム用パーティションの作成
# EFIシステムパーティション（UEFI起動用）
part /boot/efi --fstype="efi" --size=600 --ondisk=sda

# /boot パーティション（カーネル・initramfs用）
part /boot --fstype="xfs" --size=1024 --ondisk=sda

# LVM の物理ボリューム（PV）の定義（残りの容量をすべてPV割り当て）
part pv.01 --fstype="lvmpv" --size=1 --grow --ondisk=sda

# 3. ボリュームグループ（VG）の作成
volgroup vg_system pv.01

# 4. 論理ボリューム（LV）の作成
# root (/)：指定サイズ（例: 50GB = 51200MB）で固定
logvol / --fstype="xfs" --size=51200 --name=lv_root --vgname=vg_system

# swap：必要に応じて（例: 8GB）
logvol swap --fstype="swap" --size=8192 --name=lv_swap --vgname=vg_system

# /data：残りのディスク全容量を自動割り当て (--grow)
logvol /data --fstype="xfs" --size=1 --grow --name=lv_data --vgname=vg_system
```

### 2. 設定の重要ポイント

1. **`logvol /data` に `--grow` と `--size=1` を指定**
    
    - `--grow` オプションを付けることで、`root` や `swap` を作成した後に**余ったボリュームグループ（VG）領域を全て `/data` に割り当てる**ことができます。
        
2. **`root`（`/`）は `--grow` を付けず `--size` のみで固定**
    
    - 固定サイズ（MB単位）で数値を明示します（例: `501200` = 50GB）。
        
3. **UEFI 必須パーティションの確保**
    
    - UEFI PXE インストールでは、必ず `/boot/efi`（EFIシステムパーティション / 600MB程度）を確保してください。
        
4. **対象ディスクの指定（`--ondisk=sda` または `ignoredisk`）**
    
    - サーバに複数のストレージが接続されている環境では、対象ディスクを誤らないよう `--ondisk=sda` や `ignoredisk --only-use=sda` などを付与してください。


### 3. 全体
```
# --------------------------------------------------
# システム基本設定
# --------------------------------------------------
# キーボード・言語設定
keyboard --vckeymap=jp --xlayouts='jp'
lang ja_JP.UTF-8

# ネットワーク設定（DHCPの例）
network --bootproto=dhcp --device=link --activate

# NTP (時計・タイムゾーン) 設定
timezone Asia/Tokyo --utc
timesource --ntp-server=ntp.nict.jp

# 認証・ユーザー設定 (※平文パスワードの例)
# ※運用環境に応じて hashed 形式 (openssl passwd -6 で生成) への置き換えを推奨します
rootpw --plaintext "YourRootPassword123"
user --name=appuser --groups=wheel --plaintext --password="YourUserPassword123"

# インストールモード設定（CUI/テキストモード）
text

# --------------------------------------------------
# パッケージ選択 (Minimal Install)
# --------------------------------------------------
%packages
@core
# 不要な標準ドキュメント類を除外して軽量化
-iwl*-firmware
%end

# --------------------------------------------------
# ストレージ・パーティション設定 (UEFI / LVM + XFS)
# --------------------------------------------------
# 既存の全パーティションを削除してディスク初期化
clearpart --all --initlabel

# 1. UEFI ブート用必須パーティション (/boot/efi)
part /boot/efi --fstype="efi" --size=600 --ondisk=sda

# 2. ブートパーティション (/boot)
part /boot --fstype="xfs" --size=1024 --ondisk=sda

# 3. LVM 物理ボリューム (PV) の作成 (残りを全割り当て)
part pv.01 --fstype="lvmpv" --size=1 --grow --ondisk=sda

# 4. ボリュームグループ (VG) の構築
volgroup vg_system pv.01

# 5. 論理ボリューム (LV) の切り分け
# root (/) ：50GB 固定 (環境に合わせてサイズ指定)
logvol / --fstype="xfs" --size=51200 --name=lv_root --vgname=vg_system

# swap ：8GB 固定
logvol swap --fstype="swap" --size=8192 --name=lv_swap --vgname=vg_system

# /data ：残りの全容量を拡張割り当て (--grow)
logvol /data --fstype="xfs" --size=1 --grow --name=lv_data --vgname=vg_system

# --------------------------------------------------
# インストール後の自動再起動
# --------------------------------------------------
reboot
```
### 主な追加・調整ポイント

1. **Minimal インストール（最小構成）**
    
    - `%packages` セクションで `@core` グループのみを指定することで Minimal Install となります。
        
2. **パスワード設定（`rootpw` / `user`）**
    
    - `--plaintext` オプションで平文指定できますが、Kickstart ファイルに生のパスワードが残るため、本番運用では事前に生成したハッシュ値（`--iscrypted`）を使うか、インストール後に公開鍵認証に移行することを推奨します。
        
    - 一般ユーザー（`appuser`）には `--groups=wheel` を付与し、`sudo` 実行可能に設定しています。
        
3. **NTP 設定（`timesource`）**
    
    - RHEL 9 / 10 系の標準構文である `timesource --ntp-server=<NTPサーバ>` を使用しています（例として日本の公開NTP `ntp.nict.jp` を指定）。


AlmaLinux（RHEL系）で `/data` ボリュームのデータを維持したまま、システム領域（`/` や `/boot` など）のみを初期化・再インストールする方法には、**「 Kickstart による自動再インストール」** と **「手動（GUI/CUIインストーラー）による再インストール」** の2通りのアプローチがあります。
### 方法1：Kickstart（自動化）で `/data` のみ維持する

Kickstart を使う場合、`clearpart`（全削除）を使わず、**不要な論理ボリューム（LV）のみを個別指定で削除・再作成**し、`/data` に対応する LV は削除対象から除外します。
#### Kickstart 記述例（ストレージ部分）

コード スニペット

```
# 1. 全削除 (clearpart --all) は絶対に使わない
# ディスクラベルの自動初期化も行わない

# 2. 既存の /boot や /boot/efi などを再利用（再フォーマット）
# ※既存のパーティションデバイス名（例: sda1, sda2）を指定して再フォーマット
part /boot/efi --onpart=sda1 --fstype="efi" --size=600 --fsoptions="defaults"
part /boot     --onpart=sda2 --fstype="xfs" --size=1024 --reformat

# 3. 既存の VG (vg_system) 内の不要な LV のみ削除・再作成
# root (/) ：再フォーマット指定 (--reformat)
logvol / --fstype="xfs" --size=51200 --name=lv_root --vgname=vg_system --reformat

# swap ：再フォーマット指定
logvol swap --fstype="swap" --size=8192 --name=lv_swap --vgname=vg_system --reformat

# 4. /data ：【最重要】--noformat を指定してフォーマットを回避
logvol /data --noformat --onlv=vg_system/lv_data
```

- **`--reformat`**: 該当の LV を初期化して新規作成します。
- **`--noformat`**: 既存データを保持したまま、指定したマウントポイント（`/data`）にマウントのみ行います。
   
### 方法2：インストーラー画面（手動）で指定する

インストール画面の「ストレージの破棄と割り当て（Custom Partitioning）」から手動で設定する場合の操作手順です。

1. **パーティション設定方式**で「LVM」を選択します。
2. 既存のボリュームグループ（`vg_system` 等）を展開します。    
3. **`/`（lv_root）および `/boot` 領域:**
    - 該当のボリュームを選択し、マウントポイント（`/` など）を設定。
    - **「フォーマットする (Format)」にチェック**を入れる。

4. **`/data`（lv_data）領域:**
    - 該当のボリュームを選択し、マウントポイントに `/data` と入力。        
    - **「フォーマットする (Format)」のチェックを外す（※厳禁）**。


### ⚠️ 作業前の重要・安全対策

- **事前にバックアップを採取する:** 操作ミスによる誤フォーマットを防ぐため、外部メディアやネットワークストレージ等へ `/data` 内の重要データをバックアップしておくことを強く推奨します。
- **マウント確認:** 再インストール完了後、`/etc/fstab` に `/data` が正しく記述されているか、データが認識されているかを `ls -l /data` や `df -h` で確認してください。