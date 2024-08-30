# Provider configuration
provider "google" {
  project = var.project_id
  zone    = var.zone
}

# Variables
variable "project_id" {
  description = "Google Cloud Project ID"
  type        = string
  default     = "psyched-choir-433003-j0"
}

variable "region" {
  description = "GCP region"
  type        = string
  default     = "us-west1"
}

variable "zone" {
  description = "GCP zone"
  type        = string
  default     = "us-west1-b"
}

variable "client_machine_type" {
  description = "Machine type for client instances"
  type        = string
  default     = "n1-highmem-8"
}

variable "client_count" {
  description = "Number of client instances to create"
  type        = number
  default     = 5
}

variable "client_snapshot_name" {
  description = "Name of the snapshot to use for client instances"
  type        = string
  default     = "projects/psyched-choir-433003-j0/global/snapshots/ima-client-snapshot"
}

# VPC Network
resource "google_compute_network" "ima_vpc" {
  name                    = "ima-vpc"
  auto_create_subnetworks = false
}

# Subnet
resource "google_compute_subnetwork" "ima_vpc" {
  name          = "android-orchestrator-subnet"
  ip_cidr_range = "10.0.1.0/24"
  region        = var.region
  network       = google_compute_network.ima_vpc.id
}

# Firewall rules
resource "google_compute_firewall" "allow_all_custom" {
  name    = "allow-all-custom-rules"
  network = google_compute_network.ima_vpc.name

  allow {
    protocol = "tcp"
    ports    = ["5037", "5555", "5901", "6444", "8443", "15550-15599"]
  }

  allow {
    protocol = "udp"
    ports    = ["15550-15599"]
  }

  allow {
    protocol = "icmp"
  }

  allow {
    protocol = "tcp"
    ports    = ["3389"]
  }

  allow {
    protocol = "tcp"
    ports    = ["22"]
  }

  allow {
    protocol = "tcp"
    ports    = ["0-65535"]
  }

  allow {
    protocol = "udp"
    ports    = ["0-65535"]
  }

  source_ranges = ["0.0.0.0/0", "10.128.0.0/9"]

  priority = 1000
}

# Client disks
resource "google_compute_disk" "ima-client-disk" {
  count = var.client_count
  name  = "ima-client-${count.index}-boot"
  type  = "pd-ssd"
  zone  = var.zone
  snapshot = var.client_snapshot_name
  size  = 350
}

# Orchestrator instance
resource "google_compute_instance" "orchestrator" {
  name         = "ima-orchestrator"
  machine_type = "e2-medium"
  zone         = var.zone

  boot_disk {
    initialize_params {
      image = "debian-cloud/debian-10"
    }
    device_name = "ima-orchestrator-boot"
  }

  network_interface {
    subnetwork = google_compute_subnetwork.ima_vpc.self_link
    access_config {
      // Ephemeral IP
    }
  }

  metadata_startup_script = <<-EOF
    #!/bin/bash

    # Update package lists and install required packages
    sudo apt-get update
    sudo apt-get install -y git docker.io

    # Clone the repository with sparse-checkout
    cd ~
    git clone --no-checkout https://github.com/cenab/android_machine_ima.git
    cd android_machine_ima
    git sparse-checkout init --cone
    git sparse-checkout set orchestrator
    git checkout main

    # Build and run the Docker container
    cd orchestrator
    docker build -t ima-orchestrator -f Dockerfile .
    docker run -d ima-orchestrator

    # Set up Android environment and launch Cuttlefish
    cd ../aosp/
    source build/envsetup.sh
    lunch 16
    launch_cvd &
  EOF

  service_account {
    scopes = ["cloud-platform"]
  }
}

# Client instances
resource "google_compute_instance" "client" {
  count        = var.client_count
  name         = "ima-client-${count.index}"
  machine_type = var.client_machine_type
  zone         = var.zone

  boot_disk {
    source      = "${element(google_compute_disk.ima-client-disk.*.self_link, count.index)}"
    device_name = "${element(google_compute_disk.ima-client-disk.*.name, count.index)}"
  }

  network_interface {
    subnetwork = google_compute_subnetwork.ima_vpc.self_link
    access_config {
      // Ephemeral IP
    }
  }

  metadata_startup_script = <<-EOF
    #!/bin/bash

    # Update package lists and install required packages
    sudo apt-get update
    sudo apt-get install -y git docker.io

    # Clone the repository with sparse-checkout
    cd ~
    git clone --no-checkout https://github.com/cenab/android_machine_ima.git
    cd android_machine_ima
    git sparse-checkout init --cone
    git sparse-checkout set client
    git checkout main

    # Build and run the Docker container
    cd client
    docker build -t ima-client -f Dockerfile .
    docker run -d ima-client

    # Set up Android environment and launch Cuttlefish
    cd ../aosp/
    source build/envsetup.sh
    lunch 16
    launch_cvd &
  EOF

  service_account {
    scopes = ["cloud-platform"]
  }
}

# Outputs
output "orchestrator_external_ip" {
  description = "The external IP of the orchestrator instance"
  value       = google_compute_instance.orchestrator.network_interface[0].access_config[0].nat_ip
}

output "client_external_ips" {
  description = "The external IPs of the client instances"
  value       = google_compute_instance.client[*].network_interface[0].access_config[0].nat_ip
}
