FROM alpine:latest
RUN apk add --no-cache dhcp

EXPOSE 67/udp
RUN mkdir -p /var/lib/dhcpd && touch /var/lib/dhcpd/dhcpd.leases
CMD ["/usr/sbin/dhcpd", "-4", "-f", "-d", "--no-pid", "-cf", "/etc/dhcp/dhcpd.conf", "-lf", "/var/lib/dhcpd/dhcpd.leases"]
