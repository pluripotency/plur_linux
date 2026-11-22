import os
from mini import misc


def get_plur_env_dir(env_dir=None):
    if env_dir:
        return os.path.expanduser(env_dir)
    env_dir_path = os.getenv("PLUR_ENV_DIR")
    if not env_dir_path:
        env_dir_path = "~/.plur"
    return os.path.expanduser(env_dir_path)


def sanitize_for_toml(value):
    if isinstance(value, dict):
        return {
            str(k): sanitize_for_toml(v)
            for k, v in value.items()
            if v is not None
        }
    if isinstance(value, (list, tuple)):
        return [sanitize_for_toml(v) for v in value if v is not None]
    if isinstance(value, (bool, int, float, str)):
        return value
    return str(value)


class TomlHistory:
    def __init__(self, filename, max_entries=10, env_dir=None, root_key="history"):
        self.env_dir = get_plur_env_dir(env_dir)
        self.file_path = os.path.join(self.env_dir, filename)
        self.max_entries = max_entries
        self.root_key = root_key

    def load_entries(self):
        if misc.is_file(self.file_path):
            data = misc.read_toml(self.file_path)
            if isinstance(data, dict):
                entries = data.get(self.root_key)
                if isinstance(entries, list):
                    return entries[: self.max_entries]
        return []

    def save_entries(self, entries):
        misc.prepare_dir_if_not_exists(self.env_dir)
        trimmed = list(entries)[: self.max_entries]
        payload = sanitize_for_toml({self.root_key: trimmed})
        return misc.write_toml(self.file_path, payload)

    def add_entry(self, entry):
        new_entry = dict(entry)
        if not new_entry.get("created_at"):
            new_entry["created_at"] = misc.now().strftime("%Y-%m-%d %H:%M:%S")
        sanitized_new = sanitize_for_toml(new_entry)
        entries = [sanitized_new] + self.load_entries()
        trimmed = entries[: self.max_entries]
        self.save_entries(trimmed)
        return trimmed

    def get_entry(self, index):
        entries = self.load_entries()
        if 0 <= index < len(entries):
            return entries[index]
        return None

    def clear(self):
        return self.save_entries([])
