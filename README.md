# Android Machine Orchestrator: IMA Data Generation Methodology

### Managing Multiple Android Devices in Instant Messaging Applications (IMAs) and Encrypted Network Traffic Flow Generation on Cloud

## Overview

This project aims to facilitate communication between multiple Android devices using Instant Messaging Applications (IMAs) to collect encrypted network traffic flows. It addresses current limitations in resource usage, synchronization, and UI workflow management, and proposes solutions for effective device management.

## Project Objectives

1. **Efficient Device Management**: Orchestrate communication between multiple Android devices for seamless IMA interactions.
2. **Encrypted Network Traffic Collection**: Gather encrypted network traffic flows from Android devices operating within cloud-based emulators.
3. **Scalability**: Enable management of numerous Android emulators in a cloud environment without hardware restrictions.

## Limitations

### 1. High Resource Usage of Android Emulators

- Running multiple Android emulators on a single computer is resource-intensive, causing significant CPU load and performance issues.

### 2. Synchronization Challenges

- Current methods using ADB and timing mechanisms in scripts lack reliability for synchronizing multiple devices.

### 3. Managed UI Workflow Status

- Commands may not execute in the intended order or timeframe, causing UI workflow disruptions.

## Proposed Solutions

### 1. Master-Slave Architecture

- Implement a master-slave architecture where a central orchestrator (master) controls the actions of individual devices (slaves). This ensures commands are executed in a controlled and verified manner.

### 2. Queuing System and Command Verification

- Introduce a queuing system to manage command execution sequentially. Verify the successful execution of each command to ensure reliability and synchronization across devices.

### 3. Cloud-Based or Distributed Emulators

- To overcome the resource limitations of running multiple emulators on a single machine, consider using cloud-based emulator services or distributing the emulators across multiple physical or virtual machines.

### 4. Performance Optimization

- Optimize emulator configurations and the orchestration script to minimize resource usage. This may include reducing emulated hardware features or using headless emulators to improve performance.

## Cloud Android Emulator Orchestrator

Due to technical limitations, we aim to replicate the local network environment in the cloud. Instead of using local hardware, we suggest running a local server on a local machine to act as the 'edge,' while the Android device emulators operate as Docker containers within the same Virtual Private Cloud (VPC) on AWS. AWS describes a VPC as a virtual network that closely resembles a traditional network but uses AWS's scalable infrastructure.

### Benefits

- **Scalability**: Boot as many emulators as needed without hardware restrictions on local machines.
- **Efficiency**: Run tests with a larger number of devices, exceeding the limitations of 2 or 3 local machines.

## Implementation Details

- **Python Flask Server**: Utilize a Python Flask server with WebSocket communication to manage cloud-based Android emulators in a queue-like fashion.
- **ADB and WebSocket Integration**: Each Android device will connect to the server via WebSocket and run a receiver to facilitate communication and execute ADB scripts.
- **Feedback Mechanism**: Modify scripts to return success or failure responses, ensuring the queue can continue managing IMA messages.
- **Data Transfer**: Use SCP (Secure Copy Protocol) to send tcp dumps and recorded unique IMA ports from emulators to the server for analysis.

## Setup and Installation

1. **Clone the Repository**:

   ```bash
   git clone https://github.com/yourusername/android-machine-orchestrator.git
   cd android-machine-orchestrator

2. **Set Up the Environment**:

   ```bash
   python3 -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt
   ```

3. **Configure AWS Credentials**:

   Set up your AWS credentials according to AWS CLI configuration guidelines.

4. **Deploy the Infrastructure**:

   ```bash
   cd terraform
   terraform init
   terraform apply
   ```

5. **Start the Orchestrator**:

   ```bash
   python orchestrator/server.py
   ```

6. **Launch Emulators**:

   ```bash
   python launch_emulators.py
   ```

## To-Do List

- [ ] Implement the Python Flask server with WebSocket communication
  - [ ] Refine and test the server code in orchestrator/server.py
- [ ] Develop the ADB and WebSocket integration for each Android device
  - [ ] Expand client/client.py to include ADB script execution
- [ ] Modify scripts to return success or failure responses
  - [ ] Update scripts in client/commands/user_interaction_functions/
- [ ] Implement SCP (Secure Copy Protocol) functionality
  - [ ] Add code to transfer tcp dumps and IMA ports from emulators to server
- [ ] Complete the setup and installation process
  - [ ] Finish writing setup instructions in README.md
  - [ ] Create necessary setup scripts
- [ ] Implement the master-slave architecture
  - [ ] Enhance server and client code to support master-slave model
- [ ] Develop a more robust queuing system and command verification
  - [ ] Improve queue implementation in server and client code
- [ ] Optimize performance
  - [ ] Review and optimize emulator configurations and orchestration script
- [ ] Implement cloud deployment
  - [ ] Develop scripts or instructions for AWS deployment
- [ ] Enhance data collection and analysis
  - [ ] Improve client/collect_ports/parse_the_unique_ports.py script
- [ ] Implement extensive testing
  - [ ] Develop and run tests for multiple emulators and IMAs
- [ ] Documentation
  - [ ] Complete documentation for setup, running, and maintenance