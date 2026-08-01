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

# --- Velum OS - Velum Trust Authority (VTA) ---

import subprocess
import os
import sys
from datetime import datetime

VTA_ROOT     = "/velum/layer4/vta"
VTA_ROOT_KEY = f"{VTA_ROOT}/root/vta-root.key"
VTA_ROOT_CRT = f"{VTA_ROOT}/root/vta-root.crt"
VTA_INT_DIR  = f"{VTA_ROOT}/intermediate"
VTA_CRL_DIR  = f"{VTA_ROOT}/crl"


def run(cmd: list, check=True) -> subprocess.CompletedProcess:
    """Run a shell command safely."""
    return subprocess.run(cmd, check=check, capture_output=True, text=True)


def init_directories() -> None:
    """Create VTA directory structure in Layer 4."""
    for path in [VTA_ROOT, f"{VTA_ROOT}/root", VTA_INT_DIR, VTA_CRL_DIR]:
        os.makedirs(path, exist_ok=True)
    print("[vta] Directory structure initialized.")


def generate_root_ca() -> None:
    """Generate the VTA root CA. Stored in Layer 4."""
    if os.path.exists(VTA_ROOT_CRT):
        print("[vta] Root CA already exists. Skipping.")
        return

    print("[vta] Generating root CA key...")
    run([
        "openssl", "genrsa",
        "-aes256",
        "-out", VTA_ROOT_KEY,
        "4096"
    ])

    print("[vta] Generating root CA certificate (valid 20 years)...")
    run([
        "openssl", "req", "-x509", "-new",
        "-key", VTA_ROOT_KEY,
        "-sha512",
        "-days", "7300",
        "-out", VTA_ROOT_CRT,
        "-subj", "/CN=Velum Trust Authority/O=Velum OS/OU=Root CA"
    ])
    print("[vta] Root CA generated and stored in Layer 4.")


def generate_intermediate_ca(department: str) -> None:
    """Generate an intermediate CA for a department."""
    int_dir  = f"{VTA_INT_DIR}/{department}"
    int_key  = f"{int_dir}/vta-{department}.key"
    int_csr  = f"{int_dir}/vta-{department}.csr"
    int_crt  = f"{int_dir}/vta-{department}.crt"

    os.makedirs(int_dir, exist_ok=True)

    if os.path.exists(int_crt):
        print(f"[vta] Intermediate CA for {department} already exists. Skipping.")
        return

    print(f"[vta] Generating intermediate CA for {department}...")
    run(["openssl", "genrsa", "-aes256", "-out", int_key, "4096"])

    run([
        "openssl", "req", "-new",
        "-key", int_key,
        "-out", int_csr,
        "-subj", f"/CN=VTA-{department.upper()}/O=Velum OS/OU={department}"
    ])

    run([
        "openssl", "x509", "-req",
        "-in", int_csr,
        "-CA", VTA_ROOT_CRT,
        "-CAkey", VTA_ROOT_KEY,
        "-CAcreateserial",
        "-out", int_crt,
        "-days", "1825",
        "-sha512"
    ])
    print(f"[vta] Intermediate CA for {department} generated.")


def issue_certificate(department: str, layer: str, machine_name: str) -> None:
    """Issue a certificate for a machine with Velum OS custom attributes."""
    int_dir  = f"{VTA_INT_DIR}/{department}"
    int_key  = f"{int_dir}/vta-{department}.key"
    int_crt  = f"{int_dir}/vta-{department}.crt"
    cert_dir = f"{int_dir}/certs"
    machine_key = f"{cert_dir}/{machine_name}.key"
    machine_csr = f"{cert_dir}/{machine_name}.csr"
    machine_crt = f"{cert_dir}/{machine_name}.crt"
    ext_file    = f"{cert_dir}/{machine_name}.ext"

    os.makedirs(cert_dir, exist_ok=True)

    print(f"[vta] Issuing certificate for {machine_name} ({department} / {layer})...")

    run(["openssl", "genrsa", "-out", machine_key, "4096"])
    run([
        "openssl", "req", "-new",
        "-key", machine_key,
        "-out", machine_csr,
        "-subj", f"/CN={machine_name}/O=Velum OS/OU={department}"
    ])

    # Velum OS custom X.509 extensions
    with open(ext_file, "w") as f:
        f.write(f"""[velum_ext]
subjectAltName=DNS:{machine_name}
1.3.6.1.4.1.99999.1=ASN1:UTF8String:{department}
1.3.6.1.4.1.99999.2=ASN1:UTF8String:{layer}
""")

    run([
        "openssl", "x509", "-req",
        "-in", machine_csr,
        "-CA", int_crt,
        "-CAkey", int_key,
        "-CAcreateserial",
        "-out", machine_crt,
        "-days", "365",
        "-sha512",
        "-extfile", ext_file,
        "-extensions", "velum_ext"
    ])
    print(f"[vta] Certificate issued: {machine_crt}")


def revoke_certificate(department: str, machine_name: str) -> None:
    """Revoke a certificate and update the CRL."""
    int_dir     = f"{VTA_INT_DIR}/{department}"
    int_key     = f"{int_dir}/vta-{department}.key"
    int_crt     = f"{int_dir}/vta-{department}.crt"
    machine_crt = f"{int_dir}/certs/{machine_name}.crt"
    crl_file    = f"{VTA_CRL_DIR}/{department}.crl"

    print(f"[vta] Revoking certificate for {machine_name}...")
    run([
        "openssl", "ca",
        "-revoke", machine_crt,
        "-keyfile", int_key,
        "-cert", int_crt
    ])

    run([
        "openssl", "ca",
        "-gencrl",
        "-keyfile", int_key,
        "-cert", int_crt,
        "-out", crl_file
    ])
    print(f"[vta] Certificate revoked. CRL updated: {crl_file}")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: vta.py [init|root|intermediate|issue|revoke] [args]")
        sys.exit(1)

    action = sys.argv[1]

    if action == "init":
        init_directories()
    elif action == "root":
        generate_root_ca()
    elif action == "intermediate":
        generate_intermediate_ca(sys.argv[2])
    elif action == "issue":
        issue_certificate(sys.argv[2], sys.argv[3], sys.argv[4])
    elif action == "revoke":
        revoke_certificate(sys.argv[2], sys.argv[3])
    else:
        print(f"[vta] Unknown action: {action}")
        sys.exit(1)