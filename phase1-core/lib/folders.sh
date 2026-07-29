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

# --------- Velum OS - Folder Structure Creator -----------

create_folders() {
    echo "[folders] Creating directory matrix..."

    for dept in "${DEPARTMENTS[@]}"; do
        for layer in "${LAYERS[@]}"; do
            local path="/velum/$dept/layer$layer"
            mkdir -p "$path"
            echo "[folders] Created: $path"
        done
    done

    echo "[folders Directory matrix complete.]"
}