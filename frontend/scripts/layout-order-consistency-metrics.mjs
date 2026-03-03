#!/usr/bin/env node
import { mkdirSync, readFileSync } from 'node:fs'
import { dirname, resolve } from 'node:path'
import { spawnSync } from 'node:child_process'

const args = new Set(process.argv.slice(2))
const thresholdArg = process.argv.find((arg) => arg.startsWith('--threshold='))
const threshold = thresholdArg ? Number(thresholdArg.split('=')[1]) : 100
const failOnThreshold = args.has('--fail-on-threshold')

if (!Number.isFinite(threshold) || threshold < 0 || threshold > 100) {
  console.error(`[layout-order] invalid threshold: ${thresholdArg}`)
  process.exit(1)
}

const projectRoot = resolve(process.cwd())
const reportPath = resolve(projectRoot, '.tmp/layout-order-consistency-vitest.json')
mkdirSync(dirname(reportPath), { recursive: true })

const vitestArgs = [
  'vitest',
  'run',
  'src/platform/layout/layoutOrderConsistency.contract.test.ts',
  '--reporter=json',
  '--outputFile',
  reportPath
]

const run = spawnSync('npx', vitestArgs, {
  cwd: projectRoot,
  stdio: 'inherit',
  shell: process.platform === 'win32'
})

if (run.status !== 0) {
  console.error('[layout-order] contract test run failed.')
  process.exit(run.status || 1)
}

let parsed
try {
  parsed = JSON.parse(readFileSync(reportPath, 'utf8'))
} catch (error) {
  console.error('[layout-order] failed to parse vitest json report:', error)
  process.exit(1)
}

const total =
  Number(parsed?.numTotalTests) ||
  Number(parsed?.numTotalTestSuites) ||
  0
const passed = Number(parsed?.numPassedTests) || 0
const consistency = total > 0 ? Number(((passed / total) * 100).toFixed(2)) : 0
const meetsThreshold = consistency >= threshold

const summary = {
  metric: 'layoutOrderConsistency',
  scope: 'designer-preview-vs-runtime-contract',
  threshold,
  totalCases: total,
  passedCases: passed,
  failedCases: Math.max(total - passed, 0),
  consistency,
  meetsThreshold
}

console.log('[layout-order]', JSON.stringify(summary, null, 2))

if (failOnThreshold && !meetsThreshold) {
  console.error(
    `[layout-order] consistency ${consistency}% is below threshold ${threshold}%.`
  )
  process.exit(1)
}
