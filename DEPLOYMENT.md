# Production Deployment Guide — Apple Yield Estimator

This document describes the full production deployment process for the Apple Yield Estimator application on AWS Cloud.

---

## Infrastructure Overview

| Component | Service | Details |
|-----------|---------|---------|
| Compute | AWS EC2 | t3.small, Ubuntu 24.04, us-east-1 |
| Database | AWS RDS | PostgreSQL 17, private VPC |
| Storage | AWS S3 | Private bucket, pre-signed URLs |
| Reverse Proxy | Nginx | Host-level, ports 80/443 |
| Containers | Docker + Docker Compose | Backend (FastAPI) + Frontend (Nginx/React) |
| CI/CD | GitHub Actions | Auto-deploy on push to master |

---

## Prerequisites

- AWS CLI installed and configured with a programmatic IAM user
- SSH key pair for EC2 access (`.pem` file)
- Docker and Docker Compose installed on EC2
- PostgreSQL 17 client on EC2
- Node.js 20 on local machine (for local development builds)

---

## 1. EC2 Instance Setup

The EC2 instance runs Ubuntu 24.04. Docker and Docker Compose were installed manually:

```bash
sudo apt-get update
sudo apt-get install -y docker.io docker-compose-plugin
sudo usermod -aG docker ubuntu
sudo systemctl enable docker
sudo systemctl start docker
```

Nginx was installed at the host level to act as a reverse proxy routing traffic to the Docker containers:

```bash
sudo apt-get install -y nginx
```

The Nginx site configuration is located at `/etc/nginx/sites-available/appledetection` and proxies:
- `/` to the frontend container on port 5173
- `/api/` to the backend container on port 8000

---

## 2. RDS PostgreSQL Setup

The database runs on AWS RDS PostgreSQL 17. The EC2 instance acts as a bastion host to connect:

```bash
psql -h YOUR_RDS_ENDPOINT -U YOUR_DB_USER -d YOUR_DB_NAME -p 5432
```

Security groups are configured with bidirectional access between the EC2 security group and the RDS security group on port 5432.

The production database was restored from a local development backup:

```bash
# On local machine
pg_dump -U postgres -d apple_yield_db -F c -f backup.dump

# Transfer to EC2
scp -i "YOUR_KEY.pem" backup.dump ubuntu@YOUR_EC2_IP:~/

# On EC2, restore to RDS
pg_restore --no-owner --no-privileges \
  -h YOUR_RDS_ENDPOINT \
  -U YOUR_DB_USER \
  -d YOUR_DB_NAME \
  backup.dump
```

---

## 3. S3 Bucket Setup

### Create the bucket

```bash
aws s3api create-bucket \
  --bucket YOUR_BUCKET_NAME \
  --region us-east-1
```

### Block all public access

Images are served via pre-signed URLs, never via public access:

```bash
aws s3api put-public-access-block \
  --bucket YOUR_BUCKET_NAME \
  --public-access-block-configuration \
  "BlockPublicAcls=true,IgnorePublicAcls=true,BlockPublicPolicy=true,RestrictPublicBuckets=true"
```

### Verify the bucket was created

```bash
aws s3 ls | grep YOUR_BUCKET_NAME
```

The bucket contains two folders:
- `uploads/` — processed apple detection images
- `avatars/` — user profile pictures

---

## 4. IAM Configuration

A dedicated IAM policy was created with minimum required permissions for the backend service:

```bash
aws iam create-policy \
  --policy-name apple-yield-s3-policy \
  --policy-document '{
    "Version": "2012-10-17",
    "Statement": [
      {
        "Effect": "Allow",
        "Action": [
          "s3:PutObject",
          "s3:GetObject",
          "s3:DeleteObject",
          "s3:ListBucket"
        ],
        "Resource": [
          "arn:aws:s3:::YOUR_BUCKET_NAME",
          "arn:aws:s3:::YOUR_BUCKET_NAME/*"
        ]
      }
    ]
  }'
```

A dedicated programmatic IAM user was created for the backend:

```bash
aws iam create-user --user-name apple-yield-backend

aws iam attach-user-policy \
  --user-name apple-yield-backend \
  --policy-arn arn:aws:iam::YOUR_ACCOUNT_ID:policy/apple-yield-s3-policy

aws iam create-access-key --user-name apple-yield-backend
```

A second IAM user `GH_Actions_Deployer` was created for GitHub Actions CI/CD with `AmazonEC2FullAccess` and `AmazonS3FullAccess` permissions to allow dynamic security group management during deployments.

---

## 5. Environment Configuration

The `.env.prod` file is stored only on the EC2 instance and is never committed to version control. It is located at `~/AppleDetection/.env.prod` with `chmod 600` permissions.

Required environment variables:

```bash
# Application
APP_NAME=Yield_EstimatorApp
DEBUG=false
SECRET_KEY=YOUR_SECRET_KEY

# Database
DATABASE_URL=postgresql://USER:PASSWORD@RDS_ENDPOINT:5432/DB_NAME

# JWT
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

# AWS S3
AWS_ACCESS_KEY_ID=YOUR_ACCESS_KEY_ID
AWS_SECRET_ACCESS_KEY=YOUR_SECRET_ACCESS_KEY
AWS_REGION=us-east-1
S3_BUCKET_NAME=YOUR_BUCKET_NAME
```

### Verify environment variables are loaded in the container

```bash
docker exec apple_backend env | grep S3
```

---

## 6. Migrating Existing Images to S3

The existing local `uploads/` directory (468 images, ~157MB) was migrated directly from the local machine using the AWS CLI sync command:

```bash
aws s3 sync uploads/ s3://YOUR_BUCKET_NAME/uploads/ \
  --region us-east-1
```

The sync command is idempotent and can be safely re-run. It only uploads files that do not already exist in the bucket.

Verify the migration:

```bash
aws s3 ls s3://YOUR_BUCKET_NAME/uploads/ | wc -l
```

---

## 7. Docker Deployment

The application runs as two containers defined in `docker-compose-prod.yml`:

- `apple_backend` — FastAPI + ONNX Runtime on port 8000
- `apple_frontend` — React (pre-built) served via Nginx on port 5173

> **Important:** The ONNX model file (`best_model2.onnx`) is excluded from version control via `.gitignore` and must be transferred manually to the EC2 instance:

```bash
scp -i "YOUR_KEY.pem" \
  app/models/weights/best_model2.onnx \
  ubuntu@YOUR_EC2_IP:~/AppleDetection/app/models/weights/
```

The model was re-exported from Google Colab with `opset=20` to ensure compatibility with `onnxruntime==1.20.1`:

```python
from ultralytics import YOLO

model = YOLO('best.pt')
model.export(format='onnx', opset=20, simplify=True, dynamic=False, imgsz=640)
```

Start all containers:

```bash
cd ~/AppleDetection
docker compose -f docker-compose-prod.yml up -d
```

Check container status:

```bash
docker compose -f docker-compose-prod.yml ps
```

View logs:

```bash
docker logs apple_backend -f
docker logs apple_frontend -f
```

---

## 8. CI/CD with GitHub Actions

The deployment pipeline is defined in `.github/workflows/deploy.yml`. It triggers automatically on every push to the `master` branch.

### Pipeline steps

1. Checkout repository
2. Setup Node.js 20 and install frontend dependencies
3. Build the React frontend (`npm run build`)
4. Dynamically open port 22 on the EC2 security group for the GitHub Actions runner IP only
5. Copy the built `dist/` to the EC2 via SCP
6. SSH into EC2, run `git pull`, rebuild the frontend container, restart the backend container
7. Close port 22 on the security group immediately after deployment

The port 22 open/close mechanism uses the AWS CLI with the `GH_Actions_Deployer` IAM credentials. Port 22 is only open for the exact IP of the GitHub Actions runner and only for the duration of the deployment (approximately 2-3 minutes).

### Required GitHub Secrets

The following secrets must be configured in the repository under `Settings > Secrets and variables > Actions`:

| Secret | Description |
|--------|-------------|
| `AWS_ACCESS_KEY_ID` | GH_Actions_Deployer access key |
| `AWS_SECRET_ACCESS_KEY` | GH_Actions_Deployer secret key |
| `EC2_HOST` | EC2 Elastic IP address |
| `EC2_USER` | EC2 SSH user (`ubuntu`) |
| `EC2_SSH_KEY` | Full contents of the `.pem` key file |

---

## 9. Database Schema Changes in Production

Schema changes must be applied manually to the RDS instance before deploying new code that depends on them. Connect via the EC2 bastion host and run the ALTER TABLE statements directly:

```bash
psql -h YOUR_RDS_ENDPOINT -U YOUR_DB_USER -d YOUR_DB_NAME -p 5432
```

Example — adding the `avatar_url` column:

```sql
ALTER TABLE users ADD COLUMN avatar_url VARCHAR;
\d users
```

Always apply the schema change first, then push the code.

---

## 10. Security Considerations

- The `.env.prod` file is never committed to version control
- The ONNX model file is excluded from version control
- The S3 bucket has all public access blocked; images are served via pre-signed URLs with 1-hour expiration
- IAM users follow the principle of least privilege
- Port 22 on EC2 is only open during CI/CD deployments for the exact runner IP
- RDS is not publicly accessible; it only accepts connections from the EC2 security group
- JWT tokens expire after 30 minutes

---

## Troubleshooting

### Containers not starting after EC2 stop/start

EC2 stop/start does not affect the EBS disk. Containers must be restarted manually:

```bash
cd ~/AppleDetection
docker compose -f docker-compose-prod.yml up -d
```

### Backend container unhealthy

Check logs for errors:

```bash
docker logs apple_backend
```

Common causes: missing `.env.prod` variables, RDS connection refused, ONNX model file not found.

### Out of memory during Docker build

The t3.micro (1GB RAM) is insufficient for building the backend container. Use a t3.small (2GB RAM) or larger. The frontend build runs on GitHub Actions infrastructure, never on the EC2 instance.

### Out of memory during Docker build

The t3.micro (1GB RAM) is insufficient for building the frontend container. Use a t3.small (2GB RAM) or larger.

### CI/CD with GitHub Actions

The deployment pipeline is defined in `.github/workflows/deploy.yml`. It triggers automatically on every push to the `master` branch.

---
git push -> GitHub Actions:
            1. npm run build  ( Open GitHub Servers)
            2. scp dist/ 2 EC2
            3. docker compose up --build in EC2
            4. docker compose down
            5. npm run build
            6. scp dist/ 2 EC2
            7. docker compose up --build in EC2
---

### Pipeline steps

 .github/workflows/deploy.yml.

 1. Create an IAM user with the following permissions:
    - EC2 full access
    - S3 full access
    - CloudFormation full access
    - Secrets Manager full access

2. Create a GitHub Secrets with the following keys:
    - AWS_ACCESS_KEY_ID
    - AWS_SECRET_ACCESS_KEY
    - EC2_HOST
    - EC2_USER
    - EC2_SSH_KEY
 
 Settings -> Secrets and variables -> Actions -> New repository secret 

3.Activate the GitHub Actions workflow
_
```
mkdir -p .github/workflows
cp deploy.yml .github/workflows/deploy.yml
git add .github/workflows/deploy.yml
git commit -m "ci: add GitHub Actions deployment workflow"
git push origin master

```

4. Create a CloudFormation stack with the following parameters:
    - EC2InstanceType: t3.small
    - EC2KeyName: EC2 key pair name
    - EC2SecurityGroup: EC2 security group name
    - S3BucketName: S3 bucket name
    - GitHubUser: GitHub user name
    - GitHubToken: GitHub token
    - GitHubRepo: GitHub repo name
    - GitHubBranch: GitHub branch name
    - GitHubWorkflow: GitHub workflow name

5. Create a Secrets Manager secret with the following parameters:
    - SecretName: EC2_HOST
    - SecretString: EC2 Elastic IP address
    - SecretName: EC2_USER
    - SecretString: EC2 SSH user
    - SecretName: EC2_SSH_KEY
    - SecretString: EC2 SSH EC2KeyName
    - SecretName: AWS_ACCESS_KEY_ID
    - SecretString: AWS access key ID
    - SecretName: AWS_SECRET_ACCESS_KEY
    - SecretString: AWS secret access key

6. Create a CloudWatch Event rule with the following parameters:
    - Name: Deploy on push to master
    - Schedule Expression: rate(1 minute)
    - Targets: EC2 instance
        - Id: deploy
        - Role: IAM role
        - Role: EC2 instance
        - Role: S3 bucket
        - Role: CloudFormation stack
        - Role: Secrets Manager secret
        - Role: GitHub Actions workflows
        - Role: GitHub Actions runner
            - Repository: GitHub repo name
            - Label: GitHub workflow name
            - Token: GitHub token
            - RunnerGroup: GitHub runner group
            - Ec2InstanceId: EC2 instance ID
            - Ec2InstanceType: EC2 instance type
            - Ec2KeyName: EC2 key pair name
            - Ec2SecurityGroup: EC2 security group Name

7.  Edit Code in Local Machine

commit changes -> git push origin master -> GitHub Actions despliega automaticamente

8.  Edit Code in GitHub

localhost -> npm run build -> git push origin master -> GitHub Actions despliega automaticamente

9. Open SSH PORT 22 on the EC2 security group for the GitHub Actions runner IP only

```
- name: Open SSH port for GitHub Actions
  run: |
    RUNNER_IP=$(curl -s https://checkip.amazonaws.com)
    aws ec2 authorize-security-group-ingress \
      --group-id sg-0574f1c713a9f5f23 \
      --protocol tcp \
      --port 22 \
      --cidr ${RUNNER_IP}/32
  env:
    AWS_ACCESS_KEY_ID: ${{ secrets.AWS_ACCESS_KEY_ID }}
    AWS_SECRET_ACCESS_KEY: ${{ secrets.AWS_SECRET_ACCESS_KEY }}
    AWS_DEFAULT_REGION: us-east-1

- name: Setup SSH key
  run: |
    mkdir -p ~/.ssh
    echo "${{ secrets.EC2_SSH_KEY }}" > ~/.ssh/deploy_key.pem
    chmod 600 ~/.ssh/deploy_key.pem
    ssh-keyscan -H ${{ secrets.EC2_HOST }} >> ~/.ssh/known_hosts

    # Add the SSH key to the known_hosts file
    ssh-keyscan -H ${{ secrets.EC2_HOST }} >> ~/.ssh/known_hosts
  env:
    AWS_ACCESS_KEY_ID: ${{ secrets.AWS_ACCESS_KEY_ID }}
    AWS_SECRET_ACCESS_KEY: ${{ secrets.AWS_SECRET_ACCESS_KEY }}
    AWS_DEFAULT_REGION: us-east-1
    EC2_HOST: ${{ secrets.EC2_HOST }}

- name: SSH into EC2
  run: |
    ssh -i ~/.ssh/deploy_key.pem ubuntu@${{ secrets.EC2_HOST }}
  env:
    AWS_ACCESS_KEY_ID: ${{ secrets.AWS_ACCESS_KEY_ID }}
    AWS_SECRET_ACCESS_KEY: ${{ secrets.AWS_SECRET_ACCESS_KEY }}
    AWS_DEFAULT_REGION: us-east-1
    EC2_HOST: ${{ secrets.EC2_HOST }}

```

10. Workflows Completed

Basic CI/CD with GitHub Actions

