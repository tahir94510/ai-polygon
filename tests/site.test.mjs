import {test} from 'node:test';
import assert from 'node:assert/strict';
import {execFileSync} from 'node:child_process';
import {readFileSync,existsSync} from 'node:fs';
import {join} from 'node:path';
import {fileURLToPath} from 'node:url';
const root=fileURLToPath(new URL('../',import.meta.url));
test('static Vercel build includes validated catalog',()=>{
 execFileSync(process.execPath,[join(root,'scripts/build.mjs')]);
 assert.ok(existsSync(join(root,'dist/index.html')));
 const catalog=JSON.parse(readFileSync(join(root,'dist/catalog.json'),'utf8'));
 assert.equal(catalog.repository,'https://github.com/tahir94510/ai-polygon');
 assert.equal(catalog.projects.length,6);
 assert.equal(catalog.tracks.length,2);
 assert.equal(catalog.report.trials,80);
 assert.equal(catalog.report.evaluation,'public_not_blind');
});
test('English site does not claim blind or frontier tests',()=>{
 const html=readFileSync(join(root,'dist/index.html'),'utf8');
 assert.match(html,/<html lang="en">/);
 assert.match(html,/not a blind benchmark/);
 assert.match(html,/a current frontier-model comparison/);
 assert.match(html,/Vercel displays results; it does not train models/);
 assert.match(html,/Could not load benchmark data/);
});
