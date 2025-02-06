# Google Cloud + Terraform: A100 GPU VM Quick‑Start (macOS)

This README walks you from **zero to a running Compute Engine VM with 1–8 × A100 GPUs** using Terraform. It includes two auth paths:

- **Option A – Service‑account key** (fast for personal projects, *only* if key creation is allowed)
- **Option B – Workload Identity Federation** (key‑less, org‑policy friendly & recommended by Google)

---

## 1 · Prerequisites

| Tool             | Install (macOS/Homebrew)               |
| ---------------- | -------------------------------------- |
| Google Cloud SDK | `brew install --cask google-cloud-sdk` |
| Terraform ≥ 1.7  | `brew install terraform`               |

Add `gcloud` to your `PATH` if Homebrew hasn't done so (restart your shell).

---

## 2 · Initial project & API setup

```bash
# Login and pick a project (or create a new one)
gcloud init

# Set it as default so you don't type it again
PROJECT_ID="project-id"    # <‑‑ replace with yours
gcloud config set project "$PROJECT_ID"

# Enable the APIs Terraform will need
gcloud services enable \
  compute.googleapis.com \
  iam.googleapis.com \
  serviceusage.googleapis.com
```

---

## 3 · (OPTION A) Service‑account key flow

> Skip this section if your organization blocks key creation — jump to **Option B** instead.

```bash
# 3‑1 Create a dedicated service account
gcloud iam service-accounts create terraform \
  --display-name "Terraform admin"

# 3‑2 Grant permissions (narrow to what you need in prod)
gcloud projects add-iam-policy-binding "$PROJECT_ID" \
  --member "serviceAccount:terraform@$PROJECT_ID.iam.gserviceaccount.com" \
  --role roles/owner         # or roles/compute.admin & roles/iam.serviceAccountUser

# 3‑3 Generate a key file *only* if allowed
gcloud iam service-accounts keys create ~/terraform-sa.json \
  --iam-account terraform@$PROJECT_ID.iam.gserviceaccount.com

# 3‑4 Tell SDKs (incl. Terraform) to use the key
export GOOGLE_APPLICATION_CREDENTIALS=~/terraform-sa.json   # add to ~/.zshrc
```

---

## 4 · (OPTION B) Workload Identity Federation (key‑less)

If you hit `FAILED_PRECONDITION: Key creation is not allowed`, use WIF:

```bash
# 4‑1 Create a Workload Identity Pool
gcloud iam workload-identity-pools create terraform-pool \
  --location="global" \
  --display-name="Terraform Pool"
POOL_ID=$(gcloud iam workload-identity-pools describe terraform-pool --location global --format="value(name)")

# 4‑2 Attach an OIDC provider that trusts Google user tokens
gcloud iam workload-identity-pools providers create-oidc terraform-provider \
  --location="global" \
  --workload-identity-pool="terraform-pool" \
  --display-name="Terraform OIDC Provider" \
  --issuer-uri="https://accounts.google.com" \
  --attribute-mapping="google.subject=assertion.sub"

# 4‑3 Allow your Google account to impersonate the SA
ACCOUNT_EMAIL="you@example.com"                 # <‑‑ replace
PROJECT_NUMBER=$(gcloud projects describe "$PROJECT_ID" --format="value(projectNumber)")
PRINCIPAL="principalSet://iam.googleapis.com/projects/$PROJECT_NUMBER/locations/global/workloadIdentityPools/terraform-pool/attribute.subject/$ACCOUNT_EMAIL"

gcloud iam service-accounts add-iam-policy-binding terraform@$PROJECT_ID.iam.gserviceaccount.com \
  --role="roles/iam.workloadIdentityUser" \
  --member="$PRINCIPAL"

# 4‑4 Create WIF credentials JSON for Terraform
cat > ~/terraform-wif.json <<EOF
{
  "type": "external_account",
  "audience": "//iam.googleapis.com/projects/$PROJECT_NUMBER/locations/global/workloadIdentityPools/terraform-pool/providers/terraform-provider",
  "subject_token_type": "urn:ietf:params:oauth:token-type:id_token",
  "token_url": "https://sts.googleapis.com/v1/token",
  "credential_source": {
    "file": "~/.config/gcloud/application_default_credentials.json"
  },
  "service_account_impersonation_url": "https://iamcredentials.googleapis.com/v1/projects/-/serviceAccounts/terraform@$PROJECT_ID.iam.gserviceaccount.com:generateAccessToken"
}
EOF
export GOOGLE_APPLICATION_CREDENTIALS=~/terraform-wif.json   # add to ~/.zshrc
```

---

## 5 · GPU quota check (A100)

```bash
# Shows how many A100s you can currently allocate in us‑central1
gcloud compute regions describe us-central1 | grep -i a100
```

If the quota is **0**, open **Cloud Console → IAM & Admin → Quotas** and request 1–8 A100 GPUs.

---

## 6 · Terraform module skeleton (quick reference)

```hcl
provider "google" {
  project = var.project_id
  region  = var.region
}

resource "google_compute_instance" "a100_vm" {
  name         = "a100-${var.gpu_count}g"
  zone         = "${var.region}-a"   # cheapest zone for A100
  machine_type = local.machine_type

  boot_disk {
    initialize_params {
      # Debian 11 • Python 3.10 • PyTorch 2.4 • fast.ai
      image = "projects/deeplearning-platform-release/global/images/family/pytorch-2-4-cu121"
      size  = 150
    }
  }

  network_interface {
    network       = "default"
    access_config {}
  }

  scheduling {
    on_host_maintenance = "TERMINATE"
    automatic_restart   = false
  }
}
```

---

## 7 · Apply

```bash
cd infrastructure/google/single_node  # Navigate to the directory

# Initialize Terraform and plugins
terraform init

# (Optional) Preview the changes
terraform plan -var 'project_id=$PROJECT_ID' -var 'gpu_count=1' # Adjust gpu_count if needed

# Create the resources (type 'yes' when prompted)
terraform apply -var 'project_id=$PROJECT_ID' -var 'gpu_count=1' # Adjust gpu_count if needed
```

Terraform will show the planned actions and ask for confirmation before creating the resources.

---

## 8 · Connecting to the VM

Once the `terraform apply` command completes successfully, it will output connection details.

### 8.1 · Terminal (via IAP Tunnel)

Use the `connection_command` output from Terraform. This command uses `gcloud` to securely tunnel your SSH connection through Google's Identity-Aware Proxy (IAP), so the VM doesn't need a public IP address.

```bash
# Example command (use the one from your terraform output)
gcloud compute ssh a100-1g --project YOUR_PROJECT_ID --zone us-central1-a --tunnel-through-iap
```

- Google Cloud's **OS Login** service manages access. It automatically links your Google account (`gcloud auth list`) to a user on the VM.
- It uses the **public SSH keys** associated with your Google account for authentication. Make sure you have a corresponding **private key** (like `~/.ssh/id_ed25519` or `~/.ssh/id_rsa`) on your local machine.
- Check for keys with `ls -l ~/.ssh` or `ssh-add -l`. Generate one if needed (`ssh-keygen -t ed25519`).

### 8.2 · VS Code (Remote-SSH Extension)

1.  **Install:** Get the "Remote - SSH" extension from the VS Code Marketplace.
2.  **Configure:** Add the following block to your SSH config file (`~/.ssh/config`):

    ```
    Host a100-gpu-vm # Or any alias you prefer
        HostName a100-1g # Use the VM name from terraform output
        User your_os_login_username # Find this via `gcloud compute ssh ...` the first time, e.g., erfan_miahi_fronix_net
        ProxyCommand gcloud compute start-iap-tunnel %h %p --project=YOUR_PROJECT_ID --zone=us-central1-a --listen-on-stdin
    ```

    *   Replace `YOUR_PROJECT_ID` with your actual Project ID.
    *   Replace `your_os_login_username` with the username OS Login assigns you on the VM (often derived from your email).
    *   Ensure `gcloud` is in your system's PATH or provide the full path in `ProxyCommand`.
3.  **Connect:** Open the VS Code Command Palette (Cmd+Shift+P), type "Remote-SSH: Connect to Host...", and select the host alias you defined (e.g., `a100-gpu-vm`).

### 8.3 · Troubleshooting: Host Key Changed Error

If you see an error like `WARNING: REMOTE HOST IDENTIFICATION HAS CHANGED!` or `Host key verification failed`, it means your local machine (`~/.ssh/known_hosts`) has an old SSH key stored for the VM's IP or hostname (this often happens if you destroy and recreate the VM).

**Fix:** Remove the old key from your `known_hosts` file using:

```bash
ssh-keygen -R a100-1g # Replace with the actual VM name if different
```

Then try connecting again. SSH will prompt you to accept the new host key.

---

## 9 · Cleanup

```bash
cd infrastructure/google/single_node # Ensure you are in the correct directory
terraform destroy -var 'project_id=$PROJECT_ID' # Tears down the VM and associated resources
```

---

\### Troubleshooting quick hits

| Symptom                                                   | Fix                                                                                                |
| --------------------------------------------------------- | -------------------------------------------------------------------------------------------------- |
| `Key creation is not allowed on this service account`     | Use **Option B** (WIF) or ask an admin to lift `constraints/iam.disableServiceAccountKeyCreation`. |
| `argument PROJECT_ID: Must be specified`                  | Export `PROJECT_ID` env var **or** pass the literal project ID in the command.                     |
| `unrecognized arguments: or granular roles/compute.admin` | Remove inline comments when pasting commands.                                                      |

---

**Happy training!**
