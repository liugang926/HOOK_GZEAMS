# GitHub Branch Protection Configuration Guide

## Document Information
| Project | Description |
|---------|-------------|
| Document Version | v1.0 |
| Created Date | 2026-01-26 |
| Related Task | Task 9: Optional Branch Protection Configuration |
| CI/CD Phase | Phase 3 - GitHub Actions CI/CD |

---

## Overview

### What is Branch Protection?

Branch protection is a GitHub feature that enforces certain rules before code can be merged into protected branches (typically `master` or `main`). This ensures code quality and prevents broken or untested code from being merged into the main codebase.

### Why Configure Branch Protection?

By enabling branch protection rules, you:

- **Prevent Broken Builds**: Only code that passes CI tests can be merged
- **Enforce Code Review**: Require pull request reviews (optional)
- **Maintain Code Quality**: Ensure all status checks pass before merging
- **Protect Production**: Safeguard the main branch from direct commits
- **Automate Quality Gates**: Leverage your CI/CD pipeline as a gatekeeper

---

## Prerequisites

Before configuring branch protection, ensure:

1. **CI Workflow is Active**: Your GitHub Actions workflow (`.github/workflows/ci.yml`) is committed and pushed
2. **Workflow has Run Successfully**: At least one CI run has completed successfully
3. **Repository Owner Access**: You have admin/owner permissions for the repository

---

## Step-by-Step Configuration

### Step 1: Navigate to Repository Settings

1. Visit your repository on GitHub:
   ```
   https://github.com/liugang926/HOOK_GZEAMS
   ```

2. Click on the **Settings** tab at the top of the repository page

3. In the left sidebar, click on **Branches** under the "Code and automation" section

### Step 2: Add Branch Protection Rule

1. Click the **"Add branch protection rule"** button

2. Configure the rule settings:

   **Branch name pattern:**
   ```
   master
   ```
   Or if your main branch is named `main`:
   ```
   main
   ```

3. **Enable the following settings:**

   #### A. Require status checks to pass before merging
   - [x] **Require status checks to pass before merging**
   - [x] **Require branches to be up to date before merging**

   This ensures:
   - The branch being merged has the latest changes from the target branch
   - All CI status checks have passed

   **Required status checks:**
   - Search for and select: **`CI Status Check`**
     - This is the job name defined in `.github/workflows/ci.yml`
     - The actual job name in the workflow is: **`test`**
     - You may see it listed as: `test` or `CI Status Check`

   #### B. Optional Additional Protections (Recommended)

   - [ ] **Require pull request reviews before merging**
     - Specify the number of approving reviews (e.g., 1)
     - Dismiss stale reviews when new commits are pushed

   - [ ] **Require conversation resolution before merging**
     - All comments on the pull request must be resolved

   - [x] **Do not allow bypassing the above settings**
     - Prevents administrators from bypassing rules

   - [x] **Restrict who can push to matching branches**
     - Only allow specific people or teams to push directly

4. Click **"Create"** or **"Save changes"** to apply the rule

---

## Verification

### Verify Branch Protection is Active

1. Try to create a pull request with a failing test
2. You should see a message indicating that the status check must pass before merging
3. The "Merge" button should be disabled until all checks pass

### Example: Protected Branch UI

When branch protection is active, you'll see:

- **Status checks required** badge on the pull request
- **All checks must pass** notification
- **Merge button disabled** until CI passes

---

## CI Workflow Job Names Reference

From your `.github/workflows/ci.yml` file:

```yaml
jobs:
  test:
    name: CI Status Check
    runs-on: ubuntu-latest
    # ... job steps
```

**Job Name**: `CI Status Check` (this is what you'll see in GitHub UI)
**Job ID**: `test` (internal workflow identifier)

When configuring branch protection, look for the status check named:
- **`CI Status Check`** or
- **`test`**

---

## Troubleshooting

### Status Check Not Appearing

If you don't see the CI status check in the list:

1. **Check if the workflow has run**:
   - Go to the "Actions" tab in your repository
   - Verify that at least one workflow run has completed

2. **Check workflow status**:
   - Ensure the workflow is not disabled
   - Verify there are no syntax errors in `.github/workflows/ci.yml`

3. **Wait a few minutes**:
   - GitHub may take a few minutes to register new status checks

### Bypassing Protection Rules

If you need to bypass protection rules temporarily:

1. Go to Settings → Branches
2. Edit the branch protection rule
3. Uncheck "Do not allow bypassing the above settings"
4. Admins can now bypass rules (use with caution)

---

## Best Practices

### 1. Start Simple
- Begin with just status check requirements
- Add pull request reviews later if needed

### 2. Keep CI Fast
- Status checks should complete in under 10 minutes
- Long-running checks discourage developers

### 3. Monitor Protected Branches
- Review who is bypassing rules (if enabled)
- Adjust rules based on team feedback

### 4. Use Branch Protection with Semantic Versioning
- Protect `master`/`main` branch
- Allow direct commits to feature branches
- Use pull requests for merging to protected branches

---

## Integration with Your CI/CD Pipeline

Your branch protection rule integrates with the workflow from Task 8:

```
.git/
├── .github/
│   └── workflows/
│       └── ci.yml              # Defines the CI Status Check job
│
└── [branch protection configured via GitHub UI]
```

### Workflow:

1. Developer creates a pull request
2. GitHub Actions automatically runs `CI Status Check` job
3. Branch protection rule blocks merging until:
   - Status check passes
   - Branch is up to date
4. Once checks pass, pull request can be merged

---

## Security Considerations

### Recommended Settings

- [x] **Require status checks** - Ensures code quality
- [x] **Require up-to-date branches** - Prevents merge conflicts
- [ ] **Require PR reviews** - Add when team is ready
- [x] **Restrict direct pushes** - Force use of pull requests
- [x] **Disable bypassing** - Prevent admin rule circumvention

### Who Can Push to Protected Branches

By default, restrict to:
- Repository owners
- Specific teams
- Automated deployment tools (if using CD)

---

## Rollback Procedure

If branch protection causes issues:

1. **Temporarily Disable**:
   - Go to Settings → Branches
   - Edit the protection rule
   - Uncheck all requirements
   - Save

2. **Fix CI Issues**:
   - Debug failing tests
   - Fix workflow syntax errors

3. **Re-enable Protection**:
   - Re-enable the settings
   - Create a new pull request to verify

---

## Additional Resources

- [GitHub Branch Protection Documentation](https://docs.github.com/en/repositories/configuring-branches-and-merges-in-your-repository/defining-the-mergeability-of-pull-requests/about-protected-branches)
- [About Status Checks](https://docs.github.com/en/pull-requests/collaborating-with-pull-requests/collaborating-on-repositories-with-code-quality-features/about-status-checks)
- [CI/CD Implementation Guide](./ci-implementation-guide.md)

---

## Next Steps After Configuration

Once branch protection is enabled:

1. **Test the Workflow**:
   - Create a test pull request
   - Verify CI runs automatically
   - Confirm merge button is disabled until CI passes

2. **Document Team Processes**:
   - Update team documentation
   - Train developers on new workflow

3. **Monitor and Adjust**:
   - Review protection rule effectiveness
   - Adjust settings based on team feedback

---

## Summary

Branch protection rules are the final piece of your CI/CD pipeline that ensures:

- Code quality is maintained
- All tests pass before merging
- The main branch remains stable
- Team collaboration is enforced

While this configuration is manual and done via the GitHub UI, it's a critical step in maintaining code quality and preventing broken code from reaching your main branch.

---

**Note**: This is an optional but highly recommended configuration for production repositories. It completes your CI/CD implementation by adding automated quality gates.
