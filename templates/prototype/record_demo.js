const {chromium}=require('playwright');(async()=>{const b=await chromium.launch();
const c=await b.newContext({viewport:{width:1920,height:1080},recordVideo:{dir:process.cwd()+'/vid',size:{width:1280,height:720}}});
const p=await c.newPage();await p.goto('file://'+process.cwd()+'/page.html');
await p.waitForFunction(()=>document.title==='done',null,{timeout:60000});await p.waitForTimeout(1200);
await c.close();await b.close();})();
