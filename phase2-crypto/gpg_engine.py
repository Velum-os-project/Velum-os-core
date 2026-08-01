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

# --- Velum OS - GPG Engine for Layer 3 at-rest encryption ---

import subprocess
import os
import sys


def run(cmd: list, check=True) -> subprocess.CompletedProcess:
    """Run a shell command safely."""
    return subprocess.run(cmd, check=check, capture_output=True, text=True)


def encrypt_file(filepath: str, recipient: str) -> None:
    """Encrypt a file with GPG asymmetric encryption."""
    if not os.path.exists(filepath):
        print(f"[gpg] File not found: {filepath}")
        sys.exit(1)

    output = filepath + ".gpg"
    print(f"[gpg] Encrypting {filepath} for {recipient}...")
    run([
        "gpg", "--batch", "--yes",
        "--trust-model", "always",
        "--recipient", recipient,
        "--output", output,
        "--encrypt", filepath
    ])
    os.remove(filepath)
    print(f"[gpg] Encrypted: {output} (original deleted)")


def decrypt_file(filepath: str, output_path: str) -> None:
    """Decrypt a GPG encrypted file."""
    if not os.path.exists(filepath):
        print(f"[gpg] File not found: {filepath}")
        sys.exit(1)

    print(f"[gpg] Decrypting {filepath}...")
    run([
        "gpg", "--batch", "--yes",
        "--output", output_path,
        "--decrypt", filepath
    ])
    print(f"[gpg] Decrypted to: {output_path}")


def encrypt_directory(dirpath: str, recipient: str) -> None:
    """Encrypt all files in a directory recursively."""
    if not os.path.isdir(dirpath):
        print(f"[gpg] Directory not found: {dirpath}")
        sys.exit(1)

    print(f"[gpg] Encrypting all files in {dirpath}...")
    for root, dirs, files in os.walk(dirpath):
        for file in files:
            if not file.endswith(".gpg"):
                encrypt_file(os.path.join(root, file), recipient)
    print(f"[gpg] Directory encryption complete.")


def decrypt_directory(dirpath: str) -> None:
    """Decrypt all GPG files in a directory recursively."""
    if not os.path.isdir(dirpath):
        print(f"[gpg] Directory not found: {dirpath}")
        sys.exit(1)

    print(f"[gpg] Decrypting all files in {dirpath}...")
    for root, dirs, files in os.walk(dirpath):
        for file in files:
            if file.endswith(".gpg"):
                filepath = os.path.join(root, file)
                output = filepath[:-4]
                decrypt_file(filepath, output)
    print(f"[gpg] Directory decryption complete.")


if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: gpg_engine.py [encrypt|decrypt] [file|directory] [recipient if encrypting]")
        sys.exit(1)

    action   = sys.argv[1]
    target   = sys.argv[2]

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