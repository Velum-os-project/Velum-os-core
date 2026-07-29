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

# --------- Velum OS - Users and Groups Creator -----------
create_users() {
    echo "[users] Creting group and permissions..."

    for dept in  "${DEPARTMENTS[@]}"; do
        for layer in "${LAYERS[@]}"; do
            local group="velum_${dept}_layer${layer}"
            local path="/velum/$dept/layer$layer"

            # Create group if it doesn´t exist
            if ! getent group "$group" > /dev/null 2>&1; then
                groupadd "$group"
                echo "[users] Created group: $group"
            else
                echo "[users] Group already exixts: $group"
            fi

            #Assign group ownership to folder
            chown "root:$group" "$path"

            # Layer 1: read/write for group, nothing for others
            # Layer 2: same but stricter
            # Layer 3 and 4: group owner only, no others
            if [ "$layer" -le 2 ]; then
                chmod 770 "$path"
            else
                chmod 700 "$path"
            fi

            echo "[users] Permissions set for: $path"
        done
    done

    echo "[users] Groups and permissions complete."
}