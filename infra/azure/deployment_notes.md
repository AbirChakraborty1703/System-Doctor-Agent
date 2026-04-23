# Azure Deployment Notes

## Current deployment-ready targets

- Streamlit app container (apps/streamlit)
- FastAPI service container (apps/api)

## Suggested Azure services

- Azure Container Apps for API and Streamlit containers
- Azure AI Foundry for managed model endpoints
- Azure Monitor + Application Insights for telemetry
- Azure Key Vault for secrets

## Minimal deployment sequence

1. Build and push containers to registry.
2. Provision Container Apps environment.
3. Deploy API and Streamlit containers with environment variables.
4. Configure ingress and health probes.
5. Enable logging and metrics.
