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

# --- Velum OS - LUKS Automated Disk Encryption ---

import subprocess
import sys
import os

VELUM_LAYERS = {
    "layer3": "/dev/sdb",  # Device for Layer 3 (adjust per deployment)
    "layer4": "/dev/sdc",  # Device for Layer 4 (adjust per deployment)
}

MAPPER_PREFIX = "velum"


def run(cmd: list, check=True) -> subprocess.CompletedProcess:
    """Run a shell command safely."""
    return subprocess.run(cmd, check=check, capture_output=True, text=True)


def is_luks(device: str) -> bool:
    """Check if a device is already LUKS formatted."""
    result = run(["cryptsetup", "isLuks", device], check=False)
    return result.returncode == 0


def setup_luks(device: str, layer: str, keyfile: str) -> None:
    """Format and open a LUKS device for a given layer."""
    mapper = f"{MAPPER_PREFIX}_{layer}"

    if is_luks(device):
        print(f"[luks] {device} is already LUKS formatted.")
    else:
        print(f"[luks] Formatting {device} as LUKS for {layer}...")
        run([
            "cryptsetup", "luksFormat",
            "--type", "luks2",
            "--key-file", keyfile,
            "--batch-mode",
            device
        ])
        print(f"[luks] {device} formatted successfully.")

    print(f"[luks] Opening {device} as /dev/mapper/{mapper}...")
    run([
        "cryptsetup", "open",
        "--key-file", keyfile,
        device, mapper
    ])
    print(f"[luks] {layer} is now available at /dev/mapper/{mapper}")


def close_luks(layer: str) -> None:
    """Close a LUKS device."""
    mapper = f"{MAPPER_PREFIX}_{layer}"
    print(f"[luks] Closing /dev/mapper/{mapper}...")
    run(["cryptsetup", "close", mapper])
    print(f"[luks] {layer} closed.")


def status_luks(layer: str) -> None:
    """Show status of a LUKS device."""
    mapper = f"{MAPPER_PREFIX}_{layer}"
    result = run(["cryptsetup", "status", mapper], check=False)
    print(result.stdout if result.stdout else f"[luks] {layer} is not active.")


if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: luks.py [setup|close|status] [layer3|layer4] [keyfile]")
        sys.exit(1)

    action = sys.argv[1]
    layer  = sys.argv[2]

    if layer not in VELUM_LAYERS:
        print(f"[luks] Unknown layer: {layer}")
        sys.exit(1)

    device = VELUM_LAYERS[layer]

    if action == "setup":
        if len(sys.argv) < 4:
            print("[luks] keyfile required for setup.")
            sys.exit(1)
        setup_luks(device, layer, sys.argv[3])
    elif action == "close":
        close_luks(layer)
    elif action == "status":
        status_luks(layer)
    else:
        print(f"[luks] Unknown action: {action}")
        sys.exit(1)