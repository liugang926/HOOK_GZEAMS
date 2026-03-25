#!/usr/bin/env bash
# Quick fix for E2E test UUID serialization issue

# This script patches the test files to fix approver_config format

# The test file should use approver_config like this:
# approver_config: {
#     user_id: str(user.id)   # <-- ID as string
# }

# Or for approval nodes:
# approvers: [
#     {type: 'user', user_id: str(user.id) }
# ]

# The validation service expects 'approvers' array, not than 'approver_config'

set -e