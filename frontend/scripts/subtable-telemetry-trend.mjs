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

const targetMs = Number(getArgValue('--target-ms', '1500'))
const maxPoints = Number(getArgValue('--max-points', '120'))
const project = getArgValue('--project', 'chromium')
const historyArg = getArgValue(
  '--history',
  '../docs/reports/history/subtable-first-render-history.json'
)
const reportArg = getArgValue(
  '--report',
  '../docs/reports/subtable-first-render-trend-latest.md'
)
const inputJsonArg = getArgValue('--input-json', '')
const failOnTarget = args.has('--fail-on-target')

if (!Number.isFinite(targetMs) || targetMs <= 0) {
  console.error(`[subtable-telemetry-trend] invalid target-ms: ${targetMs}`)
  process.exit(1)
}
if (!Number.isFinite(maxPoints) || maxPoints < 1) {
  console.error(`[subtable-telemetry-trend] invalid max-points: ${maxPoints}`)
  process.exit(1)
}

const frontendRoot = process.cwd()
const repoRoot = resolve(frontendRoot, '..')
const historyPath = resolve(frontendRoot, historyArg)
const reportPath = resolve(frontendRoot, reportArg)
const jsonPath = inputJsonArg
  ? resolve(frontendRoot, inputJsonArg)
  : resolve(frontendRoot, '.tmp/subtable-perf-playwright.json')

const quantile = (values, q) => {
  if (!values.length) return 0
  const sorted = [...values].sort((a, b) => a - b)
  const pos = (sorted.length - 1) * q
  const base = Math.floor(pos)
  const rest = pos - base
  if (sorted[base + 1] === undefined) return Number(sorted[base].toFixed(2))
  return Number((sorted[base] + rest * (sorted[base + 1] - sorted[base])).toFixed(2))
}

const collectAttachments = (node, matches) => {
  if (!node || typeof node !== 'object') return
  if (Array.isArray(node)) {
    for (const item of node) collectAttachments(item, matches)
    return
  }
  if (Array.isArray(node.attachments)) {
    for (const attachment of node.attachments) {
      if (attachment?.name === 'subtable-perf-metrics' && attachment?.body) {
        matches.push(attachment.body)
      }
    }
  }
  for (const value of Object.values(node)) {
    collectAttachments(value, matches)
  }
}

if (!inputJsonArg) {
  const pwArgs = [
    'playwright',
    'test',
    'e2e/objects/subtable-first-render-performance.spec.ts',
    '--project',
    project,
    '--reporter=json'
  ]
  const run = spawnSync('npx', pwArgs, {
    cwd: frontendRoot,
    shell: process.platform === 'win32',
    encoding: 'utf8'
  })
  if (run.status !== 0) {
    process.stdout.write(run.stdout || '')
    process.stderr.write(run.stderr || '')
    process.exit(run.status || 1)
  }
  mkdirSync(dirname(jsonPath), { recursive: true })
  writeFileSync(jsonPath, run.stdout || '{}', 'utf8')
}

if (!existsSync(jsonPath)) {
  console.error(`[subtable-telemetry-trend] telemetry json not found: ${jsonPath}`)
  process.exit(1)
}

let payload
try {
  payload = JSON.parse(readFileSync(jsonPath, 'utf8'))
} catch (error) {
  console.error('[subtable-telemetry-trend] failed to parse telemetry json:', error)
  process.exit(1)
}

const attachmentBodies = []
collectAttachments(payload, attachmentBodies)

const samples = []
for (const body of attachmentBodies) {
  try {
    const decoded = Buffer.from(body, 'base64').toString('utf8')
    const metrics = JSON.parse(decoded)
    if (Number.isFinite(Number(metrics?.elapsedMs))) {
      samples.push(metrics)
    }
  } catch {
    // ignore malformed attachment
  }
}

if (samples.length === 0) {
  console.error('[subtable-telemetry-trend] no subtable telemetry samples found.')
  process.exit(1)
}

const elapsedValues = samples
  .map((item) => Number(item.elapsedMs))
  .filter((value) => Number.isFinite(value))
const minMs = Number(Math.min(...elapsedValues).toFixed(2))
const maxMs = Number(Math.max(...elapsedValues).toFixed(2))
const medianMs = quantile(elapsedValues, 0.5)
const p95Ms = quantile(elapsedValues, 0.95)

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

const first = samples[0] || {}
const point = {
  date,
  timestamp,
  commit,
  project,
  objectCode: String(first.objectCode || ''),
  rowCount: Number(first.rowCount) || 0,
  pageSize: Number(first.pageSize) || 0,
  sampleCount: samples.length,
  targetMs,
  minMs,
  medianMs,
  p95Ms,
  maxMs,
  withinTarget: p95Ms < targetMs
}

let history = {
  metric: 'subtableFirstRenderElapsedMs',
  unit: 'ms',
  source: 'frontend/e2e/objects/subtable-first-render-performance.spec.ts',
  points: []
}

if (existsSync(historyPath)) {
  try {
    const parsed = JSON.parse(readFileSync(historyPath, 'utf8'))
    if (Array.isArray(parsed?.points)) {
      history = parsed
    }
  } catch (error) {
    console.error('[subtable-telemetry-trend] failed to parse history file:', error)
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
  metric: 'subtableFirstRenderElapsedMs',
  unit: 'ms',
  source: 'frontend/e2e/objects/subtable-first-render-performance.spec.ts',
  points: points.slice(-maxPoints)
}

mkdirSync(dirname(historyPath), { recursive: true })
writeFileSync(historyPath, `${JSON.stringify(history, null, 2)}\n`, 'utf8')

const p95History = quantile(
  history.points
    .map((item) => Number(item?.p95Ms))
    .filter((item) => Number.isFinite(item)),
  0.95
)
const medianHistory = quantile(
  history.points
    .map((item) => Number(item?.medianMs))
    .filter((item) => Number.isFinite(item)),
  0.5
)

const latestPoints = history.points.slice(-10)
const latestRows = latestPoints
  .map(
    (item) =>
      `| ${item.date} | ${item.medianMs} | ${item.p95Ms} | ${item.maxMs} | ${item.targetMs} | ${item.withinTarget ? 'yes' : 'no'} |`
  )
  .join('\n')

const markdown = `# SubTable First Render Trend (Latest)

- Date: ${date}
- Project: ${project}
- Latest median: ${medianMs}ms
- Latest p95: ${p95Ms}ms
- Latest max: ${maxMs}ms
- Target: < ${targetMs}ms
- Latest within target: ${point.withinTarget ? 'true' : 'false'}
- Samples in history: ${history.points.length}
- Median (history): ${medianHistory}ms
- P95 (history): ${p95History}ms

## Recent Samples (up to 10)

| Date | Median (ms) | P95 (ms) | Max (ms) | Target (ms) | Within Target |
| --- | --- | --- | --- | --- | --- |
${latestRows || '| - | - | - | - | - | - |'}
`

mkdirSync(dirname(reportPath), { recursive: true })
writeFileSync(reportPath, markdown, 'utf8')

const summary = {
  metric: 'subtableFirstRenderTrend',
  latest: point,
  samples: history.points.length,
  medianHistory,
  p95History,
  historyPath,
  reportPath,
  jsonPath
}

console.log('[subtable-telemetry-trend]', JSON.stringify(summary, null, 2))

if (failOnTarget && !point.withinTarget) {
  process.exit(1)
}
