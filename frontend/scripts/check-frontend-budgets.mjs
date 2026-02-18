#!/usr/bin/env node

import { existsSync, readdirSync, readFileSync, statSync } from 'node:fs'
import path from 'node:path'

const rootDir = process.cwd()
const distAssetsDir = path.join(rootDir, 'dist', 'assets')
const srcDir = path.join(rootDir, 'src')

const entryBundleBudgetBytes = Number(process.env.FRONTEND_ENTRY_BUNDLE_BUDGET_BYTES ?? 700 * 1024)
const maxSourceLines = Number(process.env.FRONTEND_MAX_SOURCE_LINES ?? 1900)

function formatKiB(bytes) {
  return `${(bytes / 1024).toFixed(1)} KiB`
}

function walkFiles(directory) {
  const entries = readdirSync(directory, { withFileTypes: true })
  const files = []

  for (const entry of entries) {
    const fullPath = path.join(directory, entry.name)
    if (entry.isDirectory()) {
      files.push(...walkFiles(fullPath))
      continue
    }
    if (entry.isFile()) {
      files.push(fullPath)
    }
  }

  return files
}

const failures = []

if (!existsSync(distAssetsDir)) {
  failures.push('Missing dist/assets. Run `npm run build` before checking budgets.')
}

let jsAssets = []
if (existsSync(distAssetsDir)) {
  jsAssets = walkFiles(distAssetsDir)
    .filter((file) => file.endsWith('.js'))
    .map((file) => ({
      file,
      size: statSync(file).size,
      rel: path.relative(rootDir, file),
      name: path.basename(file),
    }))
    .sort((a, b) => b.size - a.size)

  const entryChunk = jsAssets.find((asset) => asset.name.startsWith('index-'))
  if (!entryChunk) {
    failures.push('Unable to find entry chunk matching dist/assets/index-*.js.')
  } else if (entryChunk.size > entryBundleBudgetBytes) {
    failures.push(
      `Entry bundle budget exceeded: ${entryChunk.rel} is ${formatKiB(entryChunk.size)} (limit ${formatKiB(entryBundleBudgetBytes)}).`
    )
  }
}

if (!existsSync(srcDir)) {
  failures.push('Missing src directory. Cannot check source file size budget.')
}

let sourceFiles = []
if (existsSync(srcDir)) {
  sourceFiles = walkFiles(srcDir)
    .filter((file) => file.endsWith('.ts') || file.endsWith('.tsx'))
    .filter((file) => !file.includes(`${path.sep}src${path.sep}api${path.sep}generated${path.sep}`))
    .filter((file) => !/\.(test|spec)\.tsx?$/.test(file))
    .map((file) => {
      const content = readFileSync(file, 'utf8')
      const lineCount = content.length === 0 ? 0 : content.split(/\r?\n/).length
      return {
        file,
        rel: path.relative(rootDir, file),
        lineCount,
      }
    })
    .sort((a, b) => b.lineCount - a.lineCount)

  const largestSourceFile = sourceFiles[0]
  if (largestSourceFile && largestSourceFile.lineCount > maxSourceLines) {
    failures.push(
      `Source file size budget exceeded: ${largestSourceFile.rel} has ${largestSourceFile.lineCount} lines (limit ${maxSourceLines}).`
    )
  }
}

if (jsAssets.length > 0) {
  const topBundles = jsAssets.slice(0, 5)
  console.log('Top JS bundles:')
  for (const bundle of topBundles) {
    console.log(`  - ${bundle.rel}: ${formatKiB(bundle.size)}`)
  }
}

if (sourceFiles.length > 0) {
  const largest = sourceFiles[0]
  console.log(`Largest non-generated source file: ${largest.rel} (${largest.lineCount} lines)`)
}

if (failures.length > 0) {
  console.error('\nFrontend budget checks failed:')
  for (const failure of failures) {
    console.error(`  - ${failure}`)
  }
  process.exit(1)
}

console.log('\nFrontend budget checks passed.')
