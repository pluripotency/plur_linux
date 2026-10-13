from plur import base_shell
from plur import output_methods
from plur import session_wrap


def add_disk(dev='/dev/vdb', partition_index=1, mount_point='/export/brick'):
    partition = f'{dev}{partition_index}'
    @session_wrap.sudo
    def func(session):
        _ = [base_shell.run(session, a) for a in [
            f'parted -s -a optimal {dev} mklabel gpt -- mkpart primary xfs 1 -1',
            'sleep 3 && mkfs.xfs ' + partition,
            'mkdir -p ' + mount_point,
        ]]
        base_shell.append_line(f'{partition} {mount_point} xfs defaults 0 0', '/etc/fstab')(session)
        base_shell.run(session, 'mount -a')
    return func


def client_mount(brick='gvol0', mount_point='/mnt/MC', gluster_nodes=None):
    if gluster_nodes is None:
        gluster_nodes = ['glfs1', 'glfs2', 'glfs3']
    first = gluster_nodes[0]
    rest = ":".join(gluster_nodes[1:])
    fstab_entry = f'{first}:/{brick} {mount_point} glusterfs '
    fstab_entry += f'defaults,_netdev,backup-volfile-servers={rest} 0 0'

    @session_wrap.sudo
    def func(session):
        base_shell.run(session, 'mkdir -p ' + mount_point)
        file_path = '/etc/fstab'
        base_shell.append_line(fstab_entry, file_path)(session)
        base_shell.run(session, 'mount -a')
    return func


def peer_status(session):
    base_shell.run(session, 'gluster peer status')


def peer_probe(peer_node_list):
    if not isinstance(peer_node_list, list):
        print("err: gluster peer_node_list is not list")
        exit(1)

    # run from primary_node
    @session_wrap.sudo
    def func(session):
        _ = [base_shell.run(session, 'gluster peer probe ' + node) for node in peer_node_list]
    return func


def peer_detach(peer_node):
    @session_wrap.sudo
    def func(session):
        base_shell.run(session, 'gluster peer detach ' + peer_node)
    return func


def info(session):
    base_shell.run(session, 'gluster volume info')


def create_replica_on_first(all_node_list, brick='gvol0', brick_dir='/export/brick'):
    if not isinstance(all_node_list, list):
        print("err: gluster replica all_node_list is not list")
        exit(1)

    @session_wrap.sudo
    def func(session):
        peer_probe(all_node_list[1:])(session)
        args = [f'{node}:{brick_dir}/{brick}' for node in all_node_list]
        num = len(args)
        command = f'gluster volume create {brick} replica {str(num)} transport tcp '
        command += ' '.join(args)

        session.do(base_shell.create_sequence(command, [
            [r'\(y/n\) ', output_methods.send_line, 'y'],
            ['', output_methods.waitprompt, ''],
        ]))
        base_shell.run(session, 'gluster volume start ' + brick)
    return func


def add_brick_to_volume(target_node, target_size, brick='gvol0', brick_dir='/export/brick', gluster_type='replica'):
    @session_wrap.sudo
    def func(session):
        peer_probe([target_node])(session)
        command = f'gluster volume add-brick {brick} {gluster_type} {target_size} '
        command += f'{target_node}:{brick_dir}/{brick}'
        base_shell.run(session, command)
    return func


def remove_brick_to_volume(target_node, target_size, brick='gvol0', brick_dir='/export/brick', gluster_type='replica'):
    @session_wrap.sudo
    def func(session):
        peer_probe([target_node])(session)
        command = f'gluster volume remove-brick {brick} {gluster_type} {target_size} '
        command += f'{target_node}:{brick_dir}/{brick}'
        base_shell.run(session, command)

        peer_detach(target_node)(session)
    return func


# for automation reference
def gluster_create(brick='gvol0', brick_dir='/export/brick/', gluster_nodes=None):
    if gluster_nodes is None:
        gluster_nodes = ['glfs1', 'glfs2', 'glfs3']

    def func(session):
        base_shell.run(session, 'service glusterd restart')
        brick_path = brick_dir + brick
        for n in gluster_nodes[1:]:
            base_shell.run(session, 'gluster peer probe ' + n)

        base_shell.run(session, 'mkdir -p ' + brick_path)
        action = f'gluster vol create {brick} replica {len(gluster_nodes)} '
        action += ' '.join([f'{node}:{brick_path}' for node in gluster_nodes])
        base_shell.run(session, action)
        base_shell.run(session, 'gluster vol start ' + brick)
    return func


def gluster_join(brick='gvol0', brick_dir='/export/brick/', gluster_node='gluster002'):
    def func(session):
        base_shell.run(session, 'service glusterd restart')
        brick_path = brick_dir + brick
        # from aliving node
        # add probe_node to brick
        actions = [
            'gluster peer probe ' + gluster_node,
            f'gluster vol add-brick {brick} replica 2 {gluster_node}:{brick_path}'
        ]
        _ = [base_shell.run(session, a) for a in actions]
    return func


def gluster_detach(session):
    # from aliving node
    brick = 'gvol0'
    brick_path = '/export/brick/' + brick
    detach_node = 'glfs1'

    # remove detach_node from brick
    action = f'gluster vol remove-brick {brick} replica 1 {detach_node}:{brick_path} force'
    rows = [
        [r'Continue\? \(y/n\)', output_methods.send_line, 'y', ''],
        ['success', output_methods.success, '', ''],
    ]
    session.do(base_shell.create_sequence(action, rows))

    # detach detach_node
    base_shell.run(session, 'gluster peer detach ' + detach_node)
