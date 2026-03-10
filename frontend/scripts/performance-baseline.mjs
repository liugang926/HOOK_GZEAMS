#!/usr/bin/env node
/**
 * performance-baseline.mjs
 *
 * Runs the Playwright page performance spec, collects metrics from test
 * attachments, calculates quantiles, writes to history JSON + Markdown report.
 *
 * Usage:
 *   node scripts/performance-baseline.mjs [options]
 *
 * Options:
 *   --project <name>       Playwright project (default: chromium)
 *   --target-tti <ms>      Target interactive time (default: 3000)
 *   --target-fcp <ms>      Target FCP (default: 1500)
 *   --history <path>       History JSON path
 *   --report <path>        Markdown report path
 *   --input-json <path>    Skip Playwright, read from existing JSON
 *   --fail-on-target       Exit 1 if any metric exceeds target
 */
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

const project = getArgValue('--project', 'chromium')
const targetTti = Number(getArgValue('--target-tti', '3000'))
const targetFcp = Number(getArgValue('--target-fcp', '1500'))
const failOnTarget = args.has('--fail-on-target')

const frontendRoot = process.cwd()
const repoRoot = resolve(frontendRoot, '..')

const historyPath = resolve(
    frontendRoot,
    getArgValue('--history', '../docs/reports/history/page-performance-history.json')
)
const reportPath = resolve(
    frontendRoot,
    getArgValue('--report', '../docs/reports/page-performance-baseline-latest.md')
)
const jsonPath = getArgValue('--input-json', '')
    ? resolve(frontendRoot, getArgValue('--input-json', ''))
    : resolve(frontendRoot, '.tmp/page-perf-playwright.json')

// ---------------------------------------------------------------------------
// Quantile helper
// ---------------------------------------------------------------------------
const quantile = (values, q) => {
    if (!values.length) return 0
    const sorted = [...values].sort((a, b) => a - b)
    const pos = (sorted.length - 1) * q
    const base = Math.floor(pos)
    const rest = pos - base
    if (sorted[base + 1] === undefined) return Number(sorted[base].toFixed(2))
    return Number((sorted[base] + rest * (sorted[base + 1] - sorted[base])).toFixed(2))
}

// ---------------------------------------------------------------------------
// Collect attachments from Playwright JSON report
// ---------------------------------------------------------------------------
const collectAttachments = (node, matches) => {
    if (!node || typeof node !== 'object') return
    if (Array.isArray(node)) {
        for (const item of node) collectAttachments(item, matches)
        return
    }
    if (Array.isArray(node.attachments)) {
        for (const attachment of node.attachments) {
            if (attachment?.name === 'page-perf-metrics' && attachment?.body) {
                matches.push(attachment.body)
            }
        }
    }
    for (const value of Object.values(node)) {
        collectAttachments(value, matches)
    }
}

// ---------------------------------------------------------------------------
// Step 1: Run Playwright (unless --input-json)
// ---------------------------------------------------------------------------
if (!getArgValue('--input-json', '')) {
    console.log(`[performance-baseline] running Playwright spec (project=${project})...`)
    const pwArgs = [
        'playwright',
        'test',
        'e2e/performance/page-performance-baseline.spec.ts',
        '--project',
        project,
        '--reporter=json',
    ]
    const run = spawnSync('npx', pwArgs, {
        cwd: frontendRoot,
        shell: process.platform === 'win32',
        encoding: 'utf8',
    })
    if (run.status !== 0) {
        process.stdout.write(run.stdout || '')
        process.stderr.write(run.stderr || '')
        console.error('[performance-baseline] Playwright failed. See output above.')
        process.exit(run.status || 1)
    }
    mkdirSync(dirname(jsonPath), { recursive: true })
    writeFileSync(jsonPath, run.stdout || '{}', 'utf8')
}

if (!existsSync(jsonPath)) {
    console.error(`[performance-baseline] telemetry json not found: ${jsonPath}`)
    process.exit(1)
}

// ---------------------------------------------------------------------------
// Step 2: Parse attachments
// ---------------------------------------------------------------------------
let payload
try {
    payload = JSON.parse(readFileSync(jsonPath, 'utf8'))
} catch (error) {
    console.error('[performance-baseline] failed to parse telemetry json:', error)
    process.exit(1)
}

const attachmentBodies = []
collectAttachments(payload, attachmentBodies)

const samples = []
for (const body of attachmentBodies) {
    try {
        const decoded = Buffer.from(body, 'base64').toString('utf8')
        const metrics = JSON.parse(decoded)
        if (metrics?.page && Number.isFinite(Number(metrics?.interactiveMs))) {
            samples.push(metrics)
        }
    } catch {
        // ignore malformed attachment
    }
}

if (samples.length === 0) {
    console.error('[performance-baseline] no page perf samples found in test output.')
    console.error('[performance-baseline] this usually means the spec did not produce attachments.')
    process.exit(1)
}

// ---------------------------------------------------------------------------
// Step 3: Compute per-page metrics
// ---------------------------------------------------------------------------
const now = new Date()
const timestamp = now.toISOString()
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

const pageMetrics = {}
for (const sample of samples) {
    const pageName = sample.page
    if (!pageMetrics[pageName]) {
        pageMetrics[pageName] = { interactiveMs: [], fcpMs: [], lcpMs: [] }
    }
    if (Number.isFinite(sample.interactiveMs)) pageMetrics[pageName].interactiveMs.push(sample.interactiveMs)
    if (Number.isFinite(sample.fcpMs)) pageMetrics[pageName].fcpMs.push(sample.fcpMs)
    if (Number.isFinite(sample.lcpMs)) pageMetrics[pageName].lcpMs.push(sample.lcpMs)
}

const point = {
    date,
    timestamp,
    commit,
    project,
    sampleCount: samples.length,
    targetTti,
    targetFcp,
    pages: {},
}

let allWithinTarget = true
for (const [pageName, metrics] of Object.entries(pageMetrics)) {
    const tti = quantile(metrics.interactiveMs, 0.5)
    const fcp = quantile(metrics.fcpMs, 0.5)
    const lcp = quantile(metrics.lcpMs, 0.5)
    const withinTarget = tti < targetTti && (fcp === 0 || fcp < targetFcp)
    if (!withinTarget) allWithinTarget = false
    point.pages[pageName] = {
        ttiMs: tti,
        fcpMs: fcp,
        lcpMs: lcp,
        withinTarget,
    }
}
point.allWithinTarget = allWithinTarget

// ---------------------------------------------------------------------------
// Step 4: Update history
// ---------------------------------------------------------------------------
let history = {
    metric: 'pagePerformanceBaseline',
    unit: 'ms',
    source: 'frontend/e2e/performance/page-performance-baseline.spec.ts',
    points: [],
}

if (existsSync(historyPath)) {
    try {
        const parsed = JSON.parse(readFileSync(historyPath, 'utf8'))
        if (Array.isArray(parsed?.points)) {
            history = parsed
        }
    } catch (error) {
        console.error('[performance-baseline] failed to parse history file:', error)
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
    metric: 'pagePerformanceBaseline',
    points: points.slice(-120),
}

mkdirSync(dirname(historyPath), { recursive: true })
writeFileSync(historyPath, `${JSON.stringify(history, null, 2)}\n`, 'utf8')

// ---------------------------------------------------------------------------
// Step 5: Generate Markdown report
// ---------------------------------------------------------------------------
const pageRows = Object.entries(point.pages)
    .map(
        ([pageName, m]) =>
            `| ${pageName} | ${m.ttiMs} | ${m.fcpMs} | ${m.lcpMs} | ${m.withinTarget ? '✅' : '❌'} |`
    )
    .join('\n')

const latestHistoryRows = points
    .slice(-10)
    .map((p) => {
        const pagesSummary = Object.entries(p.pages || {})
            .map(([name, m]) => `${name}:${m.ttiMs}ms`)
            .join(', ')
        return `| ${p.date} | ${p.commit} | ${pagesSummary} | ${p.allWithinTarget ? '✅' : '❌'} |`
    })
    .join('\n')

const markdown = `# Page Performance Baseline (Latest)

- **Date**: ${date}
- **Commit**: ${commit}
- **Project**: ${project}
- **Target TTI**: < ${targetTti}ms
- **Target FCP**: < ${targetFcp}ms
- **All within target**: ${point.allWithinTarget ? '✅ Yes' : '❌ No'}
- **History entries**: ${history.points.length}

## Current Metrics

| Page | TTI (ms) | FCP (ms) | LCP (ms) | Within Target |
| --- | --- | --- | --- | --- |
${pageRows || '| - | - | - | - | - |'}

## Trend (Last 10 Runs)

| Date | Commit | Pages TTI | Within Target |
| --- | --- | --- | --- |
${latestHistoryRows || '| - | - | - | - |'}
`

mkdirSync(dirname(reportPath), { recursive: true })
writeFileSync(reportPath, markdown, 'utf8')

// ---------------------------------------------------------------------------
// Output
// ---------------------------------------------------------------------------
const summary = {
    metric: 'pagePerformanceBaseline',
    latest: point,
    historyEntries: history.points.length,
    historyPath,
    reportPath,
}

console.log('[performance-baseline]', JSON.stringify(summary, null, 2))

if (failOnTarget && !allWithinTarget) {
    console.error('[performance-baseline] FAIL: one or more pages exceed target thresholds.')
    process.exit(1)
}
