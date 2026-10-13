## やりたいこと
- ./src/plur_linux/lib/env_ops.pyはsegmentsでkvm仮想マシンのセグメントを設定していますが、IPv4のフォーマットを簡単にするために、ip_base_prefixとprefixでセグメント情報を保持し、仮想マシンのIPをセグメントとip_seedを指定することで決定していました。しかし、これだと/24より数字が小さいPrefixに対応できません。
- ip_base_prefix, prefixでの対応をやめ、network_with_prefixとして172.16.0.0/22などの値を取り、intの1を設定すると172.16.0.1を取得でき、strの'1.5'を指定すると172.16.1.5を取得でき、'4.1'を指定すると’IP Range Error'を返せるようにしたいです。
- ip_seedによる設定や、ip_base_prefixを直接使用したip設定はコードに散らばっているので、どのように変更するかが課題です。

## TODO
- [x] 上記を実現する方法を提案して (実装完了: [implementation_plan.md](implementation_plan.md))
  - `src/plur_linux/lib/ip_calc.py` を新設し、`network_with_prefix` (CIDR記法) から `int` (オフセット) および `str` ('1.5' 等のドット記法) によるIP計算、範囲外時の `'IP Range Error'` 返却 / `IPRangeError` 例外送出を実装。
  - `src/plur_linux/lib/env_ops.py` のセグメント定義・一覧表示・`bind_env` を更新し、旧形式 (`ip_base_prefix` / `prefix`) との後方互換性を担保。
  - 各レシピ・ノード生成コード (`kubeadm_a9.py`, `gluster.py`, `new_node.py`) の直接文字列結合を `get_ip_from_segment` ヘルパー呼び出しに集約。
  - `tests/test_ip_calc.py` による単体テストを追加。
