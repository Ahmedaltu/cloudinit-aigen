"""Module docs tool: inline reference for common cloud-init modules."""

MODULE_DOCS: dict[str, str] = {
    "users": """
users:
  - name: <username>
    sudo: ALL=(ALL) NOPASSWD:ALL
    groups: sudo, docker
    shell: /bin/bash
    ssh_authorized_keys:
      - ssh-ed25519 AAAA...
    lock_passwd: true
""",
    "packages": """
packages:
  - package-name
package_update: true
package_upgrade: true
""",
    "runcmd": """
runcmd:
  - command string
  - [list, form, also, valid]
""",
    "ssh_authorized_keys": """
users:
  - name: <username>
    ssh_authorized_keys:
      - ssh-ed25519 AAAA...
""",
    "write_files": """
write_files:
  - path: /etc/myapp/config.yaml
    content: |
      key: value
    owner: root:root
    permissions: '0644'
""",
    "hostname": "hostname: my-vm\nfqdn: my-vm.example.com\nmanage_etc_hosts: true\n",
    "timezone": "timezone: Europe/Helsinki\n",
}


def lookup_module(module_name: str) -> str:
    doc = MODULE_DOCS.get(module_name)
    if doc:
        return f"# cloud-init module: {module_name}\n{doc}"
    return f"# No inline docs for '{module_name}'. See https://cloudinit.readthedocs.io/en/latest/reference/modules.html"
