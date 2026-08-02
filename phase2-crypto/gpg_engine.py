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
# --- Velum OS - GPG Engine for Layer 3 (libgpgme) ---

import ctypes
import ctypes.util
import sys
import os

# Load libgpgme directly
_lib = ctypes.CDLL(ctypes.util.find_library("gpgme"))

# GPGME protocol
GPGME_PROTOCOL_OpenPGP = 0


def _init_gpgme():
    _lib.gpgme_check_version(None)
    ctx = ctypes.c_void_p()
    ret = _lib.gpgme_new(ctypes.byref(ctx))
    if ret != 0:
        print("[gpg] Failed to initialize GPGME context.")
        sys.exit(1)
    _lib.gpgme_set_protocol(ctx, GPGME_PROTOCOL_OpenPGP)
    _lib.gpgme_set_armor(ctx, 0)
    return ctx


def encrypt_file(filepath: str, recipient: str) -> None:
    if not os.path.exists(filepath):
        print(f"[gpg] File not found: {filepath}")
        sys.exit(1)

    ctx = _init_gpgme()
    output = filepath + ".gpg"

    print(f"[gpg] Encrypting {filepath} for {recipient}...")

    # Get recipient key
    key = ctypes.c_void_p()
    ret = _lib.gpgme_get_key(ctx, recipient.encode(), ctypes.byref(key), 0)
    if ret != 0:
        print(f"[gpg] Recipient key not found: {recipient}")
        sys.exit(1)

    # Create key array (NULL terminated)
    keys = (ctypes.c_void_p * 2)(key, None)

    # Create data objects
    plain = ctypes.c_void_p()
    cipher = ctypes.c_void_p()
    _lib.gpgme_data_new_from_file(ctypes.byref(plain), filepath.encode(), 1)
    _lib.gpgme_data_new(ctypes.byref(cipher))

    ret = _lib.gpgme_op_encrypt(ctx, keys, 1, plain, cipher)
    if ret != 0:
        print(f"[gpg] Encryption failed: {ret}")
        sys.exit(1)

    # Write output
    _lib.gpgme_data_seek(cipher, 0, 0)
    buf = ctypes.create_string_buffer(4096)
    with open(output, "wb") as f:
        while True:
            n = _lib.gpgme_data_read(cipher, buf, 4096)
            if n <= 0:
                break
            f.write(buf.raw[:n])

    _lib.gpgme_data_release(plain)
    _lib.gpgme_data_release(cipher)
    _lib.gpgme_key_unref(key)
    _lib.gpgme_release(ctx)

    os.remove(filepath)
    print(f"[gpg] Encrypted: {output} (original deleted)")


def decrypt_file(filepath: str, output_path: str) -> None:
    if not os.path.exists(filepath):
        print(f"[gpg] File not found: {filepath}")
        sys.exit(1)

    ctx = _init_gpgme()
    print(f"[gpg] Decrypting {filepath}...")

    cipher = ctypes.c_void_p()
    plain  = ctypes.c_void_p()
    _lib.gpgme_data_new_from_file(ctypes.byref(cipher), filepath.encode(), 1)
    _lib.gpgme_data_new(ctypes.byref(plain))

    ret = _lib.gpgme_op_decrypt(ctx, cipher, plain)
    if ret != 0:
        print(f"[gpg] Decryption failed: {ret}")
        sys.exit(1)

    _lib.gpgme_data_seek(plain, 0, 0)
    buf = ctypes.create_string_buffer(4096)
    with open(output_path, "wb") as f:
        while True:
            n = _lib.gpgme_data_read(plain, buf, 4096)
            if n <= 0:
                break
            f.write(buf.raw[:n])

    _lib.gpgme_data_release(cipher)
    _lib.gpgme_data_release(plain)
    _lib.gpgme_release(ctx)
    print(f"[gpg] Decrypted to: {output_path}")


def encrypt_directory(dirpath: str, recipient: str) -> None:
    if not os.path.isdir(dirpath):
        print(f"[gpg] Directory not found: {dirpath}")
        sys.exit(1)
    print(f"[gpg] Encrypting all files in {dirpath}...")
    for root, dirs, files in os.walk(dirpath):
        for file in files:
            if not file.endswith(".gpg"):
                encrypt_file(os.path.join(root, file), recipient)
    print("[gpg] Directory encryption complete.")


def decrypt_directory(dirpath: str) -> None:
    if not os.path.isdir(dirpath):
        print(f"[gpg] Directory not found: {dirpath}")
        sys.exit(1)
    print(f"[gpg] Decrypting all files in {dirpath}...")
    for root, dirs, files in os.walk(dirpath):
        for file in files:
            if file.endswith(".gpg"):
                filepath = os.path.join(root, file)
                decrypt_file(filepath, filepath[:-4])
    print("[gpg] Directory decryption complete.")


if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: gpg_engine.py [encrypt|decrypt] [file|directory] [recipient if encrypting]")
        sys.exit(1)

    action = sys.argv[1]
    target = sys.argv[2]

    if action == "encrypt":
        if len(sys.argv) < 4:
            print("[gpg] recipient required for encryption.")
            sys.exit(1)
        recipient = sys.argv[3]
        if os.path.isdir(target):
            encrypt_directory(target, recipient)
        else:
            encrypt_file(target, recipient)
    elif action == "decrypt":
        if os.path.isdir(target):
            decrypt_directory(target)
        else:
            output = target[:-4] if target.endswith(".gpg") else target + ".dec"
            decrypt_file(target, output)
    else:
        print(f"[gpg] Unknown action: {action}")
        sys.exit(1)