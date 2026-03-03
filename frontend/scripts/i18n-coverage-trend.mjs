#!/usr/bin/env node
import { execSync, spawnSync } from 'node:child_process'
import { existsSync, mkdirSync, readFileSync, writeFileSync } from 'node:fs'
import { dirname, resolve } from 'node:path'

const argv = process.argv.slice(2)
const args = new Set(argv)

const getArgValue = (name, fallback) => {
  const idx = argv.indexOf(name)
  if (idx < 0 || idx + 1 >= argv.length) return fallback
  return argv[idx + 1]
}

const threshold = Number(getArgValue('--threshold', '95'))
const maxPoints = Number(getArgValue('--max-points', '120'))
const historyArg = getArgValue(
  '--history',
  '../docs/reports/history/i18n-dynamic-coverage-history.json'
)
const reportArg = getArgValue(
  '--report',
  '../docs/reports/i18n-dynamic-coverage-trend-latest.md'
)
const failOnThreshold = args.has('--fail-on-threshold')

if (!Number.isFinite(threshold) || threshold < 0 || threshold > 100) {
  console.error(`[i18n-coverage-trend] invalid threshold: ${threshold}`)
  process.exit(1)
}
if (!Number.isFinite(maxPoints) || maxPoints < 1) {
  console.error(`[i18n-coverage-trend] invalid max-points: ${maxPoints}`)
  process.exit(1)
}

const frontendRoot = process.cwd()
const repoRoot = resolve(frontendRoot, '..')
const historyPath = resolve(frontendRoot, historyArg)
const reportPath = resolve(frontendRoot, reportArg)

const coverageArgs = [
  'scripts/i18n-coverage-metrics.mjs',
  '--scope',
  'dynamic',
  '--all',
  '--threshold',
  String(threshold),
  '--json'
]
if (failOnThreshold) {
  coverageArgs.push('--fail-on-threshold')
}

const coverageRun = spawnSync('node', coverageArgs, {
  cwd: frontendRoot,
  shell: process.platform === 'win32',
  encoding: 'utf8'
})

if (coverageRun.status !== 0) {
  process.stdout.write(coverageRun.stdout || '')
  process.stderr.write(coverageRun.stderr || '')
  process.exit(coverageRun.status || 1)
}

let metrics
try {
  metrics = JSON.parse((coverageRun.stdout || '').trim())
} catch (error) {
  console.error('[i18n-coverage-trend] failed to parse coverage metrics json:', error)
  process.exit(1)
}

const quantile = (values, q) => {
  if (!values.length) return 0
  const sorted = [...values].sort((a, b) => a - b)
  const pos = (sorted.length - 1) * q
  const base = Math.floor(pos)
  const rest = pos - base
  if (sorted[base + 1] === undefined) return Number(sorted[base].toFixed(2))
  return Number((sorted[base] + rest * (sorted[base + 1] - sorted[base])).toFixed(2))
}

const now = new Date()
const timestamp = now.toISOString()
const date = timestamp.slice(0, 10)

let commit = 'unknown'
try {
  commit = execSync('git rev-parse --short HEAD', {
    cwd: repoRoot,
    encoding: 'utf8',
    stdio: ['ignore', 'pipe', 'ignore']
  }).trim()
} catch {
  // keep "unknown"
}

const point = {
  date,
  timestamp,
  commit,
  threshold,
  filesScanned: Number(metrics.filesScanned) || 0,
  i18nRefs: Number(metrics.i18nRefs) || 0,
  hardcodedTotal: Number(metrics.hardcodedTotal) || 0,
  localizableTotal: Number(metrics.localizableTotal) || 0,
  coverage: Number(metrics.coverage) || 0,
  meetsThreshold: Boolean(metrics.meetsThreshold)
}

let history = {
  metric: 'i18nDynamicCoverage',
  unit: 'percent',
  source: 'frontend/scripts/i18n-coverage-metrics.mjs',
  points: []
}

if (existsSync(historyPath)) {
  try {
    const parsed = JSON.parse(readFileSync(historyPath, 'utf8'))
    if (Array.isArray(parsed?.points)) {
      history = parsed
    }
  } catch (error) {
    console.error('[i18n-coverage-trend] failed to parse history file:', error)
    process.exit(1)
  }
}

const points = Array.isArray(history.points) ? history.points : []
const replaceIndex = points.findIndex((item) => item?.date === date)
if (replaceIndex >= 0) {
  points[replaceIndex] = point
} else {
  points.push(point)
}

points.sort((a, b) => String(a.timestamp).localeCompare(String(b.timestamp)))
history = {
  ...history,
  metric: 'i18nDynamicCoverage',
  unit: 'percent',
  source: 'frontend/scripts/i18n-coverage-metrics.mjs',
  points: points.slice(-maxPoints)
}

mkdirSync(dirname(historyPath), { recursive: true })
writeFileSync(historyPath, `${JSON.stringify(history, null, 2)}\n`, 'utf8')

const values = history.points
  .map((item) => Number(item?.coverage))
  .filter((item) => Number.isFinite(item))
const medianCoverage = quantile(values, 0.5)
const p95Coverage = quantile(values, 0.95)

const latestPoints = history.points.slice(-10)
const latestRows = latestPoints
  .map(
    (item) =>
      `| ${item.date} | ${item.coverage}% | ${item.hardcodedTotal} | ${item.i18nRefs} | ${item.meetsThreshold ? 'yes' : 'no'} |`
  )
  .join('\n')

const markdown = `# i18n Dynamic Coverage Trend (Latest)

- Date: ${date}
- Latest coverage: ${point.coverage}%
- Threshold: ${threshold}%
- Latest meets threshold: ${point.meetsThreshold ? 'true' : 'false'}
- Samples in history: ${history.points.length}
- Median coverage (history): ${medianCoverage}%
- P95 coverage (history): ${p95Coverage}%

## Recent Samples (up to 10)

| Date | Coverage | Hardcoded | i18nRefs | Meets Threshold |
| --- | --- | --- | --- | --- |
${latestRows || '| - | - | - | - | - |'}
`

mkdirSync(dirname(reportPath), { recursive: true })
writeFileSync(reportPath, markdown, 'utf8')

const summary = {
  metric: 'i18nDynamicCoverageTrend',
  latest: point,
  samples: history.points.length,
  medianCoverage,
  p95Coverage,
  historyPath,
  reportPath
}

console.log('[i18n-coverage-trend]', JSON.stringify(summary, null, 2))

if (failOnThreshold && !point.meetsThreshold) {
  process.exit(1)
}
