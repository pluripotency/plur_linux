FROM centos:7

RUN yum install -y freeradius freeradius-utils freeradius-mysql iproute
COPY init.sh /

EXPOSE 1812 1813

ENTRYPOINT ["/init.sh"]
