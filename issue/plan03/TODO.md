## やりたいこと
- ../../src/plur_linux/recipes/pxe/dhcpd.pyのセグメント設定は、env_opsで設定したsegmentsにセットアップ先のVMのIPが属しているか、セットアップ時にsegmentをしてしたときは、env_opsの値をもとにdhcpd.confを生成してください。dhcp rangeはセグメントの後半に4分の1確保し、最後の4つのIPは使用しないでください。例えば、192.168.0.0/24では251,252,253,254は使用しないでください。

## TODO
- [x] 上のやりたいことを実装して
