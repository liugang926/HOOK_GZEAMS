# GZEAMS Project Rules Plugin

This plugin enforces GZEAMS-specific coding standards and workflows.

## Features

- **Code Standards Validation**: Enforces BaseModel inheritance, English-only comments, soft delete patterns
- **PRD Validation**: Validates PRD documents against project standards
- **Feature Development**: Structured workflow for new features
- **Git Automation**: Smart commit and PR workflows

## Commands

- `/gzeams:review` - Review code against GZEAMS standards
- `/gzeams:prd-check` - Validate PRD document
- `/gzeams:feature` - Start a new feature with proper structure

## Hooks

- **PreEdit**: Warns about Chinese comments
- **PreCommit**: Validates BaseModel inheritance
- **PreToolUse**: Validates bash commands before execution
