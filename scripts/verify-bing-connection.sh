#!/bin/bash

# Script to verify Bing Grounding connection is properly configured
# Usage: ./scripts/verify-bing-connection.sh

set -e

echo "🔍 Verifying Bing Grounding Connection Configuration"
echo "=================================================="
echo ""

# Check if azd is installed
if ! command -v azd &> /dev/null; then
    echo "❌ Azure Developer CLI (azd) is not installed"
    echo "   Install from: https://aka.ms/azd"
    exit 1
fi

echo "✅ Azure Developer CLI found"

# Get environment variables
echo ""
echo "📋 Checking deployment outputs..."

ACCOUNT_NAME=$(azd env get-values | grep AZURE_AI_ACCOUNT_NAME | cut -d'=' -f2 | tr -d '"')
PROJECT_NAME=$(azd env get-values | grep AZURE_AI_PROJECT_NAME | cut -d'=' -f2 | tr -d '"')
BING_CONNECTION_NAME=$(azd env get-values | grep BING_CONNECTION_NAME | cut -d'=' -f2 | tr -d '"')
BING_RESOURCE_NAME=$(azd env get-values | grep BING_RESOURCE_NAME | cut -d'=' -f2 | tr -d '"')
APP_URI=$(azd env get-values | grep AZURE_APP_URI | cut -d'=' -f2 | tr -d '"')

if [ -z "$ACCOUNT_NAME" ] || [ -z "$PROJECT_NAME" ] || [ -z "$BING_CONNECTION_NAME" ]; then
    echo "❌ Missing deployment outputs. Have you run 'azd up' yet?"
    exit 1
fi

echo "✅ Deployment outputs found:"
echo "   AI Account: $ACCOUNT_NAME"
echo "   AI Project: $PROJECT_NAME"
echo "   Bing Connection: $BING_CONNECTION_NAME"
echo "   Bing Resource: $BING_RESOURCE_NAME"
echo "   App URI: $APP_URI"

# Check if .env file exists
echo ""
echo "📄 Checking local configuration..."

if [ ! -f ".env" ]; then
    echo "⚠️  No .env file found (this is OK if running in Container App)"
else
    echo "✅ .env file exists"
    if grep -q "BING_CONNECTION_NAME" .env; then
        LOCAL_CONNECTION=$(grep BING_CONNECTION_NAME .env | cut -d'=' -f2)
        echo "   Local BING_CONNECTION_NAME: $LOCAL_CONNECTION"
        
        if [ "$LOCAL_CONNECTION" == "$BING_CONNECTION_NAME" ]; then
            echo "   ✅ Local configuration matches deployment"
        else
            echo "   ⚠️  Local configuration differs from deployment"
            echo "      Consider updating .env with: BING_CONNECTION_NAME=$BING_CONNECTION_NAME"
        fi
    else
        echo "   ⚠️  BING_CONNECTION_NAME not set in .env"
        echo "      Add: BING_CONNECTION_NAME=$BING_CONNECTION_NAME"
    fi
fi

# Verify with Azure CLI
echo ""
echo "🔐 Verifying Azure resources..."

if ! command -v az &> /dev/null; then
    echo "⚠️  Azure CLI (az) not found - skipping resource verification"
    echo "   Install from: https://aka.ms/azure-cli"
else
    echo "✅ Azure CLI found"
    
    # Check if logged in
    if ! az account show &> /dev/null; then
        echo "❌ Not logged in to Azure CLI. Run: az login"
        exit 1
    fi
    
    # Get resource group
    RESOURCE_GROUP=$(az resource list --name "$ACCOUNT_NAME" --query "[0].resourceGroup" -o tsv 2>/dev/null)
    
    if [ -z "$RESOURCE_GROUP" ]; then
        echo "❌ Could not find AI Foundry account in current subscription"
        exit 1
    fi
    
    echo "   Resource Group: $RESOURCE_GROUP"
    
    # Check Bing resource
    echo ""
    echo "🔍 Checking Bing Grounding resource..."
    
    if az resource show --name "$BING_RESOURCE_NAME" --resource-type "Microsoft.Bing/accounts" --resource-group "$RESOURCE_GROUP" &> /dev/null; then
        echo "✅ Bing Grounding resource found: $BING_RESOURCE_NAME"
        
        BING_SKU=$(az resource show --name "$BING_RESOURCE_NAME" --resource-type "Microsoft.Bing/accounts" --resource-group "$RESOURCE_GROUP" --query "sku.name" -o tsv 2>/dev/null)
        echo "   SKU: $BING_SKU"
    else
        echo "❌ Bing Grounding resource not found: $BING_RESOURCE_NAME"
        exit 1
    fi
    
    # Check AI Foundry connection
    echo ""
    echo "🔗 Checking AI Foundry connection..."
    echo "   (Note: Connection details require Azure AI Foundry API)"
    echo "   Manual verification:"
    echo "   1. Go to: https://portal.azure.com"
    echo "   2. Navigate to: $ACCOUNT_NAME"
    echo "   3. Check 'Connections' section"
    echo "   4. Verify 'bing-grounding' connection exists"
fi

# Test application accessibility
echo ""
echo "🌐 Testing application accessibility..."

if [ -n "$APP_URI" ]; then
    if curl -s -o /dev/null -w "%{http_code}" "$APP_URI" | grep -q "200\|302\|301"; then
        echo "✅ Application is accessible at: $APP_URI"
    else
        echo "⚠️  Application may not be ready yet at: $APP_URI"
        echo "   Wait a few minutes for the container to start"
    fi
else
    echo "⚠️  Application URI not found in deployment outputs"
fi

echo ""
echo "=================================================="
echo "✨ Verification complete!"
echo ""
echo "Next steps:"
echo "1. Visit the Azure Portal to verify the connection manually"
echo "2. Access the application at: $APP_URI"
echo "3. Test web search functionality with Venue Specialist or Catering Coordinator"
echo ""
echo "For troubleshooting, see: infra/README.md"
