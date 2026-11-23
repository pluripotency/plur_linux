import copy
from plur import base_node
from plur_linux.lib.history import TomlHistory
from plur_linux.nodes import new_node

ADHOC_HISTORY_FILENAME = "adhoc_history.toml"
MAX_ADHOC_HISTORY = 10

CONNECT_KEYS = (
    "login_method",
    "hostname",
    "access_ip",
    "ssh_options",
    "size",
    "definexml",
    "restart_before_setup",
    "prepare_vdisk",
    "ifaces",
    "vnets",
    "org_hostname",
    "diskformat",
)

DEFAULT_CONNECT_METHODS = [
    "ssh",
    "bash",
    "virsh console",
    "create vm",
    "create vm by copy",
]


def extract_connect_dict(vm_dict):
    if not isinstance(vm_dict, dict):
        return {}
    login_method = vm_dict.get("login_method")
    if not login_method:
        hostname = vm_dict.get("hostname")
        return {"hostname": hostname} if hostname else {}
    if login_method == "bash":
        return {
            "login_method": "bash",
            "hostname": vm_dict.get("hostname", ""),
        }
    connect = {}
    for key in CONNECT_KEYS:
        if key in vm_dict and vm_dict[key] is not None:
            connect[key] = copy.deepcopy(vm_dict[key])
    return connect


def restore_connect_node_dict(connect_data, connect_method_list=None):
    if not isinstance(connect_data, dict) or "login_method" not in connect_data:
        return None, None
    login_method = connect_data["login_method"]
    allowed_methods = (
        connect_method_list if connect_method_list else DEFAULT_CONNECT_METHODS
    )
    if login_method not in allowed_methods:
        return None, None

    if login_method == "bash":
        me = base_node.Me()
        node_dict = copy.deepcopy(me.__dict__)
        node_dict["login_method"] = "bash"
        return "bash", node_dict

    node_dict = copy.deepcopy(connect_data)
    if "vnets" in node_dict and isinstance(node_dict["vnets"], list):
        for vnet in node_dict["vnets"]:
            if isinstance(vnet, dict) and "mac" in vnet:
                vnet["mac"] = new_node.random_mac()
    return login_method, node_dict


def build_adhoc_history_entry(os_label, vm_dict, post_run_list):
    resource = {
        "vcpu": int(vm_dict.get("vcpu", 2)),
        "vmem": int(vm_dict.get("vmem", 2048)),
    }
    account = {}
    if "username" in vm_dict and vm_dict["username"]:
        account["username"] = str(vm_dict["username"])

    connect = extract_connect_dict(vm_dict)
    post_run = [instance.to_history_dict() for instance in post_run_list]

    return {
        "os_label": os_label or vm_dict.get("platform", ""),
        "platform": vm_dict.get("platform", ""),
        "resource": resource,
        "account": account,
        "connect": connect,
        "post_run": post_run,
    }


def apply_history_to_post_run_list(post_run_list, entry):
    if not isinstance(entry, dict):
        return
    saved_items = entry.get("post_run", [])
    if not isinstance(saved_items, list):
        return
    remaining = list(saved_items)
    for instance in post_run_list:
        matched_idx = None
        for idx, saved in enumerate(remaining):
            if isinstance(saved, dict) and saved.get("menu_title") == instance.menu_title:
                matched_idx = idx
                break
        if matched_idx is not None:
            instance.apply_history_dict(remaining.pop(matched_idx))


def format_connect_summary(connect_data):
    if not isinstance(connect_data, dict):
        return "unknown"
    login_method = connect_data.get("login_method")
    hostname = connect_data.get("hostname", "")
    if not login_method:
        return f"guest(hostname:{hostname})" if hostname else "guest"
    if login_method == "create vm":
        from plur_linux.recipes.kvm import spawn

        access_ip = connect_data.get("access_ip", "")
        size = connect_data.get("size", "")
        mode = spawn.get_vm_boot_mode_label(connect_data)
        return f"create vm(hostname:{hostname} ip:{access_ip} size:{size}G mode:{mode})"
    if login_method == "create vm by copy":
        from plur_linux.recipes.kvm import spawn

        mode = spawn.get_vm_boot_mode_label(connect_data)
        return f"create vm by copy(hostname:{hostname} mode:{mode})"
    if login_method == "ssh":
        access_ip = connect_data.get("access_ip", "")
        return f"ssh(hostname:{hostname} ip:{access_ip})"
    return f"{login_method}(hostname:{hostname})"


def _format_post_run_item_brief(item):
    if not isinstance(item, dict) or not item.get("enable"):
        return None
    title = item.get("menu_title", "")
    selection = item.get("selection", {})
    if isinstance(selection, dict):
        enabled_keys = [k for k, v in selection.items() if v is True]
    else:
        enabled_keys = []
    if not enabled_keys:
        return title
    if len(enabled_keys) <= 3:
        return f"{title}({','.join(enabled_keys)})"
    shown = ",".join(enabled_keys[:2])
    return f"{title}({shown},+{len(enabled_keys) - 2})"


def format_history_entry(entry):
    created_at = entry.get("created_at", "")
    os_label = entry.get("os_label") or entry.get("platform", "unknown")
    con_str = format_connect_summary(entry.get("connect", {}))
    post_items = [
        s
        for s in (_format_post_run_item_brief(i) for i in entry.get("post_run", []))
        if s
    ]
    setup_str = ", ".join(post_items) if post_items else "none"
    if created_at:
        return f"[{created_at}] {os_label} | {con_str} | {setup_str}"
    return f"{os_label} | {con_str} | {setup_str}"


class AdhocHistory(TomlHistory):
    def __init__(
        self,
        filename=ADHOC_HISTORY_FILENAME,
        max_entries=MAX_ADHOC_HISTORY,
        env_dir=None,
    ):
        super().__init__(
            filename=filename,
            max_entries=max_entries,
            env_dir=env_dir,
            root_key="history",
        )

    def save_selection(self, os_label, vm_dict, post_run_list):
        entry = build_adhoc_history_entry(os_label, vm_dict, post_run_list)
        return self.add_entry(entry)
