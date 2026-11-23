## Question1
virt-installコマンドでkvm仮想マシンを起動すると、最初のrebootコマンドが必ずshutdownになってしまうことを避けるすべはある？

## Answer1
はい、用途に合わせて **`--import`**、**`--wait=-1`**、または **`--events on_reboot=restart`** のいずれかのオプションを指定することで回避できます。

### なぜ最初の `reboot` がシャットダウンになるのか

`virt-install` はOSインストール用の初回起動時、一時的に `<on_reboot>destroy</on_reboot>` を設定します。インストール完了後の再起動タイミングで一度VMを停止させ、インストール用ISOの切り離しやブート順序の変更を行ってから再起動させるための仕様です。

そのため、`--noautoconsole` などで `virt-install` コマンド自体が先に終了していると、初回 `reboot` で停止したまま自動起動されず、シャットダウン状態になります。

---

### 回避方法（用途別）

#### 1. 作成済みディスク・クラウドイメージから起動する場合（最も推奨）

OSのインストール作業が不要な場合は、**`--import`** オプションを付けます。インストールフェーズがスキップされ、初回起動時から `<on_reboot>restart</on_reboot>` が適用されます。

```bash
virt-install --name my-vm --disk path=/path/to/image.qcow2 --import ...

```

#### 2. ISO等からインストールし、完了後に自動で再起動させたい場合

`--noautoconsole` を使用している場合でも、**`--wait=-1`** を併用します。`virt-install` がインストール完了（初回シャットダウン）まで待機し、インストール用設定を解除したうえで自動的にVMを再起動します。

```bash
virt-install --name my-vm --cdrom /path/to/os.iso --noautoconsole --wait=-1 ...

```

※ `--noreboot` オプションを付けている場合は自動再起動されないため外してください。

#### 3. 初回起動時から強制的に `restart` 扱いにしたい場合

**`--events on_reboot=restart`** を明示的に指定します。

```bash
virt-install --name my-vm --events on_reboot=restart ...

```

※ **注意点:** `--cdrom` や `--location` を使った通常インストールでこのオプションを使うと、再起動時にインストールメディアが外れず、再度インストーラが起動してしまう場合があります。ブート順序が適切に制御されている環境向けです。

---

### 設定の確認方法

VM起動後、ホスト側で以下のコマンドを実行し、`<on_reboot>restart</on_reboot>` と出力されれば、初回から再起動が正常に機能する状態です。

```bash
virsh dumpxml <VM名> | grep on_reboot

```

## Question2
起動したあとの再起動が必要な方法は選択肢にないです。--importを試しましたが全く効果がありません。virt-installで仮想マシンのxmlファイルだけ作成してそれをvirsh defineして起動する方法は？ただし、virt-installでxmlを出力すると最新版でもバグで壊れたxmlが表示されます。

## Answer2
`virt-install` でXMLを出力した際に壊れたように見える原因は、バグではなく「2つの `<domain>` ブロックが連結されて出力される仕様」によるものです。`--print-xml` にステップ番号を指定することで、単一の正常なXMLを出力し、`virsh define` から起動できます。

### 1. XMLが壊れて見える原因と対処

`--print-xml` を引数なしで実行すると、インストール時（1回目）と通常起動時（2回目）の **2つの `<domain>...</domain>` が1つの出力に連続して書き出されます**。これをそのまま `virsh define` に渡すと、XMLパースエラーになります。

以下のように **`--print-xml 1`** または **`--print-xml 2`** と番号を指定すると、単一の有効なXMLだけが出力されます。

* **`--print-xml 1`**: 初回起動用の構成（ISOやシードイメージがマウントされた状態）
* **`--print-xml 2`**: 2回目以降の通常起動用の構成（インストール用メディアが外れた状態）

---

### 2. XML生成 → `virsh define` → 起動の手順

既存のディスクイメージ等から起動し、初回から `reboot` を有効にする手順です。

1. **単一のXMLを出力する**
`--events on_reboot=restart` を付け、`--print-xml 2`（初回起動時にISO等のマウントが必要な場合は `--print-xml 1`）でファイルに書き出します。
```bash
virt-install \
  --name my-vm \
  ...（既存のオプション） \
  --events on_reboot=restart \
  --print-xml 2 > my-vm.xml

```


*確認:* `grep -c "<domain" my-vm.xml` を実行し、`1` と表示されれば単一のXMLとして出力されています。
2. **`<on_reboot>` の設定を確認・修正する**
`--print-xml 1` を使った場合など、XML内に `destroy` が残っている場合は置換します。
```bash
sed -i 's|<on_reboot>destroy</on_reboot>|<on_reboot>restart</on_reboot>|g' my-vm.xml

```


*確認:* `grep on_reboot my-vm.xml` で `<on_reboot>restart</on_reboot>` になっていることを確認します。
3. **VMを定義して起動する**
```bash
virsh define my-vm.xml
virsh start my-vm

```


*確認:* `virsh dumpxml my-vm | grep on_reboot` を実行し、稼働中の設定でも `<on_reboot>restart</on_reboot>` になっていれば、初回からの `reboot` が正常に動作します。

---

### 補足：`--import` が効かなかった主な原因

`--import` を指定しても初回 `reboot` がシャットダウンになる場合、**`--cloud-init`** を併用しているケースが大半です。`virt-install` は `--cloud-init` 用のシードISOを初回起動後に切り離すため、`--import` を付けていても強制的に2段階起動（`on_reboot=destroy`）として処理します。

なお、`--cloud-init` と `--print-xml` を組み合わせる場合、シードISOは一時ファイルとして生成され `virt-install` 終了時に削除されるため、`--print-xml` 方式を使う際は `cloud-localds` 等で事前にシードISOを作成し、`--disk path=seed.iso,device=cdrom` として渡す必要があります。
