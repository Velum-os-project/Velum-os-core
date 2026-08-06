# ==============================================================================
# Velum OS - Core Enterprise Infrastructure
# Copyright (C) 2026 Velum OS Project Contributors <velum_os_project@proton.me>
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published
# by the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program. If not, see <https://gnu.org>.
# ==============================================================================

# cython: language_level=3
# --- Velum OS - Phase 2 Main Installer ---

import os
import sys

# Import modules directly — no subprocess calls.
# When compiled with Cython, all modules are linked into the same binary.
from luks import setup_luks
from gpg_engine import encrypt_directory
from vta import init_directories, generate_root_ca, generate_intermediate_ca

CONFIG_PATH    = os.path.join(os.path.dirname(__file__), "../phase1-core/config/departments.conf")
DEPLOY_CONFIG  = "/etc/velum/deploy.conf"


def load_departments() -> list:
    """Read departments from departments.conf."""
    departments = []
    with open(CONFIG_PATH, "r") as f:
        inside = False
        for line in f:
            line = line.strip()
            if line.startswith("DEPARTMENTS=("):
                inside = True
                continue
            if inside:
                if line == ")":
                    break
                dept = line.strip('"').strip("'")
                if dept:
                    departments.append(dept)
    return departments


def prompt_deploy_config() -> dict:
    """Ask the admin for deployment-specific configuration interactively."""
    print("\n[phase2] Deployment configuration")
    print("[phase2] This information will be stored in /etc/velum/deploy.conf")
    print()

    gpg_recipient = input("  GPG recipient email for Layer 3 encryption: ").strip()
    if not gpg_recipient:
        print("[phase2] Error: GPG recipient cannot be empty.")
        sys.exit(1)

    return {
        "gpg_recipient": gpg_recipient,
    }


def save_deploy_config(config: dict) -> None:
    """Save deployment configuration to /etc/velum/deploy.conf."""
    os.makedirs("/etc/velum", exist_ok=True)
    with open(DEPLOY_CONFIG, "w") as f:
        for key, value in config.items():
            f.write(f"{key}={value}\n")
    os.chmod(DEPLOY_CONFIG, 0o600)
    print(f"[phase2] Configuration saved to {DEPLOY_CONFIG}")


def load_deploy_config() -> dict:
    """Load existing deployment configuration if it exists."""
    config = {}
    if os.path.exists(DEPLOY_CONFIG):
        with open(DEPLOY_CONFIG, "r") as f:
            for line in f:
                line = line.strip()
                if "=" in line and not line.startswith("#"):
                    key, value = line.split("=", 1)
                    config[key.strip()] = value.strip()
    return config


def step(msg: str) -> None:
    print(f"\n[phase2] {msg}")


def main():
    if os.geteuid() != 0:
        print("[phase2] Error: must be run as root.")
        sys.exit(1)

    departments = load_departments()
    print(f"[phase2] Departments loaded: {', '.join(departments)}")

    # Load or prompt deployment config
    config = load_deploy_config()
    if not config:
        config = prompt_deploy_config()
        save_deploy_config(config)

    gpg_recipient = config.get("gpg_recipient", "")
    if not gpg_recipient:
        print("[phase2] Error: gpg_recipient missing from deploy.conf.")
        sys.exit(1)

    # Step 1: Initialize VTA directory structure
    step("Initializing Velum Trust Authority...")
    init_directories()

    # Step 2: Generate root CA
    step("Generating VTA root CA (stored in Layer 4)...")
    generate_root_ca()

    # Step 3: Generate intermediate CA per department
    step("Generating intermediate CAs per department...")
    for dept in departments:
        print(f"[phase2]   -> {dept}")
        generate_intermediate_ca(dept)

    # Step 4: LUKS setup note
    step("LUKS encryption setup...")
    print("[phase2] Note: LUKS requires a keyfile path configured per deployment.")
    print("[phase2] Run luks binary manually with your keyfile after installation.")

    # Step 5: Encrypt Layer 3 directories with GPG
    step("Encrypting Layer 3 directories...")
    for dept in departments:
        path = f"/velum/{dept}/layer3"
        if os.path.isdir(path):
            print(f"[phase2]   -> Encrypting {path}")
            encrypt_directory(path, gpg_recipient)

    print("\n[phase2] Phase 2 complete.")


if __name__ == "__main__":
    main()
