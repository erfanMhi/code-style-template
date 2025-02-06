############################################################
# 0. Provider & required APIs
############################################################
provider "google" {
  project = var.project_id
  region  = var.region
}

# Enable the APIs we need (idempotent, no‑op if already enabled)
resource "google_project_service" "services" {
  for_each = toset([
    "compute.googleapis.com",
    "iam.googleapis.com",
    "containeranalysis.googleapis.com" # pulled in by DL images
  ])
  service = each.key
}

############################################################
# 1. Networking ‑ private VM, public egress
############################################################
# 1.1 Dedicated VPC keeps GPU quotas & firewall separate
resource "google_compute_network" "gpu_vpc" {
  name                    = "gpu-vpc"
  auto_create_subnetworks = false
}

# 1.2 Private subnet with **Private Google Access** for GCS/GCR etc.
resource "google_compute_subnetwork" "gpu_subnet" {
  name                     = "gpu-subnet"
  ip_cidr_range            = var.subnet_cidr
  region                   = var.region
  network                  = google_compute_network.gpu_vpc.id
  private_ip_google_access = true # ← lets gsutil reach the driver bucket
}

# 1.3 Cloud NAT so the VM can reach the wider Internet (PyPI, apt, …)
resource "google_compute_router" "gpu_router" {
  name    = "gpu-router"
  network = google_compute_network.gpu_vpc.id
  region  = var.region
}

resource "google_compute_router_nat" "gpu_nat" {
  name                               = "gpu-nat"
  router                             = google_compute_router.gpu_router.name
  region                             = var.region
  nat_ip_allocate_option             = "AUTO_ONLY"
  source_subnetwork_ip_ranges_to_nat = "ALL_SUBNETWORKS_ALL_IP_RANGES"
}

############################################################
# 2. Least‑privilege service account for the VM
############################################################
resource "google_service_account" "vm_sa" {
  account_id   = "gpu-vm-sa"
  display_name = "Service account for GPU VM with GCS read access"
}

# Grant GCS read access to the service account
resource "google_project_iam_member" "vm_sa_storage_viewer" {
  project = var.project_id
  role    = "roles/storage.objectViewer"
  member  = "serviceAccount:${google_service_account.vm_sa.email}"
}

############################################################
# 3. Firewall: SSH/IAP only
############################################################
resource "google_compute_firewall" "allow_ssh_via_iap" {
  name    = "allow-ssh-via-iap"
  network = google_compute_network.gpu_vpc.id

  allow {
    protocol = "tcp"
    ports    = ["22"]
  }

  source_ranges = ["35.235.240.0/20"] # IAP
  target_tags   = ["gpu-vm"]
  description   = "Allow SSH from Google IAP only"
}

############################################################
# 4. GPU instance (no external IP)
############################################################
locals {
  zone         = "${var.region}-a"
  gpu_type     = "nvidia-tesla-a100"
  gpu_count    = tonumber(var.gpu_count)
  machine_type = "a2-highgpu-${local.gpu_count}g" # e.g. a2‑highgpu‑1g / 2g / 4g / 8g
}

resource "google_compute_instance" "a100_vm" {
  name         = "a100-${local.gpu_count}g"
  zone         = local.zone
  machine_type = local.machine_type

  boot_disk {
    initialize_params {
      image = var.vm_image
      size  = var.boot_disk_size
    }
  }

  network_interface {
    subnetwork = google_compute_subnetwork.gpu_subnet.id
    # **NO** access_config ⇒ no external IP (policy‑compliant)
  }

  # Attach GPUs
  guest_accelerator {
    type  = local.gpu_type
    count = local.gpu_count
  }

  scheduling {
    on_host_maintenance = "TERMINATE"
    automatic_restart   = false
  }

  service_account {
    email  = google_service_account.vm_sa.email
    scopes = ["https://www.googleapis.com/auth/cloud-platform"]
  }

  metadata = {
    enable-oslogin = "TRUE"
    startup-script = <<-EOT
      #!/usr/bin/env bash
      set -euxo pipefail

      # Ensure we can reach GCS before the NVIDIA installer runs
      until gsutil ls gs://nvidia-drivers-us-public/ >/dev/null 2>&1; do
        echo "Waiting for Private Google Access / NAT ..."
        sleep 5
      done

      # Trigger the interactive installer non‑interactively
      /opt/deeplearning/install-driver.sh --quiet
    EOT
  }

  tags = ["gpu-vm"]

  depends_on = [
    google_compute_router_nat.gpu_nat, # make sure NAT exists first
    google_project_service.services    # APIs enabled
  ]
}
