# Velum OS

> Enterprise Linux distribution built for security, sovereignty, and community trust.

Velum OS is a Linux distribution **based on Debian Server**, designed to compete directly against closed corporate solutions (such as RHEL/IBM). It introduces a bidimensional **Zero Trust security model** that no traditional enterprise OS provides out of the box.

---

## Why Velum OS?

- **No corporate lock-in** — Built on Debian, the most stable and community-governed Linux base. No snap traps, no code source restrictions, no IBM strings attached.
- **AGPLv3 Shield License** — If any corporation runs Velum OS as a cloud service (SaaS), they are legally required to release all their modifications back to the community. This closes the cloud loophole that standard GPL licenses leave open.
- **Privacy by design** — Contributor identities are protected via anonymous GitHub handles and encrypted email (ProtonMail).

---

## Security Architecture — The Matrix Model

Velum OS replaces traditional RBAC (one-dimensional role access) with a **bidimensional ABAC (Attribute-Based Access Control)** model.

Access is granted only when **both** attributes match:

| | Accounting | Systems | HR | Legal | Management |
|---|---|---|---|---|---|
| **Layer 4** (Ultra Critical) | GPG + LUKS + SSH + YubiKey | GPG + LUKS + SSH + YubiKey | GPG + LUKS + SSH + YubiKey | GPG + LUKS + SSH + YubiKey | GPG + LUKS + SSH + YubiKey |
| **Layer 3** (Critical) | GPG at rest + YubiKey | GPG at rest + YubiKey | GPG at rest + YubiKey | GPG at rest + YubiKey | GPG at rest + YubiKey |
| **Layer 2** (Restricted) | MFA + SSH/GPG keys | MFA + SSH/GPG keys | MFA + SSH/GPG keys | MFA + SSH/GPG keys | MFA + SSH/GPG keys |
| **Layer 1** (Standard) | LUKS full-disk encryption | LUKS full-disk encryption | LUKS full-disk encryption | LUKS full-disk encryption | LUKS full-disk encryption |

> If both attributes (department + layer) do not match the matrix, access is explicitly denied via ACL — not just withheld.

### How departments work
Managed via **Samba 4 in Active Directory mode**, compatible with Windows, macOS, and Linux clients simultaneously. Each department is an independent Organizational Unit (OU). A user in Accounting cannot see anything in Systems, even at the same Layer.

### How layers work
- **Layer 1** — End-user workstations. Full-disk encryption with LUKS protects against physical theft.
- **Layer 2** — Mid-tier servers. Requires MFA + SSH/GPG key pairs.
- **Layer 3** — Critical data encrypted at rest with asymmetric GPG. Requires a physical hardware token (YubiKey). Even a Layer 2 admin cannot list the file structure of Layer 3.
- **Layer 4** — Ultra critical. Combines all mechanisms from all previous layers. YubiKey alone or full three-layer combination required.

---

## Roadmap

### Phase 1 — Core Scripts (Bash) ✅ Tested on Debian 13
Automates deployment of the base security structure on a clean Debian Server:
- `departments.conf` — defines departments and layers (fully customizable per organization)
- `folders.sh` — creates the `/velum/dept/layerN/` directory matrix
- `users.sh` — creates Linux groups and applies explicit ABAC permissions via `setfacl`
- `kernel.sh` — applies kernel hardening rules (USB lockdown, SUID removal, process isolation, privilege escalation prevention)
- `install.sh` — main orchestrator

### Phase 2 — Cryptographic Engine 🔲 Planned
- Automated `cryptsetup` (LUKS) management
- Python scripts for GPG encryption/decryption on Layer 3
- YubiKey integration for Layer 3 and 4
- Post-quantum cryptography for the orchestration API

### Phase 3 — Web Orchestration Panel 🔲 Planned
- Lightweight web UI (Go or Python) to manage the security matrix without touching the terminal
- Mandatory "View Source Code" button in compliance with AGPLv3
- Support for Windows Enterprise, Windows Server, and Red Hat environments

### Phase 4 — Full Distribution 🔲 Planned
- Package everything as `.deb`
- Own signed APT repository
- ISO generation with `live-build`
- Bootable, distributable Velum OS image

---

## Getting Started

> Phase 1 requires a clean Debian Server installation.

```bash
git clone https://github.com/Velum-os-project/Velum-os-core.git
cd Velum-os-core
chmod +x phase1-core/install.sh phase1-core/lib/*.sh
bash phase1-core/install.sh
```

To customize departments and layers, edit `phase1-core/config/departments.conf` before running the installer. The scripts are **idempotent** — you can run them multiple times without breaking existing configurations.

---

## License

This project is licensed under the **GNU Affero General Public License v3.0 (AGPLv3)**.

See [LICENSE](LICENSE) for the full license text, or visit [https://www.gnu.org/licenses/agpl-3.0.html](https://www.gnu.org/licenses/agpl-3.0.html).

---

## Contributing

Contributor identities are protected. Use anonymous GitHub handles and encrypted email when contributing.

Contact: velum_os_project@proton.me
