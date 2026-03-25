#!/usr/bin/env node
import { execSync } from 'node:child_process'
import { existsSync, mkdirSync, readdirSync, readFileSync, statSync, writeFileSync } from 'node:fs'
import { dirname, extname, resolve } from 'node:path'

const argv = process.argv.slice(2)
const args = new Set(argv)

const getArgValue = (name, fallback) => {
  const index = argv.indexOf(name)
  if (index < 0 || index + 1 >= argv.length) return fallback
  return argv[index + 1]
}

const formatBytes = (value) => `${(value / 1024).toFixed(2)} KiB`
const formatDelta = (value) => {
  if (!Number.isFinite(value) || value === 0) return '0.00 KiB'
  const sign = value > 0 ? '+' : '-'
  return `${sign}${(Math.abs(value) / 1024).toFixed(2)} KiB`
}

const normalizeChunkLabel = (filename) => {
  const matched = filename.match(/^(.*)-([A-Za-z0-9_-]{8,})\.(js|css)$/)
  if (!matched) return filename
  return `${matched[1]}.${matched[3]}`
}

const frontendRoot = process.cwd()
const repoRoot = resolve(frontendRoot, '..')

const distArg = getArgValue('--dist', 'dist/assets')
const historyArg = getArgValue(
  '--history',
  '../docs/reports/history/frontend-build-chunk-history.json'
)
const reportArg = getArgValue(
  '--report',
  '../docs/reports/frontend-build-chunk-analysis-latest.md'
)
const summaryArg = getArgValue(
  '--summary-json',
  '../docs/reports/history/frontend-build-chunk-analysis-latest.json'
)
const topCount = Number(getArgValue('--top', '20'))
const maxPoints = Number(getArgValue('--max-points', '120'))
const jsBudget = Number(getArgValue('--budget-js', '768000'))
const cssBudget = Number(getArgValue('--budget-css', '358400'))
const failOnBudget = args.has('--fail-on-budget')

if (!Number.isFinite(topCount) || topCount < 1) {
  console.error(`[build-chunk-report] invalid --top value: ${topCount}`)
  process.exit(1)
}

if (!Number.isFinite(maxPoints) || maxPoints < 1) {
  console.error(`[build-chunk-report] invalid --max-points value: ${maxPoints}`)
  process.exit(1)
}

if (!Number.isFinite(jsBudget) || jsBudget < 1 || !Number.isFinite(cssBudget) || cssBudget < 1) {
  console.error('[build-chunk-report] budget values must be positive numbers.')
  process.exit(1)
}

const distPath = resolve(frontendRoot, distArg)
const historyPath = resolve(frontendRoot, historyArg)
const reportPath = resolve(frontendRoot, reportArg)
const summaryPath = resolve(frontendRoot, summaryArg)

if (!existsSync(distPath)) {
  console.error(`[build-chunk-report] dist assets directory not found: ${distPath}`)
  process.exit(1)
}

const files = readdirSync(distPath)
  .map((name) => {
    const fullPath = resolve(distPath, name)
    const stats = statSync(fullPath)
    if (!stats.isFile()) return null
    const extension = extname(name).toLowerCase()
    const type = extension === '.js' ? 'js' : extension === '.css' ? 'css' : 'other'
    return {
      name,
      label: normalizeChunkLabel(name),
      type,
      bytes: stats.size,
      kib: Number((stats.size / 1024).toFixed(2)),
    }
  })
  .filter(Boolean)
  .sort((left, right) => right.bytes - left.bytes)

if (!files.length) {
  console.error(`[build-chunk-report] no files found in dist assets directory: ${distPath}`)
  process.exit(1)
}

const jsFiles = files.filter((file) => file.type === 'js')
const cssFiles = files.filter((file) => file.type === 'css')
const otherFiles = files.filter((file) => file.type === 'other')

const sumBytes = (items) => items.reduce((total, item) => total + item.bytes, 0)
const totalBytes = sumBytes(files)
const totalJsBytes = sumBytes(jsFiles)
const totalCssBytes = sumBytes(cssFiles)
const totalOtherBytes = sumBytes(otherFiles)

const largestChunk = files[0] ?? null
const largestJsChunk = jsFiles[0] ?? null
const largestCssChunk = cssFiles[0] ?? null

const oversizedJsChunks = jsFiles
  .filter((file) => file.bytes > jsBudget)
  .map((file) => ({
    name: file.name,
    label: file.label,
    bytes: file.bytes,
    kib: file.kib,
    budgetKib: Number((jsBudget / 1024).toFixed(2)),
  }))

const oversizedCssChunks = cssFiles
  .filter((file) => file.bytes > cssBudget)
  .map((file) => ({
    name: file.name,
    label: file.label,
    bytes: file.bytes,
    kib: file.kib,
    budgetKib: Number((cssBudget / 1024).toFixed(2)),
  }))

const timestamp = new Date().toISOString()
const date = timestamp.slice(0, 10)

let commit = 'unknown'
try {
  commit = execSync('git rev-parse --short HEAD', {
    cwd: repoRoot,
    encoding: 'utf8',
    stdio: ['ignore', 'pipe', 'ignore'],
  }).trim()
} catch {
  // keep "unknown"
}

let history = {
  metric: 'frontendBuildChunkSizes',
  unit: 'bytes',
  source: 'frontend/dist/assets',
  points: [],
}

if (existsSync(historyPath)) {
  try {
    const parsed = JSON.parse(readFileSync(historyPath, 'utf8'))
    if (Array.isArray(parsed?.points)) {
      history = parsed
    }
  } catch (error) {
    console.error('[build-chunk-report] failed to parse history file:', error)
    process.exit(1)
  }
}

const points = Array.isArray(history.points) ? history.points : []
const previousPoint = points.at(-1) ?? null

const point = {
  date,
  timestamp,
  commit,
  distPath,
  chunkCount: files.length,
  jsCount: jsFiles.length,
  cssCount: cssFiles.length,
  otherCount: otherFiles.length,
  totalBytes,
  totalJsBytes,
  totalCssBytes,
  totalOtherBytes,
  jsBudget,
  cssBudget,
  oversizedJsCount: oversizedJsChunks.length,
  oversizedCssCount: oversizedCssChunks.length,
  largestChunk: largestChunk
    ? { name: largestChunk.name, label: largestChunk.label, bytes: largestChunk.bytes }
    : null,
  largestJsChunk: largestJsChunk
    ? { name: largestJsChunk.name, label: largestJsChunk.label, bytes: largestJsChunk.bytes }
    : null,
  largestCssChunk: largestCssChunk
    ? { name: largestCssChunk.name, label: largestCssChunk.label, bytes: largestCssChunk.bytes }
    : null,
  topChunks: files.slice(0, Math.min(topCount, 10)).map((file) => ({
    name: file.name,
    label: file.label,
    type: file.type,
    bytes: file.bytes,
  })),
}

const replaceIndex = points.findIndex((item) => item?.date === date)
if (replaceIndex >= 0) {
  points[replaceIndex] = point
} else {
  points.push(point)
}
points.sort((left, right) => String(left.timestamp).localeCompare(String(right.timestamp)))

history = {
  ...history,
  metric: 'frontendBuildChunkSizes',
  unit: 'bytes',
  source: 'frontend/dist/assets',
  points: points.slice(-maxPoints),
}

const latestPoints = history.points.slice(-10)

const topChunkRows = files
  .slice(0, topCount)
  .map(
    (file) =>
      `| ${file.label} | ${file.type.toUpperCase()} | ${formatBytes(file.bytes)} | ${file.name} |`
  )
  .join('\n')

const oversizedRows = [...oversizedJsChunks, ...oversizedCssChunks]
  .sort((left, right) => right.bytes - left.bytes)
  .map(
    (file) =>
      `| ${file.label} | ${file.name.endsWith('.css') ? 'CSS' : 'JS'} | ${formatBytes(file.bytes)} | ${formatBytes(
        file.name.endsWith('.css') ? cssBudget : jsBudget
      )} |`
  )
  .join('\n')

const recentRows = latestPoints
  .map((item) => {
    const largest = item?.largestChunk
      ? `${item.largestChunk.label} (${formatBytes(item.largestChunk.bytes)})`
      : '-'
    return `| ${item.date} | ${item.commit} | ${formatBytes(item.totalJsBytes || 0)} | ${formatBytes(
      item.totalCssBytes || 0
    )} | ${largest} | ${(item.oversizedJsCount || 0) + (item.oversizedCssCount || 0)} |`
  })
  .join('\n')

const deltaJsBytes = previousPoint ? totalJsBytes - Number(previousPoint.totalJsBytes || 0) : 0
const deltaCssBytes = previousPoint ? totalCssBytes - Number(previousPoint.totalCssBytes || 0) : 0
const deltaChunkCount = previousPoint ? files.length - Number(previousPoint.chunkCount || 0) : 0

const markdown = `# Frontend Build Chunk Analysis (Latest)

- Date: ${date}
- Commit: ${commit}
- Dist assets: ${distArg}
- Total chunks: ${files.length} (${jsFiles.length} JS / ${cssFiles.length} CSS / ${otherFiles.length} other)
- Total JS size: ${formatBytes(totalJsBytes)}${previousPoint ? ` (${formatDelta(deltaJsBytes)} vs previous)` : ''}
- Total CSS size: ${formatBytes(totalCssBytes)}${previousPoint ? ` (${formatDelta(deltaCssBytes)} vs previous)` : ''}
- Total asset size: ${formatBytes(totalBytes)}
- Chunk count delta: ${previousPoint ? `${deltaChunkCount > 0 ? '+' : ''}${deltaChunkCount}` : 'baseline'}
- Largest chunk: ${largestChunk ? `${largestChunk.label} (${formatBytes(largestChunk.bytes)})` : '-'}
- Largest JS chunk budget: ${formatBytes(jsBudget)} | Over budget: ${oversizedJsChunks.length}
- Largest CSS chunk budget: ${formatBytes(cssBudget)} | Over budget: ${oversizedCssChunks.length}

## Top Chunks

| Chunk | Type | Size | File |
| --- | --- | --- | --- |
${topChunkRows || '| - | - | - | - |'}

## Budget Alerts

| Chunk | Type | Size | Budget |
| --- | --- | --- | --- |
${oversizedRows || '| None | - | - | - |'}

## Recent Trend (Last 10 Runs)

| Date | Commit | Total JS | Total CSS | Largest Chunk | Over Budget |
| --- | --- | --- | --- | --- | --- |
${recentRows || '| - | - | - | - | - | - |'}
`

const summary = {
  metric: 'frontendBuildChunkSizes',
  latest: point,
  deltaFromPrevious: previousPoint
    ? {
        totalJsBytes: deltaJsBytes,
        totalCssBytes: deltaCssBytes,
        chunkCount: deltaChunkCount,
      }
    : null,
  historyEntries: history.points.length,
  reportPath,
  historyPath,
  summaryPath,
}

mkdirSync(dirname(historyPath), { recursive: true })
mkdirSync(dirname(reportPath), { recursive: true })
mkdirSync(dirname(summaryPath), { recursive: true })
writeFileSync(historyPath, `${JSON.stringify(history, null, 2)}\n`, 'utf8')
writeFileSync(reportPath, markdown, 'utf8')
writeFileSync(summaryPath, `${JSON.stringify(summary, null, 2)}\n`, 'utf8')

console.log('[build-chunk-report]', JSON.stringify(summary, null, 2))

if (failOnBudget && (oversizedJsChunks.length > 0 || oversizedCssChunks.length > 0)) {
  process.exit(1)
}
