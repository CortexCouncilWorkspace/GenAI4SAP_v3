import configparser
import subprocess
import os
import sys
import requests
from utilities import (PROJECT_ID, REGION_ID, BQ_DATASET_ID, BQ_TABLE_LIST, CHROMA_DATA_BUCKET, SERVICE_ACCOUNT_NAME, CLOUDRUN_APP_NAME, SECRET_NAME)


def run_command(command):
    """
    Executes a command and checks for success.

    Args:
        command (str): The command to execute.

    Returns:
        bool: True if the command succeeds, False otherwise.
    """
    process = subprocess.run(command.split(), capture_output=True, text=True)
    if process.returncode != 0:
        print(f"Error executing command: {command}")
        print(f"Error output: {process.stderr}")
        return False
    return True

def resource_exists(resource_type, resource_name, project_id=None):
    """
    Checks if a given Google Cloud resource already exists.

    Args:
        resource_type (str): The type of resource to check (e.g., "serviceAccounts", "buckets").
        resource_name (str): The name of the resource to check.
        project_id (str, optional): The project ID of the resource. Defaults to the currently configured project.

    Returns:
        bool: True if the resource exists, False otherwise.
    """

    if project_id:
        command = f"gcloud {resource_type} list --filter=name:{resource_name} --project {project_id}"
    else:
        command = f"gcloud {resource_type} list --filter=name:{resource_name}"

    process = subprocess.run(command.split(), capture_output=True, text=True)

    # Check for both the resource name and the "Listed 0 items" message
    return resource_name in process.stdout and "Listed 0 items" not in process.stdout

def train_setup(service_url, project_id, dataset_id, table_list):
    endpoint = f"{service_url}/api/v0/setup_train"
    payload = {"project_id": f"{project_id}", "dataset_id": f"{dataset_id}", "table_list": f"{table_list}"}
    try:
        response = requests.post(endpoint, json=payload)
        response.raise_for_status()
        data = response.json()
        return data
    except requests.exceptions.RequestException as e:
        exception = (f"Error generating Training Session: {e}")
        return exception

def main():
    # Read configuration variables from config.ini
    print("Reading Configuration File   ")
    project_id = PROJECT_ID
    dataset_id = BQ_DATASET_ID
    service_account_name = SERVICE_ACCOUNT_NAME
    chroma_data_bucket = CHROMA_DATA_BUCKET
    cloud_run_app_name = CLOUDRUN_APP_NAME
    region_id = REGION_ID
    secret_name = SECRET_NAME
    table_list = BQ_TABLE_LIST

    # Set Google Cloud project
    print(f"Setting project to {project_id}")
    if not run_command(f"gcloud config set project {project_id}"):
        sys.exit(1)

    # Enable required Google Cloud services
    services = [
        "cloudresourcemanager.googleapis.com",
        "serviceusage.googleapis.com",
        "bigquery.googleapis.com",
        "run.googleapis.com",
        "iam.googleapis.com",
        "cloudapis.googleapis.com",
        "cloudbuild.googleapis.com",
        "aiplatform.googleapis.com",
        "storage.googleapis.com",
        "generativelanguage.googleapis.com",
        "secretmanager.googleapis.com"
    ]
    enable_command = f"gcloud services enable {' '.join(services)}"
    print("Enabling required services...")
    if not run_command(enable_command):
        sys.exit(1)

    # Create service account if it doesn't exist
    print("Creating Service Account...")
    if resource_exists("iam service-accounts", service_account_name, project_id):
        print(f"Service account {service_account_name} already exists, skipping creation.")
    else:
        if not run_command(f"gcloud iam service-accounts create {service_account_name} --project={project_id}"):
            sys.exit(1)

    # Get service account email
    service_account_email = subprocess.check_output(
        f"gcloud iam service-accounts list --filter=email:{service_account_name} --project={project_id} --format='value(email)'",
        shell=True,
        text=True
    ).strip()
    member = f"serviceAccount:{service_account_email}"

    # Grant necessary roles to the service account
    roles = [
        'roles/bigquery.admin',
        'roles/run.invoker',
        'roles/iam.serviceAccountTokenCreator',
        'roles/aiplatform.user',
        'roles/storage.admin',
        'roles/secretmanager.admin',
    ]
    print("Granting roles...")
    for role in roles:
        command = f"""gcloud projects add-iam-policy-binding {project_id} --member="serviceAccount:{service_account_email}" --role="{role}" --quiet --condition=None"""
        if not subprocess.run(command, shell=True):
            sys.exit(1)

    # Grant Storage Permissions to Cloud Build Service Account
    print("Granting required permissions to Cloud Build Service Account...")
    build_roles = [
        'roles/storage.admin',
        'roles/artifactregistry.admin',
    ]
    for build_role in build_roles:
        buildgrant_command = f"""gcloud projects add-iam-policy-binding {project_id}  --member=serviceAccount:$(gcloud projects describe {project_id} --format="value(projectNumber)")@cloudbuild.gserviceaccount.com --role="{build_role}" --quiet"""
        if not subprocess.run(buildgrant_command, shell=True):
            sys.exit(1)
    developer_roles = [
        'roles/storage.admin',
        'roles/artifactregistry.admin',
    ]
    for developer_role in developer_roles:
        developergrant_command = f"""gcloud projects add-iam-policy-binding {project_id}  --member=serviceAccount:$(gcloud projects describe {project_id} --format="value(projectNumber)")-compute@developer.gserviceaccount.com --role={developer_role} --quiet"""
        if not subprocess.run(developergrant_command, shell=True):
            sys.exit(1)

    # Check if artifact repository is available
    print("Check if Default Artifact Repository exist...")
    if resource_exists("artifacts repositories", "cloud-run-source-deploy", project_id):
        print("Repository found, skipping...")
    else:
        print("Default Repository not found, creating...")
        if not run_command(f"gcloud artifacts repositories create cloud-run-source-deploy --repository-format=docker --location={region_id} --immutable-tags --async"):
            sys.exit(1)

    # Create storage bucket if it doesn't exist
    print("Creating Storage Bucket...")
    if resource_exists("storage buckets", chroma_data_bucket, project_id):
        print(f"Storage bucket {chroma_data_bucket} already exists, skipping creation.")
    else:
        if not run_command(f"gcloud storage buckets create gs://{chroma_data_bucket} --project={project_id} --location={region_id}"):
            sys.exit(1)        

    # Create API Key
    print("Creating API Key...")
    api_key = subprocess.check_output("gcloud beta services api-keys create --display-name='GENAI4SAP' --format='json' | jq -r '.response.keyString'", shell=True, text=True).strip()
    module_path = os.path.abspath(os.path.join('.'))
    sys.path.append(module_path)
    config_file = module_path+'/config/config.ini'
    config = configparser.ConfigParser()
    config.read(config_file)
    config.set('API_AUTH', 'api_key', f'{api_key}')

    with open(config_file, 'w') as configfile:
        config.write(configfile)

    
    # Deploy Cloud Run app
    deploy_command = (
        f"gcloud beta run deploy {cloud_run_app_name} "
        f"--region {region_id} "
        f"--source . "
        f"--execution-environment gen2 "
        f"--add-volume=name=v_chromadb,type=cloud-storage,bucket={chroma_data_bucket} "
        f"--add-volume-mount=volume=v_chromadb,mount-path=/chroma_data "
        f"--service-account={service_account_email} "
        #f"--update-secrets=/secrets/api_key={secret_name}:latest "
        f"--port 8084 "
        f"--cpu=2 "
        f"--memory=2Gi "
        f"--service-min-instances=1 "
        f"--min-instances=1 "
        #f"--allow-unauthenticated "
        f"--project={project_id} "
        f"--format='value(status.url)'"
    )
    print("Executing App Deploy...")
    if not subprocess.run(deploy_command, stdout=subprocess.PIPE, shell=True):
        sys.exit(1)    

    # Get Service URL
    # get_service_url_cmd = f"""gcloud run services list --filter="SERVICE:{cloud_run_app_name}" --format='value(URL)'"""
    # service_url = subprocess.check_output(get_service_url_cmd, shell=True, text=True).strip()
    # if service_url is not None:
    #     print(f"App Service URL: {service_url}")
    # else:
    #     print("Cannot get Service URL, check logs and run training setup later")
    #     sys.exit(1)

    print("Setup completed successfully!")

if __name__ == "__main__":
    main()