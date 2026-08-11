$ErrorActionPreference = "Stop"
$aws = "C:\Program Files\Amazon\AWSCLIV2\aws.exe"
$Region = "ap-southeast-2"
$KeyPairName = "insurance-rag-key"
$SecurityGroupName = "insurance-rag-sg"

# 1. Create KeyPair
Write-Host "Creating KeyPair..."
try {
    $keyPair = & $aws ec2 create-key-pair --key-name $KeyPairName --query 'KeyMaterial' --output text --region $Region
    if ($keyPair -and $LASTEXITCODE -eq 0) {
        Set-Content -Path ".\$KeyPairName.pem" -Value $keyPair
        Write-Host "Saved key to $KeyPairName.pem"
    }
} catch {
    Write-Host "KeyPair might already exist, continuing..."
}

# 2. Create Security Group
Write-Host "Creating Security Group..."
try {
    $sgId = & $aws ec2 create-security-group --group-name $SecurityGroupName --description "Allow 8000 and 22" --query 'GroupId' --output text --region $Region
    if ($sgId -and $LASTEXITCODE -eq 0) {
        Write-Host "Authorizing ports..."
        & $aws ec2 authorize-security-group-ingress --group-id $sgId --protocol tcp --port 22 --cidr 0.0.0.0/0 --region $Region
        & $aws ec2 authorize-security-group-ingress --group-id $sgId --protocol tcp --port 8000 --cidr 0.0.0.0/0 --region $Region
    }
} catch {
    Write-Host "Security Group might already exist, fetching it..."
    $sgId = & $aws ec2 describe-security-groups --group-names $SecurityGroupName --query 'SecurityGroups[0].GroupId' --output text --region $Region
}

# 3. Get latest Ubuntu AMI
Write-Host "Fetching Ubuntu AMI..."
$amiId = & $aws ec2 describe-images --owners 099720109477 --filters "Name=name,Values=ubuntu/images/hvm-ssd/ubuntu-jammy-22.04-amd64-server-*" "Name=state,Values=available" --query "sort_by(Images, &CreationDate)[-1].ImageId" --output text --region $Region

# 4. UserData Script
$envContent = @"
GOOGLE_API_KEY=YOUR_GOOGLE_API_KEY
OPENROUTER_API_KEY=YOUR_OPENROUTER_API_KEY
PHASE2_ENVIRONMENT=development
PHASE2__LLM__PROVIDER=openrouter
PHASE2__LLM__API_KEY=YOUR_OPENROUTER_API_KEY
PHASE2__LLM__MODEL_NAME=openai/gpt-4o-mini
"@

$userData = @"
#!/bin/bash
apt-get update
apt-get install -y docker.io docker-compose git
systemctl start docker
systemctl enable docker
usermod -aG docker ubuntu
cd /home/ubuntu
git clone https://github.com/Vk18dh/insurance-rag-system.git
cd insurance-rag-system
cat << 'EOF' > .env
$envContent
EOF
chown -R ubuntu:ubuntu /home/ubuntu/insurance-rag-system
docker-compose up -d backend chromadb
"@

$Bytes = [System.Text.Encoding]::UTF8.GetBytes($userData)
$EncodedUserData = [System.Convert]::ToBase64String($Bytes)

# 5. Launch Instance
Write-Host "Launching EC2 Instance ($amiId)..."
$instanceId = & $aws ec2 run-instances --image-id $amiId --count 1 --instance-type t3.small --key-name $KeyPairName --security-group-ids $sgId --user-data $EncodedUserData --query 'Instances[0].InstanceId' --output text --region $Region

Write-Host "Waiting for instance to be running (this may take a minute)..."
& $aws ec2 wait instance-running --instance-ids $instanceId --region $Region

$publicIp = & $aws ec2 describe-instances --instance-ids $instanceId --query 'Reservations[0].Instances[0].PublicIpAddress' --output text --region $Region

Write-Host ""
Write-Host "=========================================="
Write-Host "DEPLOYMENT SUCCESSFUL!"
Write-Host "Backend API URL: http://${publicIp}:8000"
Write-Host "=========================================="
