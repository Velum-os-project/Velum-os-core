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
# --- Velum OS - Velum Trust Authority (libssl/libcrypto) ---

import ctypes
import ctypes.util
import sys
import os

# Load libssl and libcrypto directly
_ssl    = ctypes.CDLL(ctypes.util.find_library("ssl"))
_crypto = ctypes.CDLL(ctypes.util.find_library("crypto"))

VTA_ROOT     = "/velum/layer4/vta"
VTA_ROOT_KEY = f"{VTA_ROOT}/root/vta-root.key"
VTA_ROOT_CRT = f"{VTA_ROOT}/root/vta-root.crt"
VTA_INT_DIR  = f"{VTA_ROOT}/intermediate"
VTA_CRL_DIR  = f"{VTA_ROOT}/crl"

# RSA key size
RSA_BITS = 4096


def init_directories() -> None:
    for path in [VTA_ROOT, f"{VTA_ROOT}/root", VTA_INT_DIR, VTA_CRL_DIR]:
        os.makedirs(path, exist_ok=True)
    print("[vta] Directory structure initialized.")


def _generate_rsa_key(path: str) -> None:
    """Generate RSA 4096 key using libcrypto and write to PEM file."""
    ctx = _crypto.EVP_PKEY_CTX_new_id(6, None)  # 6 = EVP_PKEY_RSA
    _crypto.EVP_PKEY_keygen_init(ctx)
    _crypto.EVP_PKEY_CTX_set_rsa_keygen_bits(ctx, RSA_BITS)

    pkey = ctypes.c_void_p()
    _crypto.EVP_PKEY_keygen(ctx, ctypes.byref(pkey))
    _crypto.EVP_PKEY_CTX_free(ctx)

    bio = _crypto.BIO_new_file(path.encode(), b"w")
    _crypto.PEM_write_bio_PrivateKey(bio, pkey, None, None, 0, None, None)
    _crypto.BIO_free(bio)
    _crypto.EVP_PKEY_free(pkey)
    print(f"[vta] Key written to {path}")


def _read_pem_key(path: str) -> ctypes.c_void_p:
    bio = _crypto.BIO_new_file(path.encode(), b"r")
    pkey = _crypto.PEM_read_bio_PrivateKey(bio, None, None, None)
    _crypto.BIO_free(bio)
    return pkey


def _read_pem_cert(path: str) -> ctypes.c_void_p:
    bio = _crypto.BIO_new_file(path.encode(), b"r")
    cert = _crypto.PEM_read_bio_X509(bio, None, None, None)
    _crypto.BIO_free(bio)
    return cert


def _write_pem_cert(cert: ctypes.c_void_p, path: str) -> None:
    bio = _crypto.BIO_new_file(path.encode(), b"w")
    _crypto.PEM_write_bio_X509(bio, cert)
    _crypto.BIO_free(bio)


def _create_cert(subject_cn: str, subject_ou: str, pkey, issuer_cert, issuer_key, days: int, extensions: dict = None) -> ctypes.c_void_p:
    """Create and sign an X509 certificate."""
    cert = _crypto.X509_new()

    # Set version to X509v3
    _crypto.X509_set_version(cert, 2)

    # Set serial number
    serial = _crypto.ASN1_INTEGER_new()
    _crypto.ASN1_INTEGER_set(serial, os.getpid())
    _crypto.X509_set_serialNumber(cert, serial)

    # Set validity
    _crypto.X509_gmtime_adj(_crypto.X509_get_notBefore(cert), 0)
    _crypto.X509_gmtime_adj(_crypto.X509_get_notAfter(cert), days * 86400)

    # Set subject
    name = _crypto.X509_get_subject_name(cert)
    _crypto.X509_NAME_add_entry_by_txt(name, b"CN", 0x1000, subject_cn.encode(), -1, -1, 0)
    _crypto.X509_NAME_add_entry_by_txt(name, b"O",  0x1000, b"Velum OS", -1, -1, 0)
    _crypto.X509_NAME_add_entry_by_txt(name, b"OU", 0x1000, subject_ou.encode(), -1, -1, 0)

    # Set issuer
    if issuer_cert:
        issuer_name = _crypto.X509_get_subject_name(issuer_cert)
        _crypto.X509_set_issuer_name(cert, issuer_name)
    else:
        _crypto.X509_set_issuer_name(cert, name)

    # Set public key
    _crypto.X509_set_pubkey(cert, pkey)

    # Add Velum OS custom extensions if provided
    if extensions:
        for oid, value in extensions.items():
            ex = _crypto.X509V3_EXT_conf_nid(None, None, oid.encode(), value.encode())
            if ex:
                _crypto.X509_add_ext(cert, ex, -1)
                _crypto.X509_EXTENSION_free(ex)

    # Sign with issuer key (or self if root)
    sign_key = issuer_key if issuer_key else pkey
    _crypto.X509_sign(cert, sign_key, _crypto.EVP_sha512())

    return cert


def generate_root_ca() -> None:
    if os.path.exists(VTA_ROOT_CRT):
        print("[vta] Root CA already exists. Skipping.")
        return

    print("[vta] Generating root CA key...")
    _generate_rsa_key(VTA_ROOT_KEY)

    print("[vta] Generating root CA certificate (valid 20 years)...")
    pkey = _read_pem_key(VTA_ROOT_KEY)
    cert = _create_cert(
        subject_cn="Velum Trust Authority",
        subject_ou="Root CA",
        pkey=pkey,
        issuer_cert=None,
        issuer_key=None,
        days=7300
    )
    _write_pem_cert(cert, VTA_ROOT_CRT)
    _crypto.X509_free(cert)
    _crypto.EVP_PKEY_free(pkey)
    print("[vta] Root CA generated and stored in Layer 4.")


def generate_intermediate_ca(department: str) -> None:
    int_dir = f"{VTA_INT_DIR}/{department}"
    int_key = f"{int_dir}/vta-{department}.key"
    int_crt = f"{int_dir}/vta-{department}.crt"

    os.makedirs(int_dir, exist_ok=True)

    if os.path.exists(int_crt):
        print(f"[vta] Intermediate CA for {department} already exists. Skipping.")
        return

    print(f"[vta] Generating intermediate CA for {department}...")
    _generate_rsa_key(int_key)

    pkey        = _read_pem_key(int_key)
    root_cert   = _read_pem_cert(VTA_ROOT_CRT)
    root_key    = _read_pem_key(VTA_ROOT_KEY)

    cert = _create_cert(
        subject_cn=f"VTA-{department.upper()}",
        subject_ou=department,
        pkey=pkey,
        issuer_cert=root_cert,
        issuer_key=root_key,
        days=1825
    )
    _write_pem_cert(cert, int_crt)
    _crypto.X509_free(cert)
    _crypto.X509_free(root_cert)
    _crypto.EVP_PKEY_free(pkey)
    _crypto.EVP_PKEY_free(root_key)
    print(f"[vta] Intermediate CA for {department} generated.")


def issue_certificate(department: str, layer: str, machine_name: str) -> None:
    int_dir     = f"{VTA_INT_DIR}/{department}"
    int_key     = f"{int_dir}/vta-{department}.key"
    int_crt     = f"{int_dir}/vta-{department}.crt"
    cert_dir    = f"{int_dir}/certs"
    machine_key = f"{cert_dir}/{machine_name}.key"
    machine_crt = f"{cert_dir}/{machine_name}.crt"

    os.makedirs(cert_dir, exist_ok=True)

    print(f"[vta] Issuing certificate for {machine_name} ({department} / {layer})...")
    _generate_rsa_key(machine_key)

    pkey     = _read_pem_key(machine_key)
    int_cert = _read_pem_cert(int_crt)
    int_pkey = _read_pem_key(int_key)

    # Velum OS custom X.509 attributes
    extensions = {
        "subjectAltName": f"DNS:{machine_name}",
    }

    cert = _create_cert(
        subject_cn=machine_name,
        subject_ou=department,
        pkey=pkey,
        issuer_cert=int_cert,
        issuer_key=int_pkey,
        days=365,
        extensions=extensions
    )
    _write_pem_cert(cert, machine_crt)
    _crypto.X509_free(cert)
    _crypto.X509_free(int_cert)
    _crypto.EVP_PKEY_free(pkey)
    _crypto.EVP_PKEY_free(int_pkey)
    print(f"[vta] Certificate issued: {machine_crt}")


def revoke_certificate(department: str, machine_name: str) -> None:
    int_dir     = f"{VTA_INT_DIR}/{department}"
    int_key     = f"{int_dir}/vta-{department}.key"
    int_crt     = f"{int_dir}/vta-{department}.crt"
    machine_crt = f"{int_dir}/certs/{machine_name}.crt"
    crl_path    = f"{VTA_CRL_DIR}/{department}.crl"

    print(f"[vta] Revoking certificate for {machine_name}...")

    crl  = _crypto.X509_CRL_new()
    cert = _read_pem_cert(machine_crt)
    pkey = _read_pem_key(int_key)
    ca   = _read_pem_cert(int_crt)

    serial   = _crypto.X509_get_serialNumber(cert)
    revoked  = _crypto.X509_REVOKED_new()
    _crypto.X509_REVOKED_set_serialNumber(revoked, serial)
    _crypto.X509_CRL_add0_revoked(crl, revoked)
    _crypto.X509_CRL_set_issuer_name(crl, _crypto.X509_get_subject_name(ca))
    _crypto.X509_CRL_sign(crl, pkey, _crypto.EVP_sha512())

    bio = _crypto.BIO_new_file(crl_path.encode(), b"w")
    _crypto.PEM_write_bio_X509_CRL(bio, crl)
    _crypto.BIO_free(bio)

    _crypto.X509_CRL_free(crl)
    _crypto.X509_free(cert)
    _crypto.X509_free(ca)
    _crypto.EVP_PKEY_free(pkey)
    print(f"[vta] Certificate revoked. CRL updated: {crl_path}")


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