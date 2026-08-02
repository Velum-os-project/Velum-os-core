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
# --- Velum OS - LUKS Automated Disk Encryption (libcryptsetup) ---

import ctypes
import ctypes.util
import sys
import os

# Load libcryptsetup directly
_lib = ctypes.CDLL(ctypes.util.find_library("cryptsetup"))

VELUM_LAYERS = {
    "layer3": "/dev/sdb",
    "layer4": "/dev/sdc",
}

MAPPER_PREFIX = "velum"


def _get_device_handle(device: str):
    cd = ctypes.c_void_p()
    ret = _lib.crypt_init(ctypes.byref(cd), device.encode())
    if ret < 0:
        print(f"[luks] Failed to init device: {device}")
        sys.exit(1)
    return cd


def is_luks(device: str) -> bool:
    cd = _get_device_handle(device)
    ret = _lib.crypt_load(cd, b"LUKS2", None)
    _lib.crypt_free(cd)
    return ret == 0


def setup_luks(device: str, layer: str, keyfile: str) -> None:
    mapper = f"{MAPPER_PREFIX}_{layer}"

    if not is_luks(device):
        print(f"[luks] Formatting {device} as LUKS2 for {layer}...")
        cd = _get_device_handle(device)
        params = None  # use defaults
        ret = _lib.crypt_format(
            cd,
            b"LUKS2",
            b"aes",
            b"xts-plain64",
            None,
            None,
            64,
            params
        )
        if ret < 0:
            print(f"[luks] Format failed: {ret}")
            sys.exit(1)

        ret = _lib.crypt_keyslot_add_by_keyfile(
            cd, -1,
            None, 0,
            keyfile.encode(), os.path.getsize(keyfile)
        )
        if ret < 0:
            print(f"[luks] Failed to add keyfile: {ret}")
            sys.exit(1)

        _lib.crypt_free(cd)
        print(f"[luks] {device} formatted successfully.")

    print(f"[luks] Opening {device} as /dev/mapper/{mapper}...")
    cd = _get_device_handle(device)
    _lib.crypt_load(cd, b"LUKS2", None)
    ret = _lib.crypt_activate_by_keyfile(
        cd,
        mapper.encode(),
        -1,
        keyfile.encode(),
        os.path.getsize(keyfile),
        0
    )
    if ret < 0:
        print(f"[luks] Failed to open device: {ret}")
        sys.exit(1)
    _lib.crypt_free(cd)
    print(f"[luks] {layer} available at /dev/mapper/{mapper}")


def close_luks(layer: str) -> None:
    mapper = f"{MAPPER_PREFIX}_{layer}"
    cd = ctypes.c_void_p()
    _lib.crypt_init_by_name(ctypes.byref(cd), mapper.encode())
    ret = _lib.crypt_deactivate(cd, mapper.encode())
    _lib.crypt_free(cd)
    if ret < 0:
        print(f"[luks] Failed to close {mapper}")
        sys.exit(1)
    print(f"[luks] {layer} closed.")


def status_luks(layer: str) -> None:
    mapper = f"{MAPPER_PREFIX}_{layer}"
    cd = ctypes.c_void_p()
    ret = _lib.crypt_init_by_name(ctypes.byref(cd), mapper.encode())
    if ret < 0:
        print(f"[luks] {layer} is not active.")
    else:
        print(f"[luks] {layer} is active at /dev/mapper/{mapper}")
    _lib.crypt_free(cd)


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