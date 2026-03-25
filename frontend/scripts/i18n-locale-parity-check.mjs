#!/usr/bin/env node
import { execSync } from 'node:child_process'
import fs from 'node:fs'
import path from 'node:path'

const args = new Set(process.argv.slice(2))
const failOnIssues = args.has('--fail-on-issues')
const verbose = args.has('--verbose')
const changedOnly = args.has('--changed') || !args.has('--all')
const detectMojibake = args.has('--detect-mojibake')
const isCi = process.env.CI === 'true'

const frontendRoot = process.cwd()
const repoRoot = path.resolve(frontendRoot, '..')
const localesRoot = path.join(frontendRoot, 'src', 'locales')
const baseLocale = 'en-US'
const targetLocale = 'zh-CN'

function listJson(localeDir) {
  return fs
    .readdirSync(localeDir)
    .filter((file) => file.endsWith('.json'))
    .sort()
}

function readJson(filePath) {
  return JSON.parse(fs.readFileSync(filePath, 'utf8'))
}

function readJsonFromGit(ref, repoRelativePath) {
  try {
    const content = execSync(`git show ${ref}:${repoRelativePath.replace(/\\/g, '/')}`, {
      cwd: repoRoot,
      encoding: 'utf8',
      stdio: ['ignore', 'pipe', 'ignore'],
    })
    return JSON.parse(content)
  } catch {
    return null
  }
}

function flattenDict(input, prefix = '') {
  const out = new Map()
  if (!input || typeof input !== 'object' || Array.isArray(input)) {
    out.set(prefix, input)
    return out
  }

  for (const [key, value] of Object.entries(input)) {
    const nextKey = prefix ? `${prefix}.${key}` : key
    if (value && typeof value === 'object' && !Array.isArray(value)) {
      const nested = flattenDict(value, nextKey)
      for (const [nestedKey, nestedValue] of nested.entries()) {
        out.set(nestedKey, nestedValue)
      }
    } else {
      out.set(nextKey, value)
    }
  }

  return out
}

function extractPlaceholders(text) {
  if (typeof text !== 'string') return []
  const matches = text.match(/\{[a-zA-Z0-9_.]+\}/g) || []
  return Array.from(new Set(matches)).sort()
}

function isSuspiciousValue(value) {
  if (typeof value !== 'string') return false
  return value.includes('???') || value.includes('\uFFFD')
}

const MOJIBAKE_CJK_CHAR_HINTS = new Set([
  '鍙', '鍒', '鍚', '鍔', '鍥', '鍐', '鍙', '鍩', '鍩', '鍩', '鍩', '鍩',
  '鎴', '鏃', '鏄', '鏍', '鏈', '涓', '娴', '淇', '妯', '瀛', '璇', '纭',
  '绯', '缁', '绫', '绛', '缂', '缃', '缁', '閰', '锛', '銆'
])

function isCjkChar(ch) {
  return /[\u3400-\u9FFF]/.test(ch)
}

function isLikelyMojibake(value) {
  if (!detectMojibake || typeof value !== 'string') return false

  let cjkCount = 0
  let hintCount = 0
  for (const ch of value) {
    if (!isCjkChar(ch)) continue
    cjkCount += 1
    if (MOJIBAKE_CJK_CHAR_HINTS.has(ch)) hintCount += 1
  }

  if (cjkCount < 2 || hintCount < 2) return false
  return hintCount / cjkCount >= 0.35
}

function compareLocaleObjects(baseJson, targetJson) {
  const baseFlat = flattenDict(baseJson)
  const targetFlat = flattenDict(targetJson)

  const missingInTarget = []
  const extraInTarget = []
  const placeholderMismatches = []
  const suspiciousValues = []
  const mojibakeValues = []

  for (const key of baseFlat.keys()) {
    if (!targetFlat.has(key)) {
      missingInTarget.push(key)
      continue
    }

    const baseValue = baseFlat.get(key)
    const targetValue = targetFlat.get(key)
    const baseVars = extractPlaceholders(baseValue)
    const targetVars = extractPlaceholders(targetValue)
    if (baseVars.join('|') !== targetVars.join('|')) {
      placeholderMismatches.push({
        key,
        baseVars,
        targetVars
      })
    }
  }

  for (const [key, value] of targetFlat.entries()) {
    if (!baseFlat.has(key)) {
      extraInTarget.push(key)
    }
    if (isSuspiciousValue(value)) {
      suspiciousValues.push(key)
    }
    if (isLikelyMojibake(value)) {
      mojibakeValues.push(key)
    }
  }

  return {
    baseCount: baseFlat.size,
    targetCount: targetFlat.size,
    missingInTarget,
    extraInTarget,
    placeholderMismatches,
    suspiciousValues,
    mojibakeValues
  }
}

function compareLocaleFile(baseFilePath, targetFilePath) {
  const baseJson = readJson(baseFilePath)
  const targetJson = readJson(targetFilePath)
  return compareLocaleObjects(baseJson, targetJson)
}

function isLocaleSourceFile(filePath) {
  const normalized = filePath.replace(/\\/g, '/')
  if (!normalized.startsWith('frontend/src/locales/')) return false
  if (!normalized.endsWith('.json')) return false
  return (
    normalized.includes(`/src/locales/${baseLocale}/`) ||
    normalized.includes(`/src/locales/${targetLocale}/`)
  )
}

function getChangedLocaleFiles() {
  // CI: enforce on latest commit changes.
  if (isCi) {
    const latestCommitFiles = execSync('git diff-tree --no-commit-id --name-only -r HEAD', {
      cwd: repoRoot,
      encoding: 'utf8',
      stdio: ['ignore', 'pipe', 'ignore'],
    })
      .split(/\r?\n/)
      .map((line) => line.trim())
      .filter(Boolean)
      .filter(isLocaleSourceFile)

    return [...new Set(latestCommitFiles)]
  }

  // Local: enforce on current working tree.
  const workingTreeFiles = execSync('git status --porcelain', {
    cwd: repoRoot,
    encoding: 'utf8',
    stdio: ['ignore', 'pipe', 'ignore'],
  })
    .split(/\r?\n/)
    .filter((line) => line && line.length >= 4)
    .map((line) => line.slice(3).trim())
    .map((line) => line.replace(/^"|"$/g, ''))
    .filter(isLocaleSourceFile)

  return [...new Set(workingTreeFiles)]
}

function toLocaleFileName(repoPath) {
  const normalized = repoPath.replace(/\\/g, '/')
  const idx = normalized.lastIndexOf('/')
  return idx >= 0 ? normalized.slice(idx + 1) : normalized
}

const mismatchSignature = (item) => {
  if (typeof item === 'string') return item
  return `${item.key}|${(item.baseVars || []).join(',')}|${(item.targetVars || []).join(',')}`
}

function diffItems(currentItems, previousItems) {
  const previousSet = new Set(previousItems.map(mismatchSignature))
  return currentItems.filter((item) => !previousSet.has(mismatchSignature(item)))
}

function applyIncrementalIssues(fileName, currentResult) {
  const baselineRef = isCi ? 'HEAD^' : 'HEAD'
  const baseRepoPath = `frontend/src/locales/${baseLocale}/${fileName}`
  const targetRepoPath = `frontend/src/locales/${targetLocale}/${fileName}`

  const basePrevJson = readJsonFromGit(baselineRef, baseRepoPath)
  const targetPrevJson = readJsonFromGit(baselineRef, targetRepoPath)
  if (!basePrevJson || !targetPrevJson) {
    return currentResult
  }

  const previousResult = compareLocaleObjects(basePrevJson, targetPrevJson)
  return {
    ...currentResult,
    missingInTarget: diffItems(currentResult.missingInTarget, previousResult.missingInTarget),
    placeholderMismatches: diffItems(currentResult.placeholderMismatches, previousResult.placeholderMismatches),
    suspiciousValues: diffItems(currentResult.suspiciousValues, previousResult.suspiciousValues),
    mojibakeValues: diffItems(currentResult.mojibakeValues, previousResult.mojibakeValues),
  }
}

function main() {
  const baseDir = path.join(localesRoot, baseLocale)
  const targetDir = path.join(localesRoot, targetLocale)
  const files = changedOnly
    ? Array.from(new Set(getChangedLocaleFiles().map(toLocaleFileName))).sort()
    : Array.from(new Set([
      ...listJson(baseDir),
      ...listJson(targetDir)
    ])).sort()

  if (files.length === 0) {
    console.log(JSON.stringify({
      baseLocale,
      targetLocale,
      mode: changedOnly ? 'changed' : 'all',
      files: [],
      totals: {
        fileCount: 0,
        issueCount: 0
      }
    }, null, 2))
    process.exit(0)
  }

  const report = []
  let issueCount = 0

  for (const file of files) {
    const basePath = path.join(baseDir, file)
    const targetPath = path.join(targetDir, file)

    const baseExists = fs.existsSync(basePath)
    const targetExists = fs.existsSync(targetPath)
    if (!baseExists || !targetExists) {
      issueCount += 1
      report.push({
        file,
        error: !baseExists
          ? `${baseLocale} missing file`
          : `${targetLocale} missing file`
      })
      continue
    }

    const result = compareLocaleFile(basePath, targetPath)
    const effectiveResult = changedOnly ? applyIncrementalIssues(file, result) : result
    const fileIssues =
      effectiveResult.missingInTarget.length +
      effectiveResult.placeholderMismatches.length +
      effectiveResult.suspiciousValues.length +
      effectiveResult.mojibakeValues.length
    if (fileIssues > 0) {
      issueCount += fileIssues
    }

    report.push({
      file,
      baseCount: effectiveResult.baseCount,
      targetCount: effectiveResult.targetCount,
      missingInTarget: effectiveResult.missingInTarget.length,
      extraInTarget: effectiveResult.extraInTarget.length,
      placeholderMismatches: effectiveResult.placeholderMismatches.length,
      suspiciousValues: effectiveResult.suspiciousValues.length,
      mojibakeValues: effectiveResult.mojibakeValues.length,
      sample: {
        missingInTarget: effectiveResult.missingInTarget.slice(0, 10),
        extraInTarget: effectiveResult.extraInTarget.slice(0, 10),
        placeholderMismatches: effectiveResult.placeholderMismatches.slice(0, 5),
        suspiciousValues: effectiveResult.suspiciousValues.slice(0, 10),
        mojibakeValues: effectiveResult.mojibakeValues.slice(0, 10)
      }
    })
  }

  console.log(JSON.stringify({
    baseLocale,
    targetLocale,
    mode: changedOnly ? 'changed' : 'all',
    files: report,
    totals: {
      fileCount: files.length,
      issueCount
    }
  }, null, 2))

  if (verbose) {
    const problematic = report.filter((item) => {
      if (item.error) return true
      return (
        item.missingInTarget > 0 ||
        item.placeholderMismatches > 0 ||
        item.suspiciousValues > 0 ||
        item.mojibakeValues > 0
      )
    })
    if (problematic.length > 0) {
      console.error('\n[parity-check] Problematic files:')
      for (const item of problematic) {
        console.error(`- ${item.file}`)
      }
    }
  }

  if (failOnIssues && issueCount > 0) {
    process.exit(1)
  }
}

main()
