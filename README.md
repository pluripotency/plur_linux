# Plur Linux

Plur Linux is a powerful, menu-driven automation tool for Linux server management and installation. It simplifies complex tasks like KVM guest provisioning, Docker deployments, Kubernetes cluster setup, and environment configuration through an intuitive interactive interface.

Built on top of the [plur](https://github.com/pluripotency/plur) library, it provides a collection of "recipes" for various Linux distributions (AlmaLinux, CentOS, Ubuntu) and a wide range of software stacks.

## Key Features

- **Interactive Menu Interface**: Navigate through administrative tasks without remembering complex commands.
- **KVM Management**: 
  - Create and provision virtual machines with custom configurations.
  - Expand guest volumes seamlessly.
  - Configure networking for defined nodes.
- **Rich Recipe Library**:
  - **OS Support**: AlmaLinux 8/9, CentOS, Ubuntu.
  - **Infrastructure**: Docker, Kubernetes (Kubeadm), Open vSwitch, Etcd, PXE.
  - **Services**: Nginx, FreeRADIUS, Syslog, RDP, vsftpd, Keepalived, Zabbix.
  - **Languages**: Automated setup for Rust, Go, Zig, Python (via pyenv), Node.js, Bun, and more.
- **Environment Configuration**: Manage SSH accounts, network segments, and KVM host details in a centralized way.
- **Ad Hoc Setup**: Quickly run setup tasks on remote or local nodes.

## Prerequisites

- Python 3.11 or higher.
- [uv](https://github.com/astral-sh/uv) (recommended for dependency management).
- SSH access to target nodes.

## Installation

Clone the repository and install dependencies:

```bash
git clone https://github.com/pluripotency/plur_linux.git
cd plur_linux
uv sync
```

## Usage

Start the main menu using the provided script:

```bash
./run.sh
```

Or run it directly with `uv`:

```bash
uv run server_menu
```

### Main Menu Options

1. **Ad Hoc Setup**: Execute specific setup tasks on selected nodes.
2. **KVM Menu**: 
   - Create defined guests.
   - Manage volumes and networking.
   - Perform post-installation tasks.
3. **Env Menu**:
   - **Set Account**: Manage SSH usernames and passwords for automation.
   - **Set KVM segments**: Define network segments (IP ranges, gateways, etc.).
   - **Set KVM**: Configure KVM host connection details.

## Project Structure

- `src/plur_linux/server_menu.py`: Main entry point for the interactive CLI.
- `src/plur_linux/recipes/`: Contains automation logic for various tools and services.
- `src/plur_linux/nodes/`: Definitions for different types of target nodes.
- `src/plur_linux/lib/`: Core utilities and environment management.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
