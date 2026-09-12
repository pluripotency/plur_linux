import ipaddress
import json
from mini import misc
from plur import session_wrap
from plur import base_shell
from plur_linux.recipes import firewalld
from plur_linux.recipes.pxe import dhcpd

DEFAULT_COMPOSE_DIR = '/etc/pxe-docker'
DEFAULT_NGINX_IMAGE = 'nginx:alpine'
DEFAULT_KEA_IMAGE = 'isc/kea-dhcp4:latest'
DEFAULT_TFTP_IMAGE = 'ghcr.io/linuxserver/tftp-hpa:latest'


def create_nginx_conf_str(alias, dir_path, allowed_net=None):
    """Generate Nginx configuration for PXE HTTP server."""
    clean_alias = '/' + alias.strip('/')
    clean_dir = dir_path.rstrip('/')

    access_blocks = []
    if allowed_net:
        access_blocks = [
            "    allow 127.0.0.1;",
            f"    allow {allowed_net};",
            "    deny all;",
        ]
    access_str = "\n".join(access_blocks)
    if access_str:
        access_str = "\n" + access_str + "\n"

    content = f"""server {{
    listen 80 default_server;
    server_name _;

    root /var/www/html;
    autoindex on;{access_str}
    location / {{
        try_files $uri $uri/ =404;
    }}

    location /ks {{
        alias /var/www/html/ks;
        autoindex on;
    }}

    location {clean_alias}/ {{
        alias {clean_dir}/;
        autoindex on;
    }}

    location = {clean_alias} {{
        return 301 {clean_alias}/;
    }}
}}
"""
    return content


def create_kea_conf_str(pxe_ip, subnet_params):
    """Generate ISC Kea DHCPv4 JSON configuration."""
    subnet = subnet_params['subnet']
    netmask = subnet_params['netmask']
    allowed_net = subnet_params.get('allowed_net')
    if allowed_net:
        subnet_cidr = allowed_net
    else:
        net = ipaddress.IPv4Network(f"{subnet}/{netmask}", strict=False)
        subnet_cidr = str(net)

    dh_range = subnet_params.get('dh_range', '')
    if ' ' in dh_range.strip():
        dh_start, dh_end = dh_range.strip().split()[:2]
        pool_str = f"{dh_start} - {dh_end}"
    else:
        pool_str = dh_range

    gateway = subnet_params.get('gateway', str(ipaddress.IPv4Network(subnet_cidr).network_address + 1))
    nameservers = subnet_params.get('nameservers', '8.8.8.8')
    domain_name = subnet_params.get('domain_name', 'local')

    conf = {
        "Dhcp4": {
            "interfaces-config": {
                "interfaces": ["*"]
            },
            "lease-database": {
                "type": "memfile",
                "persist": True,
                "name": "/tmp/kea-leases4.csv"
            },
            "valid-lifetime": 7200,
            "renew-timer": 600,
            "rebind-timer": 1200,
            "option-data": [
                {
                    "name": "domain-name",
                    "data": domain_name
                },
                {
                    "name": "domain-name-servers",
                    "data": nameservers
                }
            ],
            "client-classes": [
                {
                    "name": "UEFI-64",
                    "test": "option[93].hex == 0x0007 or option[93].hex == 0x0009",
                    "boot-file-name": "BOOTX64.EFI"
                },
                {
                    "name": "BIOS-x86",
                    "test": "not (option[93].hex == 0x0007 or option[93].hex == 0x0009)",
                    "boot-file-name": "pxelinux.0"
                }
            ],
            "subnet4": [
                {
                    "id": 1,
                    "subnet": subnet_cidr,
                    "pools": [
                        {
                            "pool": pool_str
                        }
                    ],
                    "option-data": [
                        {
                            "name": "routers",
                            "data": gateway
                        },
                        {
                            "name": "domain-name-servers",
                            "data": nameservers
                        }
                    ],
                    "next-server": pxe_ip,
                    "boot-file-name": "pxelinux.0"
                }
            ]
        }
    }
    return json.dumps(conf, indent=2) + "\n"


def create_docker_compose_str(
    compose_dir=DEFAULT_COMPOSE_DIR,
    www_iso_dir='/var/pxe',
    nginx_image=DEFAULT_NGINX_IMAGE,
    kea_image=DEFAULT_KEA_IMAGE,
    tftp_image=DEFAULT_TFTP_IMAGE,
):
    """Generate docker-compose.yml configuration with host network mode."""
    clean_compose_dir = compose_dir.rstrip('/')
    clean_iso_dir = www_iso_dir.rstrip('/')

    content = f"""services:
  nginx:
    image: {nginx_image}
    container_name: pxe-nginx
    restart: unless-stopped
    network_mode: host
    volumes:
      - {clean_compose_dir}/nginx.conf:/etc/nginx/conf.d/default.conf:ro
      - /var/www/html:/var/www/html:ro
      - {clean_iso_dir}:{clean_iso_dir}:ro

  kea:
    image: {kea_image}
    container_name: pxe-kea
    restart: unless-stopped
    network_mode: host
    volumes:
      - {clean_compose_dir}/kea-dhcp4.conf:/etc/kea/kea-dhcp4.conf:ro

  tftpd:
    image: {tftp_image}
    container_name: pxe-tftp
    restart: unless-stopped
    network_mode: host
    environment:
      - PUID=0
      - PGID=0
      - TFTPD_OPTS=--secure
    volumes:
      - /var/lib/tftpboot:/tftpboot:ro
      - /var/lib/tftpboot:/var/lib/tftpboot:ro
      - /var/lib/tftpboot:/var/tftpboot:ro
"""
    return content


def prepare_compose_files(
    session,
    pxe_ip,
    dist_dir,
    www_iso_dir,
    subnet_params=None,
    compose_dir=DEFAULT_COMPOSE_DIR,
    allowed_net=None,
    nginx_image=DEFAULT_NGINX_IMAGE,
    kea_image=DEFAULT_KEA_IMAGE,
    tftp_image=DEFAULT_TFTP_IMAGE,
):
    """Prepare directories and write configuration files for docker-compose."""
    if subnet_params is None:
        subnet_params = dhcpd.get_subnet_params(pxe_ip=pxe_ip)

    if allowed_net is None:
        allowed_net = subnet_params.get('allowed_net')

    base_shell.run(session, f'mkdir -p {compose_dir} /var/lib/tftpboot /var/www/html/ks {www_iso_dir}')

    nginx_conf = create_nginx_conf_str(alias=f'/{dist_dir}', dir_path=www_iso_dir, allowed_net=allowed_net)
    kea_conf = create_kea_conf_str(pxe_ip=pxe_ip, subnet_params=subnet_params)
    compose_yml = create_docker_compose_str(
        compose_dir=compose_dir,
        www_iso_dir=www_iso_dir,
        nginx_image=nginx_image,
        kea_image=kea_image,
        tftp_image=tftp_image,
    )

    base_shell.here_doc(session, f'{compose_dir}/nginx.conf', nginx_conf.split('\n'))
    base_shell.here_doc(session, f'{compose_dir}/kea-dhcp4.conf', kea_conf.split('\n'))
    base_shell.here_doc(session, f'{compose_dir}/docker-compose.yml', compose_yml.split('\n'))


def start_containers(session, compose_dir=DEFAULT_COMPOSE_DIR):
    """Start PXE services via docker compose."""
    base_shell.run(session, f'docker compose -f {compose_dir}/docker-compose.yml up -d')


def stop_containers(session, compose_dir=DEFAULT_COMPOSE_DIR):
    """Stop PXE services via docker compose."""
    base_shell.run(session, f'docker compose -f {compose_dir}/docker-compose.yml down')


def setup_pxe_compose(
    pxe_ip,
    dist_dir,
    www_iso_dir,
    segment=None,
    compose_dir=DEFAULT_COMPOSE_DIR,
    set_fw=True,
    nginx_image=DEFAULT_NGINX_IMAGE,
    kea_image=DEFAULT_KEA_IMAGE,
    tftp_image=DEFAULT_TFTP_IMAGE,
):
    """Setup PXE base services using Docker Compose (Nginx, Kea DHCP, TFTP)."""
    subnet_params = dhcpd.get_subnet_params(pxe_ip=pxe_ip, segment=segment)
    allowed_net = subnet_params.get('allowed_net', f"{subnet_params['subnet']}/24")

    @session_wrap.sudo
    def func(session):
        if set_fw:
            firewalld.configure(services=['dhcp', 'tftp', 'http'], add=True)(session)

        prepare_compose_files(
            session=session,
            pxe_ip=pxe_ip,
            dist_dir=dist_dir,
            www_iso_dir=www_iso_dir,
            subnet_params=subnet_params,
            compose_dir=compose_dir,
            allowed_net=allowed_net,
            nginx_image=nginx_image,
            kea_image=kea_image,
            tftp_image=tftp_image,
        )
        start_containers(session, compose_dir=compose_dir)

    return func
