#!/usr/bin/env node
import { existsSync, readFileSync } from 'node:fs'
import { resolve } from 'node:path'

const argv = process.argv.slice(2)
const args = new Set(argv)

const getArgValue = (name, fallback) => {
  const idx = argv.indexOf(name)
  if (idx < 0 || idx + 1 >= argv.length) return fallback
  return argv[idx + 1]
}

const failOnActive = args.has('--fail-on-active')
const jsonOnly = args.has('--json')
const ledgerArg = getArgValue('--ledger', '../docs/reports/i18n-p1-defect-ledger.json')
const frontendRoot = process.cwd()
const ledgerPath = resolve(frontendRoot, ledgerArg)

if (!existsSync(ledgerPath)) {
  console.error(`[i18n-defects] ledger file not found: ${ledgerPath}`)
  process.exit(1)
}

let ledger
try {
  ledger = JSON.parse(readFileSync(ledgerPath, 'utf8'))
} catch (error) {
  console.error('[i18n-defects] invalid ledger json:', error)
  process.exit(1)
}

const defects = Array.isArray(ledger?.defects) ? ledger.defects : []
const allowedActiveRaw = Number(ledger?.policy?.allowedActive)
const allowedActive = Number.isFinite(allowedActiveRaw) ? allowedActiveRaw : 0
const closedStatuses = new Set(['resolved', 'closed', 'done', 'fixed', 'released', 'verified'])

const normalizeSeverity = (defect) =>
  String(defect?.severity ?? defect?.priority ?? defect?.level ?? '')
    .trim()
    .toUpperCase()

const normalizeStatus = (defect) =>
  String(defect?.status ?? defect?.state ?? 'open')
    .trim()
    .toLowerCase()

const isP1Severity = (severity) =>
  severity === 'P1' ||
  severity === '1' ||
  severity === 'SEV1' ||
  severity === 'SEV-1' ||
  severity === 'S1'

const activeP1Defects = defects.filter((defect) => {
  const severity = normalizeSeverity(defect)
  const status = normalizeStatus(defect)
  return isP1Severity(severity) && !closedStatuses.has(status)
})

const summary = {
  metric: 'i18nP1Defects',
  releaseWindow: ledger?.releaseWindow ?? null,
  policy: ledger?.policy ?? null,
  ledgerPath,
  generatedAt: ledger?.generatedAt ?? null,
  totalDefects: defects.length,
  activeP1Defects: activeP1Defects.length,
  allowedActive,
  meetsTarget: activeP1Defects.length <= allowedActive,
  samples: activeP1Defects.slice(0, 10).map((defect) => ({
    id: defect?.id ?? null,
    title: defect?.title ?? defect?.summary ?? null,
    severity: normalizeSeverity(defect),
    status: normalizeStatus(defect)
  }))
}

if (!jsonOnly) {
  console.log(
    `[i18n-defects] activeP1=${summary.activeP1Defects} allowed=${summary.allowedActive} meetsTarget=${summary.meetsTarget}`
  )
}
console.log(JSON.stringify(summary, null, 2))

if (failOnActive && !summary.meetsTarget) {
  console.error('[i18n-defects] active P1 defects exceed policy allowance.')
  process.exit(1)
}
