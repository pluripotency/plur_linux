FROM ubuntu:22.04

RUN apt-get update && apt-get install -y tftpd-hpa tftp-hpa && apt-get clean && rm -rf /var/lib/apt/lists/*
ARG USERNAME=tftp_user
ARG UID=1000
RUN groupadd -g $UID $USERNAME && useradd -u $UID -g $UID -m $USERNAME
USER $USERNAME
WORKDIR /home/$USERNAME
RUN mkdir tftpboot
USER root
CMD ["/usr/sbin/in.tftpd","--foreground","--user","tftp_user","--create","--address","0.0.0.0:69","--secure","/home/tftp_user/tftpboot"]
