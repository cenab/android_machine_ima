# Android Machine Orchestrator: IMA Data Generation Methodology

### Managing Multiple Android Devices in Instant Messaging Applications (IMAs) and Encrypted Network Traffic Flow Generation on Cloud

---

## Overview

This project facilitates communication between multiple Android devices using Instant Messaging Applications (IMAs) to collect encrypted network traffic flows. It addresses resource usage limitations, synchronization, and UI workflow management challenges, proposing solutions for effective device management.

---

## Project Objectives

1. **Efficient Device Management:** Orchestrate communication between multiple Android devices for seamless IMA interactions.
2. **Encrypted Network Traffic Collection:** Gather encrypted network traffic flows from Android devices operating within cloud-based emulators.
3. **Scalability:** Enable management of numerous Android emulators in a cloud environment, bypassing local hardware constraints.

---

## Limitations

1. **High Resource Usage of Android Emulators:** Running multiple emulators can strain CPU resources.
2. **Synchronization Challenges:** Current ADB-based methods lack reliability for device synchronization.
3. **Managed UI Workflow Status:** Commands may not execute in order, causing UI disruptions.

---

## Proposed Solutions

1. **Master-Slave Architecture:** Central orchestrator (master) manages individual devices (slaves), ensuring command control and verification.
2. **Queuing System & Command Verification:** Sequentially queue commands and verify their execution to maintain reliable synchronization.
3. **Cloud-Based Emulators:** Use cloud-based emulator services or distributed VMs to overcome resource limitations.
4. **Performance Optimization:** Adjust emulator settings and scripts to reduce resource usage.

---

## Cloud Android Emulator Orchestrator

This project leverages cloud infrastructure to replicate a local network environment. Instead of local hardware, a local server acts as the "edge," while Android emulators run in Docker containers within a VPC on AWS.

### Benefits

- **Scalability:** Launch multiple emulators without local hardware limits.
- **Efficiency:** Test with a large number of devices beyond the capacity of a few local machines.

---

## Implementation Details

- **Python Flask Server with WebSocket Communication:** Orchestrates emulators in a queue-like fashion.
- **ADB & WebSocket Integration:** Facilitates server-device communication for executing ADB scripts.
- **Feedback Mechanism:** Scripts return success/failure responses for queue management.
- **Data Transfer:** SCP transfers network captures and IMA ports from emulators to the server for analysis.

---

## System Architecture and Workflow

The system includes:

1. **Server:** Manages devices and commands using Flask-SocketIO.
2. **Client Devices:** Android emulators or devices executing commands.
3. **Orchestrator:** Sends commands to the server based on a defined schedule.

### Interaction Flow

- Clients and Orchestrator connect to the server via WebSocket.
- Clients register upon connection.
- Orchestrator sends commands to the server, which queues and distributes them.
- Clients execute commands and return results, maintaining system state.

---

## Setup and Installation

### Prerequisites

- **Operating System:** Linux-based system recommended.
- **Python 3**, **Git**, **ADB (Android Debug Bridge)**, **Terraform**
- **AWS/GCP Account** (for cloud emulators)

### Installation Steps

1. **Clone the Repository**

   ```bash
   git clone https://github.com/yourusername/android-machine-orchestrator.git
   cd android-machine-orchestrator
   ```

2. **Set Up Environment**

   **Install system dependencies**

   ```bash
   sudo apt update && sudo apt install python3-venv python3-pip -y
   ```

   **Create and activate a virtual environment**

   ```bash
   python3 -m venv venv
   source venv/bin/activate
   ```

   **Install Python dependencies**

   ```bash
   pip install -r requirements.txt
   ```

3. **Configure Cloud Infrastructure**

   **Google Cloud Platform (GCP):**

   - Install and configure Google Cloud SDK.
   - Authenticate and set up IAM permissions.

     ```bash
     gcloud auth login
     gcloud config set project your-project-id
     ```

   **AWS:**

   - Install and configure AWS CLI.

     ```bash
     aws configure
     ```

4. **Provision Infrastructure with Terraform**

   ```bash
   terraform -chdir=terraform apply
   ```

5. **Start the Orchestrator**

   ```bash
   ./start_orchestrator.sh
   ```

6. **Launch Client Emulators**

   ```bash
   ./client_setup.sh
   ```

7. **Generate Dialogues (Optional)**

   ```bash
   ./generate_dialogues.sh
   ```

8. **Run the System**

   With the server, orchestrator, and clients running, the orchestrator will send scheduled commands to the clients for IMA interaction and data collection.

9. **Data Collection and Analysis**

   - Use `util/flow_generation` scripts to process network captures.
   - Run `process_ports_filters.py` to generate Wireshark filters.
   - Execute `run_all.sh` and `generate_flows.sh` for automated flow generation.
   - Use `util/ml_analysis` scripts for ML analysis on collected data.

---

## Directory Structure

- **client/**: Client scripts and modules for IMAs.
- **orchestrator/**: Server and orchestrator code, dialogue scripts.
- **terraform/**: Infrastructure configuration.
- **util/**: Utility scripts for traffic generation and ML analysis.

---

## Dependencies

- **Python Packages**: Flask, flask-socketio, python-socketio[client], pandas, openpyxl, eventlet, gunicorn, asyncio, aiohttp
- **System Packages**: python3-venv, python3-pip, Android SDK & ADB Tools
- **Cloud SDKs**: Google Cloud SDK or AWS CLI (based on provider)

---

## IMAs Versions

- **WhatsApp**: 2.23.12.75
- **Facebook Messenger**: 471.0.0.0.6
- **Telegram**: 10.0.5
- **Microsoft Teams**: 14161.0.0.2023053702
- **Discord**: 194.24 - Stable
- **Signal**: 6.42.7
- **Slack**: 21.10.20.0
- **TextNow**: 23.26.0.2

---

## License

This project is licensed under the MIT License - see the LICENSE file for details.

---

## Notes

- Replace placeholders (e.g., `yourusername`, `your-project-id`) with your actual credentials.
- Refer to detailed *.md files for explanations (`SETUP.md`, `WORKFLOW.md`).
- Robust error handling included for connection and execution errors.

---