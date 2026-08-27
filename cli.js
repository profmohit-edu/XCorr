#!/usr/bin/env node
const fs=require('node:fs'),core=require('./core.js'),paths=process.argv.slice(2);if(!paths.length){console.error('Usage: node cli.js analyzer1.json analyzer2.json [...]');process.exit(1)}const inputs=paths.map(name=>({name,data:JSON.parse(fs.readFileSync(name,'utf8'))}));process.stdout.write(JSON.stringify(core.analyze(inputs),null,2)+'\n');
