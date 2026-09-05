// Run: node tools/tests/search.mjs, then open the printed URL.
import { createServer } from 'node:http'
import { readFileSync } from 'node:fs'
import ts from 'typescript'

const source = readFileSync(new URL('../../src/search/search.ts', import.meta.url), 'utf8')
const compiled = ts
  .transpileModule(source, {
    compilerOptions: { target: ts.ScriptTarget.ES2022, module: ts.ModuleKind.ES2022 },
  })
  .outputText.replace(/^import .*getSiteConfig.*\n/m, '')
const checks = `
const assert = (condition, message) => { if (!condition) throw new Error(message) }
const wait = () => new Promise(resolve => setTimeout(resolve, 200))
const fixture = () => {
  const input = document.createElement('input'), list = document.createElement('ul'), status = document.createElement('p')
  document.body.append(input, status, list)
  initSearch({ searchInput: input, resultsContainer: list, statusElement: status, searchJsonUrl: '/index', noResultsText: '没有匹配结果' })
  const type = value => { input.value = value; input.dispatchEvent(new Event('input')) }
  return { input, list, status, type }
}
const data = Array.from({length: 151}, (_, i) => ({title: 'LeetCode ' + i, url: '/post/' + i, question_id: String(i), frequency: i}))
let requests = 0
window.fetch = async () => { requests++; return {ok:true, json:async()=>data} }
try {
  const all = fixture()
  all.type('  leetcode  ')
  await wait()
  assert(all.list.querySelectorAll('li a').length === 151, 'Show every match, including those past 100')
  assert(all.status.textContent === '共找到 151 篇文章', 'Show the actual total')
  assert(all.list.querySelector('.search-freq').textContent === '频率 150', 'Label frequency and preserve ranking')
  assert(all.list.lastElementChild.textContent.includes('频率 0'), 'Keep zero frequencies visible')
  all.type('no-such-result')
  await wait()
  assert(all.status.textContent === '共找到 0 篇文章', 'Show zero count')
  all.type('')
  assert(all.list.children.length === 0 && all.status.textContent === '', 'Clear immediately')
  assert(requests === 1, 'Reuse loaded index')

  let resolveFetch
  requests = 0
  window.fetch = () => { requests++; return new Promise(resolve => { resolveFetch = resolve }) }
  const race = fixture()
  race.type('LeetCode 1')
  await wait()
  race.type('LeetCode 150')
  resolveFetch({ok:true, json:async()=>data})
  await wait()
  assert(race.list.querySelectorAll('li a').length === 1 && race.list.textContent.includes('LeetCode 150'), 'Stale search must not overwrite newest input')
  assert(requests === 1, 'Share in-flight index load')

  window.fetch = () => new Promise(resolve => { resolveFetch = resolve })
  const closed = fixture()
  closed.type('leetcode')
  await wait()
  closed.input.value = ''
  closed.status.textContent = ''
  resolveFetch({ok:true, json:async()=>data})
  await wait()
  assert(closed.list.children.length === 0 && closed.status.textContent === '', 'Closing search must not restore old results')

  let fail = true
  window.fetch = async () => {
    if (fail) { fail = false; throw new Error('offline') }
    return {ok:true,json:async()=>[{title:'<img src=x onerror=alert(1)>',url:'/safe',frequency:0}]}
  }
  const retry = fixture()
  retry.type('img')
  await wait()
  assert(retry.status.textContent === '搜索数据加载失败', 'Report index failures')
  retry.type('img')
  await wait()
  assert(retry.list.querySelectorAll('a').length === 1 && !retry.list.querySelector('img'), 'Retry and escape result text')
  document.querySelector('output').textContent = 'PASS: full count, frequency, trimming, cache, clear, stale responses, close, retry and escaping'
} catch (error) {
  document.querySelector('output').textContent = 'FAIL: ' + error.message
  throw error
}
`
const html = `<!doctype html><meta charset="utf-8"><title>Search checks</title>
<output>Running…</output><script type="module">${compiled}\n${checks}</script>`
createServer((_request, response) => {
  response.writeHead(200, { 'Content-Type': 'text/html; charset=utf-8' })
  response.end(html)
}).listen(4013, '127.0.0.1', () => console.log('Open http://127.0.0.1:4013 — Ctrl+C to stop'))
