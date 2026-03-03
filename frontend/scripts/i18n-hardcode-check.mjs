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
const scope = args.has('--scope-dynamic') ? 'dynamic' : 'all'

const DYNAMIC_PATH_PREFIXES = [
  'frontend/src/views/dynamic/',
  'frontend/src/components/engine/',
  'frontend/src/platform/layout/'
]

const DYNAMIC_PATH_EXACT = new Set([
  'frontend/src/components/common/BaseListPage.vue',
  'frontend/src/components/common/BaseFormPage.vue',
  'frontend/src/components/common/BaseDetailPage.vue',
  'frontend/src/components/common/RelatedObjectTable.vue'
])

const isSourceFile = (filePath) => {
  if (!filePath.startsWith('frontend/src/')) return false
  if (!/\.(vue|ts|tsx|js|jsx|mjs|cjs)$/.test(filePath)) return false
  if (filePath.includes('/locales/')) return false
  if (filePath.includes('/__tests__/')) return false
  if (filePath.includes('/e2e/')) return false
  if (scope === 'dynamic') {
    const inDynamicPrefix = DYNAMIC_PATH_PREFIXES.some((prefix) => filePath.startsWith(prefix))
    if (!inDynamicPrefix && !DYNAMIC_PATH_EXACT.has(filePath)) return false
  }
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
const i18nCallPattern = /(?:\$t|(?:^|[^A-Za-z0-9_$])t|i18n\.global\.t)\s*\(/
const scriptPlaceholderLiteral = /\b(?:placeholder|startPlaceholder|endPlaceholder)\s*:\s*(['"`])(?:\\.|(?!\1).)+\1/
const templateTextLiteral = />\s*([^<{}]*[A-Za-z\u3400-\u9FFF][^<{}]*)\s*</g
const i18nIgnoreMarker = 'i18n-hardcode-ignore'

const shouldSkipLine = (line) => {
  const trimmed = line.trim()
  if (!trimmed) return true
  if (trimmed.startsWith('//')) return true
  if (trimmed.startsWith('/*')) return true
  if (trimmed.startsWith('*')) return true
  if (trimmed.startsWith('*/')) return true
  if (trimmed.startsWith('import ')) return true
  if (trimmed.includes(i18nIgnoreMarker)) return true
  return false
}

const normalizePath = (relativePath) => relativePath.replace(/\\/g, '/')

const files = getCandidateFiles()
if (files.length === 0) {
  console.log(`[i18n-check] No ${changedOnly ? 'changed' : 'tracked'} source files to scan (scope=${scope}).`)
  process.exit(0)
}

const violations = []
for (const relativePath of files) {
  const fullPath = path.resolve(repoRoot, relativePath)
  if (!fs.existsSync(fullPath)) continue

  const content = fs.readFileSync(fullPath, 'utf8')
  const lines = content.split(/\r?\n/)
  const isVueFile = relativePath.endsWith('.vue')
  let inTemplate = false
  let inHtmlComment = false

  for (let i = 0; i < lines.length; i += 1) {
    const line = lines[i]
    const trimmed = line.trim()

    if (isVueFile && trimmed.startsWith('<template')) {
      inTemplate = true
    }
    if (isVueFile && trimmed.startsWith('</template')) {
      inTemplate = false
      continue
    }

    if (isVueFile && inTemplate) {
      if (inHtmlComment) {
        if (trimmed.includes('-->')) inHtmlComment = false
      } else {
        const commentStart = trimmed.indexOf('<!--')
        if (commentStart >= 0) {
          const commentEnd = trimmed.indexOf('-->', commentStart + 4)
          if (commentEnd < 0) inHtmlComment = true
        } else {
          const textMatches = [...line.matchAll(templateTextLiteral)]
          const hasTemplateTextLiteral = textMatches.some((match) => {
            const text = (match[1] || '').trim()
            if (!text) return false
            if (text.includes('{{') || text.includes('}}')) return false
            if (text.includes('$t(')) return false
            return /[A-Za-z\u3400-\u9FFF]/.test(text)
          })

          if (hasTemplateTextLiteral) {
            violations.push({
              file: normalizePath(path.relative(frontendRoot, fullPath)),
              line: i + 1,
              reason: 'template-text-literal',
              code: line.trim().slice(0, 180),
            })
            continue
          }
        }
      }
    }

    if (shouldSkipLine(line)) continue

    const hasCjkLiteral = cjkInQuote.test(line)
    const hasI18nCall = i18nCallPattern.test(line)
    const hasElMessageLiteral = elMessageLiteral.test(line) && !hasI18nCall
    const hasScriptPlaceholderLiteral = scriptPlaceholderLiteral.test(line)
    if (!hasCjkLiteral && !hasElMessageLiteral && !hasScriptPlaceholderLiteral) continue

    violations.push({
      file: normalizePath(path.relative(frontendRoot, fullPath)),
      line: i + 1,
      reason: hasElMessageLiteral
        ? 'element-message-literal'
        : hasScriptPlaceholderLiteral
          ? 'script-placeholder-literal'
          : 'cjk-literal',
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

console.log(`[i18n-check] Passed (${files.length} files scanned, scope=${scope}, mode=${changedOnly ? 'changed' : 'all'}).`)
