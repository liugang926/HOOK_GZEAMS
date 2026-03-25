#!/usr/bin/env node
import { execSync } from 'node:child_process'
import fs from 'node:fs'
import path from 'node:path'

const argv = process.argv.slice(2)
const args = new Set(argv)
const isCi = process.env.CI === 'true'

const getArgValue = (name, fallback) => {
  const idx = argv.indexOf(name)
  if (idx < 0 || idx + 1 >= argv.length) return fallback
  return argv[idx + 1]
}

const changedOnly = args.has('--changed')
const failOnThreshold = args.has('--fail-on-threshold')
const jsonOnly = args.has('--json')
const threshold = Number(getArgValue('--threshold', '95'))
const scope = getArgValue('--scope', 'dynamic')

const frontendRoot = process.cwd()
const repoRoot = path.resolve(frontendRoot, '..')

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

const i18nCallPattern = /(?:\$t|(?:^|[^A-Za-z0-9_$])t|i18n\.global\.t)\s*\(\s*(['"`])[^'"`]+?\1/g
const cjkInQuote = /(['"`])(?:\\.|(?!\1).)*[\u3400-\u9FFF]+(?:\\.|(?!\1).)*\1/g
const elMessageLiteral =
  /\bElMessage(?:Box)?\s*\.\s*(?:success|error|warning|info|confirm|alert|prompt)\s*\(\s*(['"`])(?:\\.|(?!\1).)+\1/g
const uiAttrLiteral =
  /(^|[^:@\w-])(label|title|placeholder|content|aria-label|confirm-button-text|cancel-button-text)\s*=\s*(['"])([^'"]+)\3/g
const scriptPlaceholderLiteral = /\b(?:placeholder|startPlaceholder|endPlaceholder)\s*:\s*(['"`])(?:\\.|(?!\1).)+\1/g
const templateTextLiteral = />\s*([^<{}]*[A-Za-z\u3400-\u9FFF][^<{}]*)\s*</g
const i18nIgnoreMarker = 'i18n-hardcode-ignore'

const normalizePath = (relativePath) => relativePath.replace(/\\/g, '/')

const isSourceFile = (filePath) => {
  if (!filePath.startsWith('frontend/src/')) return false
  if (!/\.(vue|ts|tsx|js|jsx|mjs|cjs)$/.test(filePath)) return false
  if (filePath.includes('/locales/')) return false
  if (filePath.includes('/__tests__/')) return false
  if (filePath.includes('/e2e/')) return false
  return true
}

const isDynamicScopeFile = (filePath) => {
  if (DYNAMIC_PATH_EXACT.has(filePath)) return true
  return DYNAMIC_PATH_PREFIXES.some((prefix) => filePath.startsWith(prefix))
}

const inScope = (filePath) => {
  if (scope === 'all') return true
  if (scope === 'dynamic') return isDynamicScopeFile(filePath)
  return false
}

const getCandidateFiles = () => {
  if (!changedOnly) {
    return execSync('git ls-files "frontend/src/**/*.*"', { cwd: repoRoot, encoding: 'utf8' })
      .split(/\r?\n/)
      .map((line) => line.trim())
      .filter(Boolean)
      .filter(isSourceFile)
      .filter(inScope)
  }

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
      .filter(inScope)
    return [...new Set(latestCommitFiles)]
  }

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
    .filter(inScope)

  return [...new Set(workingTreeFiles)]
}

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

const hasNaturalLanguage = (value) => {
  if (!value) return false
  if (/[\u3400-\u9FFF]/.test(value)) return true
  // Match basic English-like words while avoiding snake_case, routes, and keys.
  if (/[A-Za-z]{2,}(?:\s+[A-Za-z]{2,})+/.test(value)) return true
  return false
}

const metrics = {
  scope,
  mode: changedOnly ? 'changed' : 'all',
  threshold,
  filesScanned: 0,
  i18nRefs: 0,
  hardcodedHits: {
    cjkQuote: 0,
    elementMessageLiteral: 0,
    staticUiAttributeLiteral: 0,
    scriptPlaceholderLiteral: 0,
    templateTextLiteral: 0
  },
  samples: []
}

const files = getCandidateFiles()
if (files.length === 0) {
  const emptyReport = {
    ...metrics,
    coverage: 100,
    meetsThreshold: true
  }
  console.log(JSON.stringify(emptyReport, null, 2))
  process.exit(0)
}

for (const relativePath of files) {
  const fullPath = path.resolve(repoRoot, relativePath)
  if (!fs.existsSync(fullPath)) continue

  metrics.filesScanned += 1
  const content = fs.readFileSync(fullPath, 'utf8')
  const lines = content.split(/\r?\n/)
  const normalizedFile = normalizePath(path.relative(frontendRoot, fullPath))
  const isVueFile = normalizedFile.endsWith('.vue')
  let inHtmlComment = false
  let inTemplate = false

  for (let i = 0; i < lines.length; i += 1) {
    const line = lines[i]
    const trimmed = line.trim()

    if (isVueFile) {
      if (trimmed.startsWith('<template')) {
        inTemplate = true
      }
      if (trimmed.startsWith('</template')) {
        inTemplate = false
        continue
      }

      if (inHtmlComment) {
        if (trimmed.includes('-->')) inHtmlComment = false
        continue
      }
      const commentStart = trimmed.indexOf('<!--')
      if (commentStart >= 0) {
        const commentEnd = trimmed.indexOf('-->', commentStart + 4)
        if (commentEnd < 0) {
          inHtmlComment = true
        }
        continue
      }

      if (inTemplate) {
        const textMatches = [...line.matchAll(templateTextLiteral)]
        for (const match of textMatches) {
          const text = (match[1] || '').trim()
          if (!hasNaturalLanguage(text)) continue
          if (text.includes('{{') || text.includes('}}')) continue
          if (text.includes('$t(')) continue
          metrics.hardcodedHits.templateTextLiteral += 1
          if (metrics.samples.length < 20) {
            metrics.samples.push({
              file: normalizedFile,
              line: i + 1,
              type: 'template-text-literal',
              code: line.trim().slice(0, 180)
            })
          }
        }
      }
    }

    if (shouldSkipLine(line)) continue

    const i18nMatches = [...line.matchAll(i18nCallPattern)]
    if (i18nMatches.length > 0) {
      metrics.i18nRefs += i18nMatches.length
    }

    const hasI18nCall = i18nMatches.length > 0
    const cjkMatches = [...line.matchAll(cjkInQuote)]
    const messageMatches = [...line.matchAll(elMessageLiteral)]
    const hasRawElementMessage = messageMatches.length > 0 && !hasI18nCall

    if (hasRawElementMessage) {
      metrics.hardcodedHits.elementMessageLiteral += 1
      if (metrics.samples.length < 20) {
        metrics.samples.push({
          file: normalizedFile,
          line: i + 1,
          type: 'element-message-literal',
          code: line.trim().slice(0, 180)
        })
      }
    } else if (cjkMatches.length > 0) {
      metrics.hardcodedHits.cjkQuote += cjkMatches.length
      for (const _ of cjkMatches) {
        if (metrics.samples.length < 20) {
          metrics.samples.push({
            file: normalizedFile,
            line: i + 1,
            type: 'cjk-quote',
            code: line.trim().slice(0, 180)
          })
        }
      }
    }

    if (isVueFile) {
      const attrMatches = [...line.matchAll(uiAttrLiteral)]
      for (const match of attrMatches) {
        const value = (match[4] || '').trim()
        if (!hasNaturalLanguage(value)) continue
        if (value.includes('$t(') || value.includes('{{')) continue
        metrics.hardcodedHits.staticUiAttributeLiteral += 1
        if (metrics.samples.length < 20) {
          metrics.samples.push({
            file: normalizedFile,
            line: i + 1,
            type: `static-ui-attribute:${match[2]}`,
            code: line.trim().slice(0, 180)
          })
        }
      }
    }

    const scriptPlaceholderMatches = [...line.matchAll(scriptPlaceholderLiteral)]
    for (const _ of scriptPlaceholderMatches) {
      metrics.hardcodedHits.scriptPlaceholderLiteral += 1
      if (metrics.samples.length < 20) {
        metrics.samples.push({
          file: normalizedFile,
          line: i + 1,
          type: 'script-placeholder-literal',
          code: line.trim().slice(0, 180)
        })
      }
    }
  }
}

const hardcodedTotal =
  metrics.hardcodedHits.cjkQuote +
  metrics.hardcodedHits.elementMessageLiteral +
  metrics.hardcodedHits.staticUiAttributeLiteral +
  metrics.hardcodedHits.scriptPlaceholderLiteral +
  metrics.hardcodedHits.templateTextLiteral

const localizableTotal = metrics.i18nRefs + hardcodedTotal
const coverage = localizableTotal === 0 ? 100 : Number(((metrics.i18nRefs / localizableTotal) * 100).toFixed(2))
const meetsThreshold = coverage >= threshold

const report = {
  ...metrics,
  hardcodedTotal,
  localizableTotal,
  coverage,
  meetsThreshold
}

if (!jsonOnly) {
  console.log(`[i18n-coverage] scope=${scope} mode=${metrics.mode} files=${metrics.filesScanned}`)
  console.log(`[i18n-coverage] i18nRefs=${metrics.i18nRefs} hardcoded=${hardcodedTotal} coverage=${coverage}% threshold=${threshold}%`)
  if (metrics.samples.length > 0) {
    console.log('[i18n-coverage] sample hardcoded hits:')
    for (const sample of metrics.samples.slice(0, 10)) {
      console.log(`- ${sample.file}:${sample.line} [${sample.type}] ${sample.code}`)
    }
  }
}
console.log(JSON.stringify(report, null, 2))

if (failOnThreshold && !meetsThreshold) {
  process.exit(1)
}
