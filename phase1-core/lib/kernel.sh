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

    echo "[kernel] Hardening rules applied."
}