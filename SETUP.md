Sure! Here's the previous answer formatted in Markdown:

---

# How to Run the Terraform Script on Google Cloud

To run the Terraform script you provided and set up the necessary permissions in Google Cloud, you need to follow these steps:

## 1. Set Up Google Cloud SDK and Terraform

First, ensure that you have the Google Cloud SDK and Terraform installed on your machine.

- **Google Cloud SDK Installation**: [Install the Google Cloud SDK](https://cloud.google.com/sdk/docs/install).
- **Terraform Installation**: [Install Terraform](https://learn.hashicorp.com/tutorials/terraform/install-cli).

## 2. Authenticate with Google Cloud

1. **Authenticate with Google Cloud**:
   - Run the following command to authenticate with Google Cloud:

     ```bash
     gcloud auth application-default login
     ```

   - This will open a browser window where you can log in with your Google Cloud credentials.

2. **Set the Project**:
   - Set your default project to the one specified in the `terraform.tfvars`:

     ```bash
     gcloud config set project psyched-choir-433003-j0
     ```

## 3. Set Up IAM Permissions

To allow Terraform to create and manage resources in Google Cloud, the account used by Terraform needs appropriate IAM roles. The service account used by Terraform should have the following permissions:

1. **Required IAM Roles**:
   - `roles/compute.admin` – Full control over Compute Engine resources.
   - `roles/iam.serviceAccountUser` – Allows the account to use service accounts.
   - `roles/storage.admin` – Access to create and manage storage buckets (for Container Registry).
   - `roles/container.admin` – Full control over Google Kubernetes Engine and Container Registry.

2. **Create a Service Account**:
   - If you don't have a service account, create one:

     ```bash
     gcloud iam service-accounts create terraform --description="Terraform Service Account" --display-name="Terraform"
     ```

3. **Assign IAM Roles to the Service Account**:
   - Assign the necessary roles to your service account:

     ```bash
     gcloud projects add-iam-policy-binding psyched-choir-433003-j0 \
       --member="serviceAccount:terraform@psyched-choir-433003-j0.iam.gserviceaccount.com" \
       --role="roles/compute.admin"

     gcloud projects add-iam-policy-binding psyched-choir-433003-j0 \
       --member="serviceAccount:terraform@psyched-choir-433003-j0.iam.gserviceaccount.com" \
       --role="roles/iam.serviceAccountUser"

     gcloud projects add-iam-policy-binding psyched-choir-433003-j0 \
       --member="serviceAccount:terraform@psyched-choir-433003-j0.iam.gserviceaccount.com" \
       --role="roles/storage.admin"

     gcloud projects add-iam-policy-binding psyched-choir-433003-j0 \
       --member="serviceAccount:terraform@psyched-choir-433003-j0.iam.gserviceaccount.com" \
       --role="roles/container.admin"
     ```

## 4. Configure Terraform

1. **Create a Directory for Terraform Files**:
   - Create a directory where your Terraform configuration files will be stored:

     ```bash
     mkdir terraform-gcp-setup
     cd terraform-gcp-setup
     ```

2. **Create a Terraform Configuration File**:
   - Copy the Terraform configuration script you provided into a file named `main.tf`.

3. **Create a `terraform.tfvars` File**:
   - Create a `terraform.tfvars` file with the following content (adjust as necessary):

     ```hcl
     project_id           = "psyched-choir-433003-j0"
     region               = "us-west1"
     zone                 = "us-west1-b"
     client_machine_type  = "n1-highmem-8"
     client_count         = 5
     client_snapshot_name = "android-machine-client"
     ```

## 5. Initialize Terraform

1. **Initialize Terraform**:
   - Run the following command to initialize Terraform in the current directory:

     ```bash
     terraform init
     ```

2. **Apply the Terraform Configuration**:
   - To apply the Terraform configuration, run:

     ```bash
     terraform apply
     ```

   - Terraform will display a summary of the resources it will create. Type `yes` to confirm.

## 6. Manage the Terraform State

- **Stop Instances**:
  - If you want to stop the instances later using Terraform, create another Terraform script based on the instructions provided earlier, or use the same script with a different approach (e.g., a `null_resource` with a `local-exec` provisioner that stops the instances).
  
  - Apply the Terraform script to stop the instances:

    ```bash
    terraform apply -var-file="terraform.tfvars"
    ```

## Summary

1. **Install and configure Google Cloud SDK and Terraform**.
2. **Authenticate with Google Cloud** and set the project.
3. **Create and assign necessary IAM roles** to the service account.
4. **Set up and initialize Terraform** with your configuration.
5. **Run the Terraform script** to create resources.
6. **Use another Terraform script** or modify the existing one to stop the instances when needed.

This setup ensures that your Terraform script has the necessary permissions to manage resources on Google Cloud, and you can easily run or stop instances as needed.

---