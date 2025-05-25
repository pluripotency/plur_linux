from recipes.docker import mariadb


def create_db_queries_str(db_name, db_user, db_pass):
    queries = f"""CREATE DATABASE {db_name};
    grant all privileges on {db_name}.* to {db_user}@'%' identified by '{db_pass}';
    FLUSH PRIVILEGES;"""
    return queries


def create_radius_client_insert_str(client_name, ipaddr, secret):
    """
    >>> create_radius_client_insert_str('localnet', '192.168.122.0/24', 'Password')
    "insert into nas (nasname,shortname,type,ports,secret,server,community,description) values ('192.168.122.0/24','localnet','',0,'Password','','','');"

    :param client_name:
    :param ipaddr:
    :param secret:
    :return:
    """
    escaped_secret = secret.replace('!', r'\!')
    attrs = [
        'nasname',
        'shortname',
        'type',
        'ports',
        'secret',
        'server',
        'community',
        'description',
    ]
    set_attrs = [
        f"'{ipaddr}'",
        f"'{client_name}'",
        "''",
        '0',
        f"'{escaped_secret}'",
        "''",
        "''",
        "''",
    ]
    return "insert into nas (" + ','.join(attrs) + ') values (' + ','.join(set_attrs) + ');'


def create_user_insert_str(username, password):
    """
    >>> create_user_insert_str('user001', 'Password')
    "insert into radcheck (username,attribute,op,value) VALUES ('user001','Cleartext-Password',':=','Password');"

    :param username:
    :param password:
    :return:
    """
    escaped_password = password.replace('!', r'\!')
    attrs = [
        'username',
        'attribute',
        'op',
        'value',
    ]
    set_attrs = [
        f"'{username}'",
        "'Cleartext-Password'",
        "':='",
        f"'{escaped_password}'",
    ]
    return "insert into radcheck (" + ','.join(attrs) + ") VALUES (" + ','.join(set_attrs) + ");"


def load_schema_for_new_db(container_name, mysql_root_password, db_name, db_user, db_pass, schema_path):
    def func(session):
        mariadb.load_query(container_name, mysql_root_password, '',
                           create_db_queries_str(db_name, db_user, db_pass))(session)
        mariadb.load_sql_file(container_name, mysql_root_password, db_name, schema_path)(session)
    return func


def load_radius_clients(container_name, mysql_root_password, db_name, radius_clients):
    def func(session):
        insert_rad_clients = ''.join(
            [create_radius_client_insert_str(s['client_name'], s['ipaddr'], s['secret']) for s in radius_clients])
        mariadb.load_query(container_name, mysql_root_password, db_name, insert_rad_clients)(session)
    return func


def load_user_list(container_name, mysql_root_password, db_name, user_list):
    def func(session):
        insert_users = ''.join([create_user_insert_str(s['username'], s['password']) for s in user_list])
        mariadb.load_query(container_name, mysql_root_password, db_name, insert_users)(session)
    return func


def run(container_name, db_params, radius_clients, user_list):
    mysql_root_password = db_params['mysql_root_password']
    db_name = db_params['db_name']
    db_user = db_params['db_user']
    db_pass = db_params['db_pass']
    schema_path = 'schema.sql'

    def func(session):
        load_schema_for_new_db(container_name, mysql_root_password, db_name, db_user, db_pass, schema_path)(session)

        load_radius_clients(container_name, mysql_root_password, db_name, radius_clients)(session)
        load_user_list(container_name, mysql_root_password, db_name, user_list)(session)

    return func
