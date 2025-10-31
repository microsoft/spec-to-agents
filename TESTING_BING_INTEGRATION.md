# Testing Bing Grounding Integration

This guide provides step-by-step instructions for testing the newly added Bing Grounding connection.

## Quick Start

```bash
# 1. Deploy infrastructure
azd up

# 2. Verify deployment
./scripts/verify-bing-connection.sh

# 3. Test the application
# Visit the URL provided by: azd show
```

## Detailed Testing Steps

### 1. Deploy Infrastructure

```bash
# Navigate to repository root
cd spec-to-agents

# Deploy everything (infrastructure + application)
azd up
```

**What to expect:**
- Prompt for environment name (e.g., `dev`, `test`)
- Prompt for Azure region (choose from: eastus2, westus, westus2, etc.)
- Deployment takes ~5-10 minutes
- Creates: AI Foundry, Bing Grounding, Container App, and supporting resources

**Outputs to note:**
```
AZURE_AI_ACCOUNT_NAME=foundry<token>
AZURE_AI_PROJECT_NAME=project<token>
BING_RESOURCE_NAME=bing-<token>
BING_CONNECTION_NAME=bing-grounding
AZURE_APP_URI=https://ca-<token>.azurecontainerapps.io
```

### 2. Automated Verification

```bash
# Run the verification script
./scripts/verify-bing-connection.sh
```

**What it checks:**
- ✅ Deployment outputs are present
- ✅ Environment variables configured correctly
- ✅ Bing Grounding resource exists in Azure
- ✅ Application is accessible
- ✅ Configuration matches between local and deployment

**Expected output:**
```
🔍 Verifying Bing Grounding Connection Configuration
==================================================

✅ Azure Developer CLI found

📋 Checking deployment outputs...
✅ Deployment outputs found:
   AI Account: foundry<token>
   AI Project: project<token>
   Bing Connection: bing-grounding
   Bing Resource: bing-<token>
   App URI: https://ca-<token>.azurecontainerapps.io

...

✨ Verification complete!
```

### 3. Manual Azure Portal Verification

1. **Open Azure Portal**: https://portal.azure.com
2. **Navigate to AI Foundry Account**:
   - Search for the AI account name from deployment outputs
   - Click on the resource
3. **Check Connections**:
   - Go to Settings → Connections
   - Verify `bing-grounding` connection exists
   - Check properties:
     - Category: ApiKey
     - Auth Type: ApiKey
     - Target: https://api.bing.microsoft.com/
     - Status: Connected
4. **Check Bing Resource**:
   - Navigate to Resource Groups
   - Find the resource group (usually `rg-<env-name>`)
   - Locate the Bing resource (`bing-<token>`)
   - Verify SKU: G1 (Grounding)

### 4. Application Testing

#### Access the Application

```bash
# Get the application URL
azd show
# Or extract from environment
azd env get-values | grep AZURE_APP_URI
```

Visit the URL in your browser.

#### Test Web Search Functionality

Submit an event planning request that requires web search. Examples:

**Example 1: Venue Search**
```
Plan a tech conference in San Francisco for 200 people.
Budget: $50,000
Date: June 15-17, 2025
Need a venue with excellent AV equipment and nearby hotels.
```

**Expected behavior:**
- Venue Specialist agent activates
- Agent performs web searches for SF conference venues
- Response includes real venue information with sources/citations
- Look for phrases like "According to..." or "Based on search results..."

**Example 2: Catering Search**
```
Plan a corporate gala dinner for 100 people in Chicago.
Budget: $15,000
Need upscale catering with vegetarian and gluten-free options.
```

**Expected behavior:**
- Catering Coordinator agent activates
- Agent searches for Chicago catering companies
- Response includes actual catering options with pricing
- Citations reference real catering services

#### What to Look For

✅ **Web Search Success Indicators:**
- Agents mention searching for information
- Responses include real business names, addresses, prices
- Citations/sources are included (e.g., "Source: bing.com/...")
- Information is current (not generic or outdated)

❌ **Web Search Issues:**
- Generic responses without specific details
- No citations or sources mentioned
- Error messages about unavailable tools
- Outdated information

### 5. DevUI Testing (Optional)

For interactive testing with the DevUI interface:

```bash
# If running locally with .env configured
uv run app
```

This starts the DevUI server where you can:
- See real-time agent orchestration
- Watch web search tool invocations
- Inspect agent reasoning and tool calls
- Debug connection issues

## Troubleshooting

### Issue: "Bing connection not found"

**Check:**
1. Verify `BING_CONNECTION_NAME` environment variable in Container App
2. Confirm connection exists in AI Foundry portal
3. Check Container App logs in Azure Portal

**Fix:**
```bash
# Redeploy application
azd deploy
```

### Issue: Web searches return errors

**Check:**
1. Bing resource status in Azure Portal
2. API key validity (connection credentials)
3. Application Insights logs for detailed errors

**Fix:**
```bash
# Check Container App logs
az containerapp logs show --name <app-name> --resource-group <rg-name>
```

### Issue: Verification script fails

**Common causes:**
- Not logged in to Azure CLI: `az login`
- Wrong subscription selected: `az account set -s <subscription-id>`
- Infrastructure not deployed yet: `azd up`

## Testing Checklist

Use this checklist to verify complete integration:

- [ ] Infrastructure deployed successfully (`azd up` completed)
- [ ] Verification script passes all checks
- [ ] `bing-grounding` connection visible in Azure Portal
- [ ] Bing resource exists with SKU G1
- [ ] Container App environment has `BING_CONNECTION_NAME` variable
- [ ] Application is accessible at provided URL
- [ ] Venue Specialist can search for venues (test with example)
- [ ] Catering Coordinator can search for catering (test with example)
- [ ] Agent responses include citations/sources from web search
- [ ] No errors in Application Insights logs related to Bing

## Success Criteria

The integration is successful when:

1. ✅ All infrastructure deploys without errors
2. ✅ Verification script reports no issues
3. ✅ Agents successfully perform web searches
4. ✅ Responses include real-time information with citations
5. ✅ No errors in monitoring/logs related to Bing connection

## Next Steps After Testing

Once testing is complete:

1. **Document any issues found** in the GitHub issue
2. **Share test results** with screenshots if possible
3. **Monitor costs** in Azure Cost Management (Bing has per-request fees)
4. **Consider rate limiting** for production use (see `infra/README.md`)

## Additional Resources

- [Infrastructure Documentation](infra/README.md) - Complete infrastructure guide
- [Development Setup](DEV_SETUP.md) - Local development instructions
- [Bing Grounding Docs](https://learn.microsoft.com/en-us/azure/ai-foundry/agents/how-to/tools/bing-grounding) - Official Microsoft documentation
- [Verification Script](scripts/verify-bing-connection.sh) - Automated testing tool

## Questions or Issues?

If you encounter problems:

1. Check `infra/README.md` troubleshooting section
2. Review Application Insights logs in Azure Portal
3. Run verification script with verbose output
4. Check Container App logs: `az containerapp logs show`
5. Open an issue in the repository with:
   - Error messages
   - Verification script output
   - Azure Portal screenshots
   - Application logs
