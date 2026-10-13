## やりたいこと
- ../../src/plur_linux/recipes/pxe/kickstart.pyでは、create_a10_ks_strとcreate_ks_strはほぼ同じ内容でalmalinux10で使用するtimezone, timesourceの違いだけです。共通部分を抜き出し、almalinux10用を指定できるようにしてください。
- ../../src/plur_linux/recipes/pxe/kickstart.pyでは、ボリュームの指定ができていません。これも抜き出し、./LVM+xfs_data_on_ks.mdに書いてあるLVMと50Gのroot、dataに残りを指定するksをphy/vda/sdaで用意できるようにしてください。

## TODO
- [x] やりたいことを実装して (実装完了: [implementation_plan.md](implementation_plan.md))
  - `src/plur_linux/recipes/pxe/kickstart.py` において、`create_timezone_str`、`create_standard_volume_str`、`create_lvm_data_volume_str` を分離・共通化。
  - `create_ks_str` を統合し、`a10=True/False` によるタイムゾーン切り替えおよび `volume_type='standard'/'lvm_data'` によるストレージ構成切り替えをサポート。`create_a10_ks_str` は後方互換ラッパーとして保持。
  - `prepare_ks` を改修し、従来の `phy.ks`, `vda.ks`, `sda.ks` に加え、LVM構成の `phy_lvm.ks`, `vda_lvm.ks`, `sda_lvm.ks` の生成に対応。
  - `tests/test_kickstart.py` による単体テストを追加。
