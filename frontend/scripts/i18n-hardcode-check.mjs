#!/usr/bin/env node
/**
 * i18n hardcoded text guard (changed-files mode by default).
 *
 * Goal:
 * - Block new hardcoded UI text in changed frontend source files.
 * - Keep legacy stock debt out of this gate (incremental enforcement).
 */
import { execSync } from 'node:child_process'
import fs from 'node:fs'
import path from 'node:path'

const repoRoot = path.resolve(process.cwd(), '..')
const frontendRoot = path.resolve(process.cwd())

const args = new Set(process.argv.slice(2))
const changedOnly = args.has('--changed') || !args.has('--all')
const isCi = process.env.CI === 'true'

const isSourceFile = (filePath) => {
  if (!filePath.startsWith('frontend/src/')) return false
  if (!/\.(vue|ts|tsx|js|jsx|mjs|cjs)$/.test(filePath)) return false
  if (filePath.includes('/locales/')) return false
  if (filePath.includes('/__tests__/')) return false
  if (filePath.includes('/e2e/')) return false
  return true
}

const getCandidateFiles = () => {
  if (!changedOnly) {
    return execSync('git ls-files "frontend/src/**/*.*"', { cwd: repoRoot, encoding: 'utf8' })
      .split(/\r?\n/)
      .map((line) => line.trim())
      .filter(Boolean)
      .filter(isSourceFile)
  }

  // CI: enforce on the latest commit only (incremental gate).
  if (isCi) {
    const latestCommitFiles = execSync('git diff-tree --no-commit-id --name-only -r HEAD', {
      cwd: repoRoot,
      encoding: 'utf8',
      stdio: ['ignore', 'pipe', 'ignore'],
    })
      .split(/\r?\n/)
      .map((line) => line.trim())
      .filter(Boolean)
      .filter(isSourceFile)
    return [...new Set(latestCommitFiles)]
  }

  // Local: enforce on current working tree changes.
  const workingTreeFiles = execSync('git status --porcelain', {
    cwd: repoRoot,
    encoding: 'utf8',
    stdio: ['ignore', 'pipe', 'ignore'],
  })
    .split(/\r?\n/)
    .filter((line) => line && line.length >= 4)
    .map((line) => line.slice(3).trim())
    .map((line) => line.replace(/^"|"$/g, ''))
    .filter(isSourceFile)

  return [...new Set(workingTreeFiles)]
}

const cjkInQuote = /(['"`])(?:\\.|(?!\1).)*[\u3400-\u9FFF]+(?:\\.|(?!\1).)*\1/
const elMessageLiteral =
  /\bElMessage(?:Box)?\s*\.\s*(?:success|error|warning|info|confirm|alert|prompt)\s*\(\s*(['"`])(?:\\.|(?!\1).)+\1/
const i18nIgnoreMarker = 'i18n-hardcode-ignore'

const shouldSkipLine = (line) => {
  const trimmed = line.trim()
  if (!trimmed) return true
  if (trimmed.startsWith('//')) return true
  if (trimmed.startsWith('*')) return true
  if (trimmed.startsWith('import ')) return true
  if (trimmed.includes(i18nIgnoreMarker)) return true
  return false
}

const normalizePath = (relativePath) => relativePath.replace(/\\/g, '/')

const files = getCandidateFiles()
if (files.length === 0) {
  console.log('[i18n-check] No changed source files to scan.')
  process.exit(0)
}

const violations = []
for (const relativePath of files) {
  const fullPath = path.resolve(repoRoot, relativePath)
  if (!fs.existsSync(fullPath)) continue

  const content = fs.readFileSync(fullPath, 'utf8')
  const lines = content.split(/\r?\n/)
  for (let i = 0; i < lines.length; i += 1) {
    const line = lines[i]
    if (shouldSkipLine(line)) continue

    const hasCjkLiteral = cjkInQuote.test(line)
    const hasElMessageLiteral = elMessageLiteral.test(line)
    if (!hasCjkLiteral && !hasElMessageLiteral) continue

    violations.push({
      file: normalizePath(path.relative(frontendRoot, fullPath)),
      line: i + 1,
      reason: hasElMessageLiteral ? 'element-message-literal' : 'cjk-literal',
      code: line.trim().slice(0, 180),
    })
  }
}

if (violations.length > 0) {
  console.error('\n[i18n-check] Found hardcoded text violations:')
  for (const issue of violations) {
    console.error(`- ${issue.file}:${issue.line} [${issue.reason}] ${issue.code}`)
  }
  console.error('\nUse i18n keys (t("...")) or add // i18n-hardcode-ignore for justified exceptions.')
  process.exit(1)
}

console.log(`[i18n-check] Passed (${files.length} files scanned).`)
