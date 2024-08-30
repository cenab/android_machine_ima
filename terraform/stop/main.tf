# Provider configuration
provider "google" {
  project = var.project_id
  region  = var.region
}

# Variables
variable "project_id" {
  description = "Google Cloud Project ID"
  type        = string
}

variable "region" {
  description = "GCP region"
  type        = string
}

variable "zone" {
  description = "GCP zone"
  type        = string
}

variable "client_machine_type" {
  description = "Machine type for client instances"
  type        = string
}

variable "client_count" {
  description = "Number of client instances to create"
  type        = number
}

variable "client_snapshot_name" {
  description = "Name of the snapshot to use for client instances"
  type        = string
}

# Use the snapshot to create the persistent disk for orchestrator
resource "google_compute_disk" "orchestrator_disk" {
  name  = "orchestrator-disk"
  type  = "pd-ssd"
  zone  = var.zone
  source_snapshot = var.client_snapshot_name
}

# Orchestrator instance
resource "google_compute_instance" "orchestrator" {
  name         = "ima-orchestrator"
  machine_type = "e2-medium"
  zone         = var.zone

  boot_disk {
    source = google_compute_disk.orchestrator_disk.id
  }

  network_interface {
    subnetwork = google_compute_subnetwork.ima_vpc.self_link
    access_config {
      // Ephemeral IP
    }
  }

  metadata_startup_script = <<-EOF
    #!/bin/bash
    sudo apt-get update
    sudo apt-get install -y git docker.io
    cd ~
    git clone --no-checkout https://github.com/cenab/android_machine_ima.git
    cd android_machine_ima
    git sparse-checkout init --cone
    git sparse-checkout set orchestrator
    git checkout main
    cd orchestrator
    docker build -t ima-orchestrator -f Dockerfile .
    docker run -d ima-orchestrator
    cd ../aosp/
    source build/envsetup.sh
    lunch 16
    launch_cvd &
  EOF

  service_account {
    scopes = ["cloud-platform"]
  }
}

# Use the snapshot to create the persistent disk for each client
resource "google_compute_disk" "client_disk" {
  count = var.client_count
  name  = "client-disk-${count.index}"
  type  = "pd-ssd"
  zone  = var.zone
  source_snapshot = var.client_snapshot_name
}

# Client instances
resource "google_compute_instance" "client" {
  count        = var.client_count
  name         = "ima-client-${count.index}"
  machine_type = var.client_machine_type
  zone         = var.zone

  boot_disk {
    source = google_compute_disk.client_disk[count.index].id
  }

  network_interface {
    subnetwork = google_compute_subnetwork.ima_vpc.self_link
    access_config {
      // Ephemeral IP
    }
  }

  metadata_startup_script = <<-EOF
    #!/bin/bash
    sudo apt-get update
    sudo apt-get install -y git docker.io
    cd ~
    git clone --no-checkout https://github.com/cenab/android_machine_ima.git
    cd android_machine_ima
    git sparse-checkout init --cone
    git sparse-checkout set client
    git checkout main
    cd client
    docker build -t ima-client -f Dockerfile .
    docker run -d ima-client
    cd ../aosp/
    source build/envsetup.sh
    lunch 16
    launch_cvd &
  EOF

  service_account {
    scopes = ["cloud-platform"]
  }
}
