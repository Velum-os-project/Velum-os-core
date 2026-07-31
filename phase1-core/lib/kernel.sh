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

#!/bin/bash
set -e
set -u

# --- Velum OS - Kernel Hardening Rules ---

apply_kernel_rules() {
    echo "[kernel] Applying hardening rules..."

    # Disable USB storage (prevents data exfiltration on Layer 3/4)
    echo "install usb-storage /bin/false" > /etc/modprobe.d/velum-usb.conf

    # Disable core dumps (prevents memory leaks of sensitive data)
    echo "* hard core 0" >> /etc/security/limits.conf

    # Restrict kernel log access to root only
    sysctl -w kernel.dmesg_restrict=1

    # Disable ICMP redirects (network hardening)
    sysctl -w net.ipv4.conf.all.accept_redirects=0
    sysctl -w net.ipv6.conf.all.accept_redirects=0

    # Make sysctl rules persistent
    cat >> /etc/sysctl.d/99-velum.conf << EOF
kernel.dmesg_restrict=1
net.ipv4.conf.all.accept_redirects=0
net.ipv6.conf.all.accept_redirects=0
EOF

    # Restrict process visibility (users only see their own processes)
    echo "proc /proc proc defaults,hidepid=2 0 0" >> /etc/fstab
    mount -o remount,hidepid=2 /proc

    # Restrict su to root only
    echo "auth required pam_wheel.so use_uid" >> /etc/pam.d/su
    groupadd -f wheel

    # Disable sudo for non-authorized users
    echo "Defaults !visiblepw" >> /etc/sudoers
    echo "%wheel ALL=(ALL) ALL" >> /etc/sudoers

    # Prevent privilege escalation via suid binaries
    find / -perm -4000 -type f 2>/dev/null | while read binary; do
        chmod u-s "$binary"
        echo "[kernel] Removed SUID from: $binary"
    done

    echo "[kernel] Hardening rules applied."
}
