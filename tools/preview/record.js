// 使い方：node tools/preview/record.js ep001_disco 出力.webm（リポジトリ直下で http サーバ :8765 を起動しておく）
const {chromium}=require('playwright');(async()=>{const [ep,out]=process.argv.slice(2);const b=await chromium.launch();
const c=await b.newContext({viewport:{width:1920,height:1080},recordVideo:{dir:require('path').dirname(out),size:{width:1280,height:720}}});
const p=await c.newPage();await p.goto(`http://127.0.0.1:8765/tools/preview/player.html?ep=${ep}`);
await p.waitForFunction(()=>document.title==='done',null,{timeout:1200000});const v=p.video();await c.close();await v.saveAs(out);await b.close();})();
