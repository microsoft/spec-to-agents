# Bing Grounding Integration Test Plan

This document outlines the testing steps to verify the Bing grounding connection integration works correctly.

## Prerequisites

- Azure subscription with permissions to create resources
- Azure Developer CLI (azd) installed
- Azure CLI (az) installed
- Access to Azure Portal

## Test Scenarios

### Scenario 1: Deploy with Bing Grounding Enabled (Default)

This tests the default behavior where Bing grounding is deployed.

**Steps:**

1. Clone the repository and navigate to the root directory
   ```bash
   git clone https://github.com/microsoft/spec-to-agents.git
   cd spec-to-agents
   ```

2. Authenticate with Azure
   ```bash
   azd auth login
   ```

3. Deploy the infrastructure (default includes Bing)
   ```bash
   azd up
   ```

4. When prompted:
   - Choose an environment name (e.g., `test-bing-default`)
   - Select an Azure location from the allowed list
   - Select your subscription

**Expected Results:**

- ✅ Deployment completes successfully
- ✅ Bing grounding resource is created (name: `mafbing` or custom name)
- ✅ Container app is deployed and running
- ✅ Outputs include:
  - `BING_GROUNDING_NAME`: Non-empty string
  - `BING_GROUNDING_ID`: Non-empty resource ID
  - `BING_CONNECTION_NAME`: `bing-grounding`

**Verification Steps:**

1. Check deployment outputs:
   ```bash
   azd show
   ```

2. Verify Bing resource in Azure Portal:
   - Navigate to the resource group
   - Confirm Bing Grounding resource exists
   - Check SKU is `G1` and Kind is `Bing.Grounding`

3. Verify connection in AI Foundry:
   - Navigate to AI Foundry account in portal
   - Go to Connections
   - Confirm `bing-grounding` connection exists
   - Verify category is `GroundingWithBingSearch`

4. Verify container app is running:
   - Navigate to Container App in portal
   - Check status is "Running"
   - Access the application URL (from `AZURE_APP_URI` output)
   - Verify devui loads successfully

### Scenario 2: Deploy with Bing Grounding Disabled

This tests explicitly disabling Bing grounding.

**Steps:**

1. Set environment variable to disable Bing:
   ```bash
   azd env set BING_GROUNDING_NAME ""
   ```

2. Deploy the infrastructure:
   ```bash
   azd up
   ```

**Expected Results:**

- ✅ Deployment completes successfully
- ✅ Bing grounding resource is NOT created
- ✅ Container app is deployed and running
- ✅ Outputs:
  - `BING_GROUNDING_NAME`: Empty string
  - `BING_GROUNDING_ID`: Empty string
  - `BING_CONNECTION_NAME`: Empty string

**Verification Steps:**

1. Check deployment outputs:
   ```bash
   azd show
   ```

2. Verify NO Bing resource in Azure Portal:
   - Navigate to the resource group
   - Confirm NO Bing Grounding resource exists

3. Verify NO connection in AI Foundry:
   - Navigate to AI Foundry account in portal
   - Go to Connections
   - Confirm `bing-grounding` connection does NOT exist

4. Verify container app still works:
   - Navigate to Container App in portal
   - Check status is "Running"
   - Access the application URL
   - Verify devui loads successfully (without Bing)

### Scenario 3: Deploy with Custom Bing Resource Name

This tests deploying with a custom Bing resource name.

**Steps:**

1. Set custom Bing resource name:
   ```bash
   azd env set BING_GROUNDING_NAME mycompany-bing
   ```

2. Deploy the infrastructure:
   ```bash
   azd up
   ```

**Expected Results:**

- ✅ Deployment completes successfully
- ✅ Bing grounding resource is created with custom name
- ✅ Container app is deployed and running
- ✅ Outputs include custom resource name

**Verification Steps:**

1. Check deployment outputs:
   ```bash
   azd show
   ```
   - Verify `BING_GROUNDING_NAME` matches `mycompany-bing`

2. Verify Bing resource in Azure Portal:
   - Navigate to the resource group
   - Confirm Bing Grounding resource exists with name `mycompany-bing`

### Scenario 4: Test Agent Web Search Functionality

This tests that agents can actually use the Bing connection.

**Steps:**

1. Access the deployed application URL (from `AZURE_APP_URI`)

2. Create a test agent or use an existing agent

3. Configure the agent to use Bing grounding:
   - The connection should be available as `bing-grounding`

4. Send a query that requires web search:
   - Example: "What's the current weather in Seattle?"
   - Example: "What are the latest news about AI?"

**Expected Results:**

- ✅ Agent can access the Bing connection
- ✅ Agent successfully performs web search
- ✅ Agent returns relevant, up-to-date information
- ✅ Response includes grounding citations (if supported)

### Scenario 5: Infrastructure Validation

This tests the infrastructure validation script.

**Steps:**

1. Run the validation script:
   ```bash
   ./scripts/validate-infra.sh
   ```

**Expected Results:**

- ✅ Script runs without errors
- ✅ Shows validation status for all modules
- ⚠️ Shows expected warnings (BCP081, BCP318, BCP422)
- ✅ Reports "Validation Complete"

## Known Warnings

The following Bicep warnings are expected and do not prevent deployment:

1. **BCP081**: Bing resource type doesn't have schema available
   - This is expected for Bing resources
   - Does not block deployment

2. **BCP318**: Conditional resource may be null
   - This is expected for the `newOrExisting` pattern
   - Handled correctly at runtime

3. **BCP422**: Function called on potentially null resource
   - This is expected for conditional resources
   - Handled correctly at runtime

## Cleanup

After testing, clean up resources:

```bash
azd down
```

Confirm deletion when prompted.

## Troubleshooting

### Issue: Bing deployment fails with quota error

**Solution:**
- Check your subscription quota for Bing resources
- Request quota increase if needed
- Try a different region

### Issue: Connection creation fails

**Solution:**
- Verify AI Foundry account deployed successfully
- Check that Bing resource exists and is accessible
- Review deployment logs for detailed error messages

### Issue: Container app fails to start

**Solution:**
- Check container app logs in Azure Portal
- Verify all environment variables are set correctly
- Ensure container image built successfully

### Issue: Agent can't access Bing connection

**Solution:**
- Verify connection exists in AI Foundry portal
- Check connection name is exactly `bing-grounding`
- Verify agent configuration includes the connection
- Check API key is valid

## Test Results Template

Use this template to document test results:

```markdown
## Test Execution: [Date]

### Environment
- Subscription: [Subscription ID]
- Location: [Azure Region]
- azd version: [Version]

### Scenario 1: Deploy with Bing Grounding Enabled
- [ ] Deployment successful
- [ ] Bing resource created
- [ ] Connection visible in AI Foundry
- [ ] Container app running
- [ ] Outputs correct
- **Notes:** 

### Scenario 2: Deploy with Bing Grounding Disabled
- [ ] Deployment successful
- [ ] No Bing resource
- [ ] No connection in AI Foundry
- [ ] Container app running
- [ ] Outputs correct
- **Notes:**

### Scenario 3: Custom Resource Name
- [ ] Deployment successful
- [ ] Custom name applied
- [ ] Connection created
- **Notes:**

### Scenario 4: Agent Web Search
- [ ] Agent can access connection
- [ ] Web search works
- [ ] Results are relevant
- **Notes:**

### Scenario 5: Validation Script
- [ ] Script runs successfully
- [ ] Expected warnings shown
- **Notes:**

### Overall Result
- [ ] All tests passed
- [ ] Issues found (describe below)

### Issues/Notes:
[Document any issues, errors, or observations here]
```
