# Infrastructure and DevOps for LLM Service

This document outlines the infrastructure and DevOps practices for our LLM service, focusing on Azure cloud resources, Infrastructure as Code with Terraform, and Continuous Integration/Continuous Deployment (CI/CD) with Azure Pipelines.

## Azure Infrastructure

Our LLM service will be hosted on Azure, leveraging its scalability and robust set of services.

### Key Components:

1. **Azure Kubernetes Service (AKS)**
   - For orchestrating our LLM service containers
   - For orhcestrating our web layer containers
   - Enables easy scaling and management

2. **Azure Container Registry (ACR)**
   - To store and manage our Docker images
  
3. **PostgreSQL database**
   - To store user data and chat history

4. **Redis**
   - Caching frequently access data for both the LLM and Web layers

5. **Azure Blob Storage**
   - For storing static resources associated with AI characters (eg. profile pictures and character style descriptions)
   - For storing GGUF model files, enables easy model updates without redeploying the entire application
   - We may potentially host other components inside the AKS cluster as opposed to separate resources. In those cases, some of them may also have mounted blob containers 

6. **Azure Monitor**
   - For monitoring the performance and health of our service

7. **Azure Key Vault**
   - To securely store sensitive configuration data

8. **Azure Virtual Network**
   - For network isolation and security

## Infrastructure as Code with Terraform

We'll use Terraform to define and manage our Azure infrastructure.

```hcl
# Example Terraform configuration
provider "azurerm" {
  features {}
}

resource "azurerm_resource_group" "llm_rg" {
  name     = "llm-service-rg"
  location = "East US"
}

resource "azurerm_kubernetes_cluster" "llm_aks" {
  name                = "llm-aks-cluster"
  location            = azurerm_resource_group.llm_rg.location
  resource_group_name = azurerm_resource_group.llm_rg.name
  dns_prefix          = "llmaks"

  default_node_pool {
    name       = "default"
    node_count = 3
    vm_size    = "Standard_NC6s_v3"  # GPU-enabled VM size
  }

  identity {
    type = "SystemAssigned"
  }
}

resource "azurerm_container_registry" "llm_acr" {
  name                = "llmacrregistry"
  resource_group_name = azurerm_resource_group.llm_rg.name
  location            = azurerm_resource_group.llm_rg.location
  sku                 = "Premium"
  admin_enabled       = false
}

# Additional resources (Blob Storage, Key Vault, etc.) would be defined here
```

## CI/CD with Azure Pipelines

We'll use Azure Pipelines for continuous integration and deployment.

```yaml
# Example Azure Pipelines configuration
trigger:
  - main

pool:
  vmImage: 'ubuntu-latest'

stages:
- stage: Build
  jobs:
  - job: BuildJob
    steps:
    - task: Docker@2
      inputs:
        containerRegistry: 'llmacrregistry'
        repository: 'llm-service'
        command: 'buildAndPush'
        Dockerfile: '**/Dockerfile'
        tags: |
          $(Build.BuildId)
          latest

- stage: Deploy
  jobs:
  - deployment: DeployToAKS
    pool:
      vmImage: 'ubuntu-latest'
    environment: 'production'
    strategy:
      runOnce:
        deploy:
          steps:
          - task: Kubernetes@1
            inputs:
              connectionType: 'Kubernetes Service Connection'
              namespace: 'default'
              manifests: |
                $(Pipeline.Workspace)/k8s/deployment.yml
                $(Pipeline.Workspace)/k8s/service.yml
              imagePullSecrets: |
                $(imagePullSecret)
              containers: |
                $(containerRegistry)/$(imageRepository):$(tag)
```

## Infrastructure Pipeline

In addition to our application CI/CD pipeline, we maintain a separate pipeline for managing our core infrastructure. This pipeline uses Terraform to create and update our Azure resources, including the AKS cluster.

### Azure DevOps Pipeline for Infrastructure

```yaml
# azure-pipelines-infrastructure.yml
trigger:
  - main  # or whichever branch you use for infrastructure changes

pool:
  vmImage: 'ubuntu-latest'

variables:
  - group: terraform-secrets  # Variable group containing Azure credentials and Terraform backend config

stages:
- stage: Terraform
  jobs:
  - job: TerraformJob
    steps:
    - task: TerraformInstaller@0
      inputs:
        terraformVersion: 'latest'
    
    - task: TerraformTaskV3@3
      inputs:
        provider: 'azurerm'
        command: 'init'
        backendServiceArm: 'Azure-Service-Connection'
        backendAzureRmResourceGroupName: 'terraform-state-rg'
        backendAzureRmStorageAccountName: 'tfstateaccount'
        backendAzureRmContainerName: 'tfstate'
        backendAzureRmKey: 'infrastructure.tfstate'

    - task: TerraformTaskV3@3
      inputs:
        provider: 'azurerm'
        command: 'plan'
        environmentServiceNameAzureRM: 'Azure-Service-Connection'

    - task: TerraformTaskV3@3
      inputs:
        provider: 'azurerm'
        command: 'apply'
        environmentServiceNameAzureRM: 'Azure-Service-Connection'
      condition: succeeded()
```

### Key Components of the Infrastructure Pipeline:

1. **Trigger**: The pipeline is triggered on changes to the main branch (or whichever branch is used for infrastructure changes).

2. **Variable Group**: Sensitive information like Azure credentials and Terraform backend configuration are stored in a variable group for security.

3. **Terraform Installation**: Ensures the latest version of Terraform is installed.

4. **Terraform Init**: Initializes the Terraform working directory and configures the Azure backend for state storage.

5. **Terraform Plan**: Creates an execution plan, allowing for review of changes before application.

6. **Terraform Apply**: Applies the changes to create or update the infrastructure.

### Usage and Best Practices:

1. **Change Control**: Run this pipeline manually after careful review of the Terraform plan output.

2. **State Management**: Use Azure Storage for maintaining Terraform state, enabling team collaboration and state locking.

3. **Environment Segregation**: Create separate pipelines or use variables for managing different environments (dev, staging, production).

4. **Access Control**: Limit the number of people who can trigger this pipeline to maintain infrastructure integrity.

5. **Monitoring**: Enable detailed logging and notifications for all runs of this pipeline.

6. **Regular Updates**: Schedule regular runs of this pipeline to ensure infrastructure stays up-to-date and to catch any configuration drift.

By maintaining a separate pipeline for infrastructure management, we ensure that our core Azure resources, including the AKS cluster, are created and managed in a controlled, version-controlled manner. This approach provides clarity in separating application deployments from infrastructure changes and allows for more granular control over our cloud resources.


## GPU and RAM Estimation

For our LLM service, we need to consider GPU and RAM requirements across different cloud providers. Here's an estimation for running a large language model:

1. **Azure (Our chosen provider)**
   - VM Size: Standard_NC6s_v3
   - GPU: 1 x NVIDIA Tesla V100
   - RAM: 112 GB
   - Estimated cost: $0.90 per hour

2. **AWS (For comparison)**
   - Instance Type: p3.2xlarge
   - GPU: 1 x NVIDIA Tesla V100
   - RAM: 61 GB
   - Estimated cost: $3.06 per hour

3. **Google Cloud (For comparison)**
   - Machine Type: n1-standard-4 with 1 x NVIDIA Tesla T4
   - GPU: 1 x NVIDIA Tesla T4
   - RAM: 64 GB
   - Estimated cost: $0.76 per hour

Note: Costs are approximate and may vary. Always check the latest pricing from cloud providers.

## Scaling Considerations

- Start with a minimum of 3 nodes in the AKS cluster for high availability
- Use the Horizontal Pod Autoscaler (HPA) to automatically scale based on CPU/GPU utilization
- Implement node auto-scaling in AKS to automatically add or remove nodes based on demand

## Monitoring and Logging

- Use Azure Monitor for comprehensive monitoring of the AKS cluster and applications
- Implement Prometheus and Grafana for more detailed, custom monitoring of the LLM service
- Use Azure Log Analytics for centralized log management and analysis

## Security Best Practices

1. Enable Azure AD integration with AKS for authentication
2. Use Azure Key Vault to store and manage secrets
3. Implement network policies in AKS to control pod-to-pod communication
4. Regularly update and patch all components, including the host OS, container images, and Kubernetes version

## Disaster Recovery and Backup

1. Use Azure Backup to regularly backup AKS cluster data
2. Implement a multi-region deployment strategy for high availability
3. Regularly test disaster recovery procedures

## Conclusion

This infrastructure setup provides a robust, scalable, and secure foundation for our LLM service. By leveraging Azure services, Infrastructure as Code with Terraform, and automated CI/CD pipelines, we ensure consistency, reliability, and ease of management for our deployment. Regular reviews and optimizations of the infrastructure will be crucial as the service grows and evolves.

