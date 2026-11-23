## やりたいこと
- まず、./issue/plan06/virt-install.mdを読んでください。
- 問題は、virt-installで仮想マシンを起動すると、rebootコマンドがshutdownになってしまうことです。これをなんとしても避けたいです。
- virt-installのバグなのか仕様なのかわからない理由で、実動作を試さないと解決しないことがわかっています。
- まずはvirt-install.mdの--print-xml 1でcloudinitのインストールを完了し、virshのcdromイジェクトでインストールを完了する手順を試したいです。
- ./src/plur_linux/recipes/kvm/spawn.pyのcreate_vm_virt_install_cloudinitでdo_definexmlを追加し、選択肢を増やし、start_domain_by_define_xmlを追加して、--print-xml 1とvirsh define、virsh startする経路を追加して
