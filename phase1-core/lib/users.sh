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

# --- Velum OS - Users, Groups and ABAC Access Control ---

create_users() {
    echo "[users] Creating groups and ABAC permissions..."

    for dept in "${DEPARTMENTS[@]}"; do
        for layer in "${LAYERS[@]}"; do
            local group="velum_${dept}_layer${layer}"
            local path="/velum/$dept/layer$layer"

            # Create group if it doesn't exist
            if ! getent group "$group" > /dev/null 2>&1; then
                groupadd "$group"
                echo "[users] Created group: $group"
            else
                echo "[users] Group already exists: $group"
            fi

            # Assign ownership
            chown "root:$group" "$path"

            # Remove all default permissions first
            chmod 000 "$path"

            # ABAC: grant access only if BOTH attributes match (dept + layer)
            # Any other group gets explicit deny via ACL
            setfacl -b "$path"
            setfacl -m "g:$group:rwx" "$path"
            setfacl -m "u:root:rwx" "$path"

            # Layer 3 and 4: no execute for group, read/write only via GPG
            if [ "$layer" -ge 3 ]; then
                setfacl -m "g:$group:rw-" "$path"
            fi

            # Explicit deny for everyone else (ABAC: if attributes don't match, deny)
            setfacl -m "o::---" "$path"

            echo "[users] ABAC permissions set for: $path ($group)"
        done
    done

    echo "[users] ABAC setup complete."
}