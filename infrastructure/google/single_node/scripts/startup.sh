#!/usr/bin/env bash
set -euxo pipefail

# Ensure we can reach GCS before the NVIDIA installer runs
echo "Waiting for network connectivity to GCS..."
until gsutil ls gs://nvidia-drivers-us-public/ >/dev/null 2>&1; do
  echo "Still waiting for Private Google Access / NAT ..."
  sleep 5
done
echo "Network connectivity established."

# Trigger the interactive installer non‑interactively
echo "Attempting to install NVIDIA drivers..."
if /opt/deeplearning/install-driver.sh --quiet; then
  echo "NVIDIA driver installation completed successfully."
else
  INSTALL_EXIT_CODE=$?
  echo "ERROR: NVIDIA driver installation failed. Exit code: ${INSTALL_EXIT_CODE}" >&2
  # The script will exit here anyway due to 'set -e', but this log message helps.
  exit ${INSTALL_EXIT_CODE} # Explicitly exit with the failure code
fi

# --- Added setup for the project repository ---

echo "Installing Poetry globally..."
# Install globally (typically to /usr/local/bin, accessible by users)
pip3 install poetry

# Define target user and directory based on expected OS Login user
TARGET_USER="erfan_miahi_fronix_net" # TODO: Change this if your OS Login username format differs
HOME_DIR="/home/${TARGET_USER}"
REPO_DIR="${HOME_DIR}/test_code_generation_models"
GIT_REPO_URL="https://github.com/erfanMhi/test_code_generation_models.git"

# Note: Assuming the OS Login service creates the user and home directory before this script runs.

echo "Cloning repository ${GIT_REPO_URL} into ${REPO_DIR} as user ${TARGET_USER}..."
# Clone directly as the target user to set correct ownership
sudo -u "${TARGET_USER}" git clone "${GIT_REPO_URL}" "${REPO_DIR}"

echo "Installing project dependencies using Poetry as user ${TARGET_USER}..."
# Run poetry install as the target user within their directory
sudo -u "${TARGET_USER}" bash -c "cd ${REPO_DIR} && poetry install --no-root"

echo "Startup script finished." # Add a final message
