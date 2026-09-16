import { readFileSync, writeFileSync, readdirSync, mkdirSync, copyFileSync, rmSync } from 'node:fs';
import { join } from 'node:path';
import { fileURLToPath } from 'node:url';
const root = fileURLToPath(new URL('../', import.meta.url));
const load = file => JSON.parse(readFileSync(join(root, file), 'utf8'));
const report = load('results/reference-demo.json');
if (report.schema !== 'polygon-public-demo-v1' || report.evaluation !== 'public_not_blind' ||
    report.trials !== 80 || !Array.isArray(report.summary) || report.summary.length !== 16) {
  throw new Error('Reference report is missing, incomplete or invalid.');
}
const names = readdirSync(join(root, 'projects')).filter(name => {
  try { return Boolean(load(`projects/${name}/manifest.json`).track); } catch { return false; }
});
const projects = names.sort().map(id => ({id, ...load(`projects/${id}/manifest.json`)}));
const tracks = [
  {id:'regression',name:'Tabular regression',suites:['linear','nonlinear','shift'],metric:'rmse',direction:'min'},
  {id:'classification',name:'Binary classification',suites:['linear','xor'],metric:'accuracy',direction:'max'}
];
for (const row of report.summary) {
  if (!projects.some(p => p.id === row.project && p.track === row.track) ||
      !tracks.some(t => t.id === row.track && t.suites.includes(row.suite) && t.metric === row.metric)) {
    throw new Error('Report refers to an unknown project, suite or metric.');
  }
}
const dir = join(root, 'dist'); rmSync(dir,{recursive:true,force:true}); mkdirSync(dir,{recursive:true});
copyFileSync(join(root,'site/index.html'),join(dir,'index.html'));
writeFileSync(join(dir,'catalog.json'),JSON.stringify({schema:'polygon-catalog-v1',
  repository:'https://github.com/tahir94510/ai-polygon',tracks,projects,report},null,2));
console.log(`Built ${projects.length} projects, ${tracks.length} tracks, ${report.trials} trials.`);
