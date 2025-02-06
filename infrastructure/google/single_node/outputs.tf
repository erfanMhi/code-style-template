output "gpu_vm_name" {
  description = "Name of the GPU VM instance"
  value       = google_compute_instance.a100_vm.name
}

output "gpu_vm_zone" {
  description = "Zone where the GPU VM is deployed"
  value       = google_compute_instance.a100_vm.zone
}

output "gpu_vm_machine_type" {
  description = "Machine type of the GPU VM"
  value       = google_compute_instance.a100_vm.machine_type
}

output "connection_command" {
  description = "Command to connect to the VM via IAP SSH"
  value       = "gcloud compute ssh ${google_compute_instance.a100_vm.name} --project ${var.project_id} --zone ${google_compute_instance.a100_vm.zone} --tunnel-through-iap"
}

output "service_account" {
  description = "Service account used by the VM"
  value       = google_service_account.vm_sa.email
}
