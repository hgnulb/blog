// Run: node tools/tests/code-tabs.mjs, then open the printed URL.
import { createServer } from 'node:http'
import { readFileSync } from 'node:fs'
import ts from 'typescript'

const source = readFileSync(new URL('../../src/content/code-block.ts', import.meta.url), 'utf8')
const compiled = ts.transpileModule(source, {
  compilerOptions: { target: ts.ScriptTarget.ES2022, module: ts.ModuleKind.ES2022 },
}).outputText

const checks = `
const assert = (condition, message) => { if (!condition) throw new Error(message) }
const block = (lang, text) => {
  const wrapper = document.createElement('div')
  wrapper.className = 'language-' + lang + ' highlighter-rouge'
  const pre = document.createElement('pre')
  const code = document.createElement('code')
  code.textContent = text
  pre.append(code)
  wrapper.append(pre)
  return wrapper
}
const root = document.querySelector('.article-inner')
const java = block('java', 'class Solution {}\\n')
const go = block('go', 'package main\\nfunc main() {}\\n')
const python = block('python', 'print("hello")\\n')
const javaAgain = block('java', 'class Other {}\\n')
const explanation = document.createElement('p')
explanation.textContent = 'Different solution: keep this boundary.'
const separate = block('go', 'package separate\\n')
const heading = document.createElement('h3')
heading.textContent = 'Second group'
const secondJava = block('java', 'class Second {}\\n')
const secondGo = block('go', 'package second\\n')
root.append(java, go, python, javaAgain, explanation, separate, heading, secondJava, secondGo)
let copied = ''
Object.defineProperty(navigator, 'clipboard', { configurable: true, value: {
  writeText: async text => { copied = text }
}})
try {
  const before = [...root.querySelectorAll('pre code')].map(e => e.textContent)
  initCodeBlocks()
  assert(root.querySelectorAll('.code-tabs').length === 2, 'Group only adjacent, distinct languages')
  assert(!javaAgain.closest('.code-tabs') && !separate.closest('.code-tabs'), 'Keep repeated language and prose boundaries')
  const group = java.closest('.code-tabs')
  const tabs = [...group.querySelectorAll('[role="tab"]')]
  assert(tabs.map(e => e.textContent).join(',') === 'Java,Go,Python', 'Use actual language labels')
  assert(!java.hidden && go.hidden && python.hidden, 'Show only first panel initially')
  tabs[1].click()
  assert(java.hidden && !go.hidden && python.hidden, 'Click switches active code')
  assert(tabs[1].getAttribute('aria-selected') === 'true' && tabs[0].tabIndex === -1, 'Update accessible selection')
  assert(document.getElementById(tabs[1].getAttribute('aria-controls')) === go, 'Connect tabs and panels')
  group.querySelector('.code-block-copy').click()
  await Promise.resolve()
  assert(copied === 'package main\\nfunc main() {}\\n', 'Copy current language only, without line numbers')
  tabs[1].dispatchEvent(new KeyboardEvent('keydown', { key: 'ArrowRight', bubbles: true }))
  assert(!python.hidden && document.activeElement === tabs[2], 'Arrow key switches and focuses tab')
  tabs[2].dispatchEvent(new KeyboardEvent('keydown', { key: 'Home', bubbles: true }))
  assert(!java.hidden && document.activeElement === tabs[0], 'Home returns to first tab')
  tabs[0].dispatchEvent(new KeyboardEvent('keydown', { key: 'ArrowLeft', bubbles: true }))
  assert(!python.hidden, 'Arrow key wraps')
  tabs[2].dispatchEvent(new KeyboardEvent('keydown', { key: 'End', bubbles: true }))
  assert(!python.hidden, 'End selects final tab')
  assert(!secondJava.hidden && secondGo.hidden, 'Groups switch independently')
  initCodeBlocks()
  assert(root.querySelectorAll('.code-tabs').length === 2, 'Initialization is idempotent')
  assert(group.querySelectorAll('.code-block-copy').length === 1, 'One copy control per group')
  assert(JSON.stringify(before) === JSON.stringify([...root.querySelectorAll('pre code')].map(e => e.textContent)), 'Preserve code text and order')
  document.querySelector('output').textContent = 'PASS: grouping, boundaries, keyboard, copy, independence, idempotence and code preservation'
} catch (error) {
  document.querySelector('output').textContent = 'FAIL: ' + error.message
  throw error
}
`
const html = `<!doctype html><meta charset="utf-8"><title>Code tabs checks</title>
<style>[hidden]{display:none}output{display:block;padding:1rem}</style>
<output>Running…</output><div class="article-inner"></div>
<script type="module">${compiled}\n${checks}</script>`
createServer((_request, response) => {
  response.writeHead(200, { 'Content-Type': 'text/html; charset=utf-8' })
  response.end(html)
}).listen(4012, '127.0.0.1', () => console.log('Open http://127.0.0.1:4012 — Ctrl+C to stop'))
