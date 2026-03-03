#!/usr/bin/env node
/**
 * Related table metadata-driven audit guard.
 *
 * Goal:
 * - Ensure related table renderers do not regress to object-specific hardcoded templates.
 * - Enforce metadata-driven column source in RelatedObjectTable.
 */
import { execSync } from 'node:child_process'
import fs from 'node:fs'
import path from 'node:path'

const repoRoot = path.resolve(process.cwd(), '..')
const frontendRoot = path.resolve(process.cwd())
const args = process.argv.slice(2)
const argSet = new Set(args)

const changedOnly = argSet.has('--changed') || !argSet.has('--all')
const failOnIssues = argSet.has('--fail-on-issues')
const isCi = process.env.CI === 'true'

const reportArgIndex = args.findIndex((arg) => arg === '--report')
const reportPath =
  reportArgIndex >= 0 && args[reportArgIndex + 1]
    ? String(args[reportArgIndex + 1]).trim()
    : ''

const TARGET_FILES = new Set([
  'frontend/src/components/common/RelatedObjectTable.vue',
  'frontend/src/components/common/BaseDetailPage.vue',
  'frontend/src/components/common/DynamicDetailPage.vue',
  'frontend/src/components/designer/WysiwygLayoutDesigner.vue',
  'frontend/src/components/engine/fields/SubTableField.vue',
])

const normalizePath = (relativePath) => relativePath.replace(/\\/g, '/')

const getCandidateFiles = () => {
  const fromAll = () =>
    execSync('git ls-files "frontend/src/**/*.*"', { cwd: repoRoot, encoding: 'utf8' })
      .split(/\r?\n/)
      .map((line) => line.trim())
      .filter(Boolean)

  const fromChangedInCi = () =>
    execSync('git diff-tree --no-commit-id --name-only -r HEAD', {
      cwd: repoRoot,
      encoding: 'utf8',
      stdio: ['ignore', 'pipe', 'ignore'],
    })
      .split(/\r?\n/)
      .map((line) => line.trim())
      .filter(Boolean)

  const fromChangedLocal = () =>
    execSync('git status --porcelain', {
      cwd: repoRoot,
      encoding: 'utf8',
      stdio: ['ignore', 'pipe', 'ignore'],
    })
      .split(/\r?\n/)
      .filter((line) => line && line.length >= 4)
      .map((line) => line.slice(3).trim())
      .map((line) => line.replace(/^"|"$/g, ''))
      .filter(Boolean)

  const files = changedOnly
    ? (isCi ? fromChangedInCi() : fromChangedLocal())
    : fromAll()

  return [...new Set(files)]
    .map(normalizePath)
    .filter((file) => TARGET_FILES.has(file))
}

const pushIssue = (issues, file, rule, detail) => {
  issues.push({
    file: normalizePath(path.relative(frontendRoot, path.resolve(repoRoot, file))),
    rule,
    detail,
  })
}

const scanRelatedObjectTable = (content, file, issues) => {
  const disallowedPatterns = [
    {
      rule: 'no-legacy-related-template-factory',
      pattern: /\bgetCommonDisplayFields\s*\(/,
      detail: 'Legacy object-specific column factory detected.',
    },
    {
      rule: 'no-object-template-map',
      pattern: /\bfieldMap\s*:\s*Record<\s*string\s*,\s*TableColumn\[\]\s*>/,
      detail: 'Object template map detected; related table must be metadata-driven.',
    },
    {
      rule: 'no-hardcoded-object-columns',
      pattern: /\b(Maintenance|AssetLoan|AssetPickup|AssetReturn|InventoryTaskItem)\s*:/,
      detail: 'Known hardcoded object column template detected.',
    },
  ]

  for (const entry of disallowedPatterns) {
    if (entry.pattern.test(content)) {
      pushIssue(issues, file, entry.rule, entry.detail)
    }
  }

  const requiredPatterns = [
    {
      rule: 'require-related-fields-metadata-endpoint',
      pattern: /\/system\/objects\/\$\{relatedObjectCode\.value\}\/fields\//,
      detail: 'Missing metadata endpoint call for related object list fields.',
    },
    {
      rule: 'require-list-context-for-related-columns',
      pattern: /context:\s*['"`]list['"`]/,
      detail: 'Missing list context when requesting related object field metadata.',
    },
  ]

  for (const entry of requiredPatterns) {
    if (!entry.pattern.test(content)) {
      pushIssue(issues, file, entry.rule, entry.detail)
    }
  }
}

const scanFile = (file, issues) => {
  const fullPath = path.resolve(repoRoot, file)
  if (!fs.existsSync(fullPath)) return
  const content = fs.readFileSync(fullPath, 'utf8')

  if (normalizePath(file) === 'frontend/src/components/common/RelatedObjectTable.vue') {
    scanRelatedObjectTable(content, file, issues)
  }
}

const writeReport = (issues, filesScanned) => {
  if (!reportPath) return
  const reportAbs = path.resolve(frontendRoot, reportPath)
  const nowIso = new Date().toISOString()
  const lines = [
    '# Related Table Metadata Audit Report',
    '',
    `- Generated at: ${nowIso}`,
    `- Files scanned: ${filesScanned}`,
    `- Issues: ${issues.length}`,
    '',
    '## Result',
    '',
    issues.length === 0 ? '- PASS' : '- FAIL',
    '',
  ]

  if (issues.length > 0) {
    lines.push('## Issues', '')
    for (const issue of issues) {
      lines.push(`- ${issue.file} [${issue.rule}] ${issue.detail}`)
    }
  }

  fs.mkdirSync(path.dirname(reportAbs), { recursive: true })
  fs.writeFileSync(reportAbs, `${lines.join('\n')}\n`, 'utf8')
}

const run = () => {
  const files = getCandidateFiles()
  if (files.length === 0) {
    console.log('[related-metadata-audit] No candidate files to scan.')
    writeReport([], 0)
    return
  }

  const issues = []
  for (const file of files) {
    scanFile(file, issues)
  }

  writeReport(issues, files.length)

  if (issues.length > 0) {
    console.error('\n[related-metadata-audit] Found issues:')
    for (const issue of issues) {
      console.error(`- ${issue.file} [${issue.rule}] ${issue.detail}`)
    }
    if (failOnIssues) {
      process.exit(1)
    }
  }

  const mode = changedOnly ? 'changed' : 'all'
  console.log(
    `[related-metadata-audit] Completed (${mode} mode, ${files.length} files, ${issues.length} issues).`
  )
}

run()

