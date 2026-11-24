const { execFileSync } = require('node:child_process');
const fs = require('node:fs');
const path = require('node:path');
if (!/^https:\/\//.test(process.env.NEXT_PUBLIC_API_URL || '')) {
  throw new Error('Static builds require NEXT_PUBLIC_API_URL pointing to the HTTPS API /api/v1');
}
execFileSync(process.execPath, [require.resolve('next/dist/bin/next'), 'build'], {
  stdio: 'inherit', env: { ...process.env, DSR_STATIC_EXPORT: '1', NEXT_PUBLIC_OFFLINE_SHELL: '1' },
});
// Only exported, public application assets enter this cache. API responses and
// authentication tokens are never intercepted or stored by the service worker.
function walk(dir) {
  return fs.readdirSync(dir, { withFileTypes: true }).flatMap(entry => entry.isDirectory()
    ? walk(path.join(dir, entry.name)) : [path.join(dir, entry.name)]);
}
const assets = walk('out').filter(file => /\.(html|txt|js|css|woff2?|webp|png|svg|ico)$/.test(file))
  .map(file => '/' + file.slice(4).split(path.sep).join('/'));
const version = fs.readFileSync('.next/BUILD_ID', 'utf8').trim();
const template = fs.readFileSync('scripts/service-worker.js', 'utf8');
fs.writeFileSync('out/sw.js', `const CACHE = ${JSON.stringify('dsr-shell-' + version)};\nconst ASSETS = ${JSON.stringify(assets)};\n${template}`);
console.log(`Prepared offline application shell: ${assets.length} public assets`);
