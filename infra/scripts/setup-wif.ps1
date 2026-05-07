# setup-wif.ps1 — Workload Identity Federation provisioning for GitHub Actions
# Run from PowerShell with: .\infra\scripts\setup-wif.ps1
# Prereq: gcloud CLI authenticated as project owner/IAM admin

$project = "brasili-ia-news"
$project_number = "180096224219"
$pool_name = "github-actions-pool"
$provider_name = "github-provider"
$sa_name = "github-actions-sa"
$sa_email = "$sa_name@$project.iam.gserviceaccount.com"
$github_repo = "viniciusbritor/Avatar"

Write-Host "=== Step 1: Create Workload Identity Pool ===" -ForegroundColor Cyan
gcloud iam workload-identity-pools create $pool_name `
  --project=$project `
  --location="global" `
  --display-name="GitHub Actions Pool"

Write-Host "=== Step 2: Create OIDC Provider ===" -ForegroundColor Cyan
gcloud iam workload-identity-pools providers create-oidc $provider_name `
  --project=$project `
  --location="global" `
  --workload-identity-pool=$pool_name `
  --display-name="GitHub OIDC Provider" `
  --attribute-mapping="google.subject=assertion.sub,attribute.actor=assertion.actor,attribute.repository=assertion.repository,attribute.repository_owner=assertion.repository_owner" `
  --issuer-uri="https://token.actions.githubusercontent.com"

Write-Host "=== Step 3: Create CI/CD Service Account (least-privilege) ===" -ForegroundColor Cyan
gcloud iam service-accounts create $sa_name `
  --project=$project `
  --display-name="GitHub Actions WIF Service Account"

Write-Host "=== Step 4: Grant IAM Roles ===" -ForegroundColor Cyan

# Cloud Build submit
gcloud projects add-iam-policy-binding $project `
  --member="serviceAccount:$sa_email" `
  --role="roles/cloudbuild.builds.editor"

# Artifact Registry push
gcloud projects add-iam-policy-binding $project `
  --member="serviceAccount:$sa_email" `
  --role="roles/artifactregistry.writer"

# Secret Manager read
gcloud projects add-iam-policy-binding $project `
  --member="serviceAccount:$sa_email" `
  --role="roles/secretmanager.secretAccessor"

# GCS read/write on vault bucket only
gcloud projects add-iam-policy-binding $project `
  --member="serviceAccount:$sa_email" `
  --role="roles/storage.objectAdmin" `
  --condition="expression=resource.name.startsWith('projects/_/buckets/brasil-ai-avatars-vault'),title=GCSVaultOnly"

# Logging
gcloud projects add-iam-policy-binding $project `
  --member="serviceAccount:$sa_email" `
  --role="roles/logging.logWriter"

# Service Account User (required for Cloud Build impersonation)
gcloud projects add-iam-policy-binding $project `
  --member="serviceAccount:$sa_email" `
  --role="roles/iam.serviceAccountUser"

Write-Host "=== Step 5: Bind WIF principal to SA ===" -ForegroundColor Cyan
$pool_id = "projects/$project_number/locations/global/workloadIdentityPools/$pool_name"
$principal = "principalSet://iam.googleapis.com/${pool_id}/attribute.repository/$github_repo"

gcloud iam service-accounts add-iam-policy-binding $sa_email `
  --project=$project `
  --role="roles/iam.workloadIdentityUser" `
  --member="$principal"

Write-Host "=== WIF Provisioning Complete ===" -ForegroundColor Green
Write-Host ""
Write-Host "Next manual steps:" -ForegroundColor Yellow
Write-Host "  1. Create GCP_SA_KEY backup: gcloud iam service-accounts keys create backup.json --iam-account=$sa_email  (store temporarily for rollback)"
Write-Host "  2. Push code changes (workflows already updated)"
Write-Host "  3. Test: Run produce_avatar.yml via workflow_dispatch"
Write-Host "  4. Test: Trigger ci-cd-api.yml via push to master"
Write-Host "  5. After all workflows pass: delete GCP_SA_KEY from GitHub repo secrets"
Write-Host "  6. Delete GCP_SA_KEY from Secret Manager: gcloud secrets versions destroy latest --secret=GCP_SA_KEY"
Write-Host "  7. Delete old SA key from avatar-api-sa: gcloud iam service-accounts keys list --iam-account=avatar-api-sa@$project.iam.gserviceaccount.com"
Write-Host "  8. Delete key/ directory from disk and backup.json"
