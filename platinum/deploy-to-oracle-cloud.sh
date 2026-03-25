# Platinum Tier - Cloud VM Deployment (Oracle Cloud Free Tier)
# Personal AI Employee - Always-On 24/7 Deployment
#
# This script deploys the AI Employee to Oracle Cloud Free VM
# Prerequisites:
# - Oracle Cloud account (free tier)
# - OCI CLI installed
# - SSH key pair
#
# Usage:
#   ./deploy-to-oracle-cloud.sh

#!/bin/bash

set -e

# Configuration
COMPARTMENT_ID="${OCI_COMPARTMENT_ID:-}"
AVAILABILITY_DOMAIN="${OCI_AVAILABILITY_DOMAIN:-}"
SUBNET_ID="${OCI_SUBNET_ID:-}"
IMAGE_ID="ocid1.image.oc1..aaaaaaaavyh0n0zr6qf3z3z3z3z3z3z3z3z3z3z3z3z3z3z3z3"  # Ubuntu 22.04
SHAPE="VM.Standard.A1.Flex"  # Free tier: 4 OCPU, 24GB RAM
INSTANCE_NAME="ai-employee-cloud"
SSH_PUBLIC_KEY="${HOME}/.ssh/id_rsa.pub"

echo "╔════════════════════════════════════════════════════════╗"
echo "║    PLATINUM TIER - Oracle Cloud Deployment            ║"
echo "╚════════════════════════════════════════════════════════╝"

# Check OCI CLI
if ! command -v oci &> /dev/null; then
    echo "Error: OCI CLI not installed. Install from:"
    echo "  https://docs.oracle.com/en-us/iaas/Content/API/Concepts/cliconcepts.htm"
    exit 1
fi

# Create VCN if not exists
echo "Creating VCN..."
VCN_ID=$(oci network vcn create \
    --compartment-id "$COMPARTMENT_ID" \
    --display-name "ai-employee-vcn" \
    --dns-label "aiemployee" \
    --cidr-block "10.0.0.0/16" \
    --wait-for-state "AVAILABLE" \
    --query "data.id" \
    --raw-output)

echo "VCN Created: $VCN_ID"

# Create Internet Gateway
echo "Creating Internet Gateway..."
IG_ID=$(oci network internet-gateway create \
    --compartment-id "$COMPARTMENT_ID" \
    --vcn-id "$VCN_ID" \
    --display-name "ai-employee-ig" \
    --is-enabled true \
    --wait-for-state "AVAILABLE" \
    --query "data.id" \
    --raw-output)

# Create Route Table
echo "Creating Route Table..."
ROUTE_TABLE_ID=$(oci network route-table create \
    --compartment-id "$COMPARTMENT_ID" \
    --vcn-id "$VCN_ID" \
    --display-name "ai-employee-rt" \
    --route-rules "[{\"destination\":\"0.0.0.0/0\",\"destinationType\":\"CIDR\",\"networkEntityId\":\"$IG_ID\"}]" \
    --wait-for-state "AVAILABLE" \
    --query "data.id" \
    --raw-output)

# Create Security List
echo "Creating Security List..."
SECURITY_LIST_ID=$(oci network security-list create \
    --compartment-id "$COMPARTMENT_ID" \
    --vcn-id "$VCN_ID" \
    --display-name "ai-employee-sg" \
    --ingress-security-rules '[{"source":"0.0.0.0/0","protocol":"6","tcpOptions":{"destinationPortRange":{"min":22,"max":22}}},{"source":"0.0.0.0/0","protocol":"6","tcpOptions":{"destinationPortRange":{"min":80,"max":80}}},{"source":"0.0.0.0/0","protocol":"6","tcpOptions":{"destinationPortRange":{"min":443,"max":443}}},{"source":"0.0.0.0/0","protocol":"6","tcpOptions":{"destinationPortRange":{"min":8069,"max":8069}}}]' \
    --egress-security-rules '[{"destination":"0.0.0.0/0","protocol":"all"}]' \
    --wait-for-state "AVAILABLE" \
    --query "data.id" \
    --raw-output)

# Create Subnet
echo "Creating Subnet..."
SUBNET_ID=$(oci network subnet create \
    --compartment-id "$COMPARTMENT_ID" \
    --vcn-id "$VCN_ID" \
    --display-name "ai-employee-subnet" \
    --cidr-block "10.0.1.0/24" \
    --route-table-id "$ROUTE_TABLE_ID" \
    --security-list-ids "[$SECURITY_LIST_ID]" \
    --wait-for-state "AVAILABLE" \
    --query "data.id" \
    --raw-output)

# Launch Instance
echo "Launching VM Instance ($SHAPE)..."
INSTANCE_ID=$(oci compute instance launch \
    --compartment-id "$COMPARTMENT_ID" \
    --availability-domain "$AVAILABILITY_DOMAIN" \
    --display-name "$INSTANCE_NAME" \
    --image-id "$IMAGE_ID" \
    --shape "$SHAPE" \
    --subnet-id "$SUBNET_ID" \
    --assign-public-ip true \
    --ssh-authorized-keys-file "$SSH_PUBLIC_KEY" \
    --metadata file:///dev/stdin <<EOF
{
  "user_data": "$(base64 -w0 <<USERDATA
#!/bin/bash
# Cloud-init script for AI Employee
apt-get update
apt-get install -y docker.io docker-compose git python3 python3-pip

# Add user to docker group
usermod -aG docker ubuntu

# Start Docker
systemctl enable docker
systemctl start docker

# Clone AI Employee repo
cd /home/ubuntu
git clone https://github.com/yourusername/personal-AI-empy.git
cd personal-AI-empy

# Start Odoo stack
docker-compose up -d

# Install Python dependencies
pip3 install -r AI_Employee_Vault/watchers/requirements.txt
USERDATA
)"
}
EOF
    --wait-for-state "RUNNING" \
    --query "data.id" \
    --raw-output)

echo "Instance Launched: $INSTANCE_ID"

# Get Public IP
PUBLIC_IP=$(oci compute instance get \
    --instance-id "$INSTANCE_ID" \
    --query "data.publicIp" \
    --raw-output)

echo ""
echo "╔════════════════════════════════════════════════════════╗"
echo "║          DEPLOYMENT COMPLETE!                          ║"
echo "╚════════════════════════════════════════════════════════╝"
echo ""
echo "Instance Name: $INSTANCE_NAME"
echo "Public IP: $PUBLIC_IP"
echo "SSH: ssh -i $SSH_PUBLIC_KEY ubuntu@$PUBLIC_IP"
echo ""
echo "Next Steps:"
echo "1. SSH into the VM: ssh -i ~/.ssh/id_rsa ubuntu@$PUBLIC_IP"
echo "2. Verify Docker: docker ps"
echo "3. Verify Odoo: curl http://localhost:8069"
echo "4. Configure vault sync (see PLATINUM_SYNC.md)"
