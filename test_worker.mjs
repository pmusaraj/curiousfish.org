import test from 'node:test';
import assert from 'node:assert/strict';
import { readFile } from 'node:fs/promises';
// Import as ESM without requiring package.json for this otherwise static site.
const source = await readFile(new URL('./worker.js', import.meta.url), 'utf8');
const { default: worker, prefersMarkdown } = await import(`data:text/javascript;base64,${Buffer.from(source).toString('base64')}`);

for (const [accept, expected] of [
  ['', false], ['*/*', false], ['text/*', false],
  ['text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8', false],
  ['text/markdown', true], ['TEXT/MARKDOWN; charset=utf-8', true],
  ['text/markdown, text/html', true],
  ['text/markdown;q=0.5,text/html', false],
  ['text/markdown;q=0.9,text/html;q=0.5', true],
  ['text/markdown;q=0,*/*', false],
  ['text/markdown;q=invalid,text/html', false],
  ['text/markdown;q=0.5,text/*;q=0.8', false],
  ['text/markdown;q=0.5,text/html;q=0,*/*', true],
]) {
  test(`Accept ${JSON.stringify(accept)} chooses ${expected ? 'Markdown' : 'HTML'}`, () => {
    assert.equal(prefersMarkdown(accept), expected);
  });
}

const seen = [];
const env = { ASSETS: { async fetch(request) {
  const pathname = new URL(request.url).pathname;
  seen.push({ pathname, method: request.method });
  const md = pathname.endsWith('.md');
  return new Response(request.method === 'HEAD' ? null : md ? '# Penar Musaraj' : '<h1>Penar Musaraj</h1>', {
    headers: { 'Content-Type': md ? 'application/octet-stream' : 'text/html', Vary: 'Accept-Encoding' },
  });
} } };

for (const pathname of ['/', '/index.html']) {
  test(`${pathname} negotiates both formats, including HEAD`, async () => {
    for (const [accept, format] of [['text/markdown', 'markdown'], ['text/html', 'html']]) {
      const response = await worker.fetch(new Request(`https://example.com${pathname}`, { headers: { Accept: accept } }), env);
      assert.match(response.headers.get('Content-Type'), new RegExp(`text/${format}`));
      assert.equal(response.headers.get('Vary'), 'Accept-Encoding, Accept');
      assert.equal(response.headers.get('Cache-Control'), 'no-store');
      assert.match(await response.text(), format === 'markdown' ? /^# Penar/ : /^<h1>/);
      const head = await worker.fetch(new Request(`https://example.com${pathname}`, { method: 'HEAD', headers: { Accept: accept } }), env);
      assert.equal(await head.text(), '');
      assert.match(head.headers.get('Content-Type'), new RegExp(`text/${format}`));
    }
  });
}

test('direct Markdown route and unrelated assets', async () => {
  const response = await worker.fetch(new Request('https://example.com/index.md'), env);
  assert.equal(response.headers.get('Content-Type'), 'text/markdown; charset=utf-8');
  assert.match(await response.text(), /^# Penar/);
  await worker.fetch(new Request('https://example.com/style.css', { headers: { Accept: 'text/markdown' } }), env);
  assert.equal(seen.at(-1).pathname, '/style.css');
});

test('private paths and unsupported methods cannot reach assets', async () => {
  for (const pathname of ['/notable.md', '/templates/index.html', '/profile-stats.json', '/templates/private.html']) {
    const count = seen.length;
    assert.equal((await worker.fetch(new Request(`https://example.com${pathname}`), env)).status, 404);
    assert.equal(seen.length, count);
  }
  assert.equal((await worker.fetch(new Request('https://example.com/', { method: 'POST' }), env)).status, 405);
});
