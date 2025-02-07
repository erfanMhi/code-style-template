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

echo "Startup script finished." # Add a final message
