from plur.base_shell import run, create_sequence
from plur.output_methods import waitprompt, send_line, send_pass
from recipes.openssl.ca_commands import rows_pem


def generate_ca_key_and_pem(cakey, cacert, passphrase, params, expiration_days='365'):
    def func(session):
        # PRIVATE KEY and CERTIFICATE
        # openssl req -new -x509 -keyout ca.key -out ca.pem \
        # -days $(CA_DEFAULT_DAYS) -config ./ca.cnf
        action = f'openssl req -new -x509 -keyout {cakey} -out {cacert} -days {expiration_days}'
        return session.do(create_sequence(action, rows_pem(cakey, passphrase, params)))
    return func


def generate_ca_der_from_pem(cacert, ca_der):
    # DER
    # openssl x509 -inform PEM -outform DER -in ca.pem -out ca.der
    action = f'openssl x509 -inform PEM -outform DER -in {cacert} -out {ca_der}'


def generate_server_key_and_csr(server_key, server_csr, passphrase, params):
    def func(session):
        # openssl req -new  -out server.csr -keyout server.key -config ./server.cnf
        action = 'openssl req -new  -out ' + server_csr + ' -keyout ' + server_key
        rows = rows_pem(server_key, passphrase, params)
        rows += [["Enter PEM pass phrase:", send_pass, passphrase, '']]
        rows += [["A challenge password .*:", send_pass, '', '']]
        rows += [["An optional company name .*:", send_pass, '', '']]

        session.do(create_sequence(action, rows))
    return func


def generate_server_crt(server_csr, server_crt, cakey, cacert, cakey_passphrase):
    def func(session):
        """ CERTIFICATE
         openssl ca -batch -keyfile ca.key -cert ca.pem -in server.csr /
         -key $(PASSWORD_CA) -out server.crt -extensions xpserver_ext /
         -extfile xpextensions -config ./server.cnf
        """
        xpextensions = '/etc/raddb/certs/xpextensions'
        action = 'openssl ca -batch -keyfile ' + cakey + ' -cert ' + cacert + \
                 ' -in ' + server_csr + ' -key ' + cakey_passphrase + \
                 ' -out ' + server_crt + ' -extensions xpserver_ext -extfile ' + xpextensions
        rows = [["Data Base Updated", waitprompt, True, '']]
        rows += [["", waitprompt, False, '']]
        return session.do(create_sequence(action, rows))
    return func


def generate_server_p12(server_key, key_pass, server_crt, server_p12, p12_pass):
    def func(session):
        """
        openssl pkcs12 -export -in server.crt -inkey server.key -out server.p12 /
         -passin pass:$(PASSWORD_SERVER) -passout pass:$(PASSWORD_SERVER)
        """
        action =  f'openssl pkcs12 -export -in {server_crt} -inkey {server_key} -out {server_p12}'
        rows = [["Enter pass phrase for {server_key}", send_pass, key_pass, '']]
        rows += [["Enter Export Password:", send_pass, p12_pass, '']]
        rows += [["", waitprompt, '', '']]

        return session.do(create_sequence(action, rows))
    return func


def generate_pkcs12(private_key_full_path, cert_full_path, pkcs12_full_path, pkcs12_password):
    action = f'openssl pkcs12 -export -in {cert_full_path} -inkey {private_key_full_path} -out {pkcs12_full_path}'
    rows = [['Enter Export Password:', send_pass, pkcs12_password, 'sending password']]
    rows += [['', waitprompt, '', 'created pkcs12']]
    return create_sequence(action, rows)


def generate_server_pem(server_p12, server_pem, p12_pass, pem_pass):
    def func(session):
        """
        openssl pkcs12 -in server.p12 -out server.pem -passin pass:$(PASSWORD_SERVER) /
         -passout pass:$(PASSWORD_SERVER)
        """
        action = f'openssl pkcs12 -in {server_p12} -out {server_pem}'
        rows = [["Enter Import Password:", send_pass, p12_pass, '']]
        rows += [["Enter PEM pass phrase:", send_pass, pem_pass, '']]
        rows += [["", waitprompt, '', '']]
        return session.do(create_sequence(action, rows))
    return func


def verify_server_pem(cacert, server_pem):
    return lambda session: run(session, f'openssl verify -CAfile {cacert} {server_pem}')


def generate_dh(dh_full_path):
    return lambda session: run(session, f'openssl dhparam -out {dh_full_path} 1024')


def generate_random(random_full_path):
    return lambda session: run(session, f'dd if=/dev/urandom of={random_full_path} count=2')


# not needed for ca and server key generation
def generate_certificate_request(private_key_full_path, csr_full_path, params):
    def func(session):
        action = f'openssl req -new -key {private_key_full_path} -out {csr_full_path}'
        rows = [[r'Country Name \(2 letter code\).+$', send_line, params.country_name, '']]
        rows += [[r'State or Province Name \(full name\).+$', send_line, params.state, '']]
        rows += [[r'Locality Name \(eg, city\).+$', send_line, params.city, '']]
        rows += [[r'Organization Name \(eg, company\).+$', send_line, params.organization, '']]
        rows += [[r'Organizational Unit Name.+$', send_line, params.org_unit, '']]
        rows += [[r"Common Name \(eg, your name or your server's hostname\).+$", send_line, params.common_name, '']]
        rows += [[r'Email Address.+$', send_line, '', '']]
        rows += [[r'A challenge password.+$', send_line, '', '']]
        rows += [[r'An optional company name.+$', send_line, '', '']]
        rows += [['', waitprompt, '', action]]
        return session.do(create_sequence(action, rows))
    return func


