variable "project_id" {
  type = string
}

variable "region" {
  type        = string
  default     = "us-central1"
  description = "Region to deploy resources"
}

variable "gpu_count" {
  type        = number
  description = "1, 2, 4 or 8 A100 GPUs"
  validation {
    condition     = contains([1, 2, 4, 8], var.gpu_count)
    error_message = "gpu_count must be 1, 2, 4, or 8."
  }
}

variable "subnet_cidr" {
  type        = string
  default     = "10.80.0.0/20"
  description = "CIDR range for the GPU subnet"
}

variable "boot_disk_size" {
  type        = number
  default     = 150
  description = "Size of the boot disk in GB"
}

variable "vm_image" {
  type        = string
  default     = "projects/deeplearning-platform-release/global/images/family/pytorch-2-4-cu124-debian-11-py310"
  description = "VM image to use for the GPU instance"
}
