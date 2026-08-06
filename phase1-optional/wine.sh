#!/bin/bash
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

set -e
set -u
set -o pipefail

# --- Velum OS - Optional Wine compatibility layer ---
# Installed per department, only on Layer 1 and 2 (never Layer 3/4).

source "$(dirname "$0")/../phase1-core/config/departments.conf"

install_wine() {
    echo "[wine] Installing Wine..."
    dpkg --add-architecture i386
    apt update
    apt install -y wine wine32 wine64 winetricks
    echo "[wine] Wine installed."
}

configure_wine_per_department() {
    echo "[wine] Configuring Wine per department and layer..."

    for dept in "${DEPARTMENTS[@]}"; do
        for layer in "${LAYERS[@]}"; do
            # Only Layer 1 and 2 get Wine access — Layer 3/4 stay untouched
            if [ "$layer" -ge 3 ]; then
                continue
            fi

            local group="velum_${dept}_layer${layer}"
            local wine_prefix="/velum/$dept/layer${layer}/.wine"

            mkdir -p "$wine_prefix"
            chown "root:$group" "$wine_prefix"
            chmod 770 "$wine_prefix"

            setfacl -b "$wine_prefix"
            setfacl -m "g:$group:rwx" "$wine_prefix"
            setfacl -m "u:root:rwx" "$wine_prefix"
            setfacl -m "o::---" "$wine_prefix"

            echo "[wine] Wine prefix configured for $dept/layer$layer"
        done
    done

    echo "[wine] Wine configuration complete."
}

echo "[Velum OS] Starting optional Wine installation..."
install_wine
configure_wine_per_department
echo "[Velum OS] Wine setup complete."
