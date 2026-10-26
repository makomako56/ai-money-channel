const {chromium}=require('playwright');(async()=>{const b=await chromium.launch();const p=await b.newPage({viewport:{width:1920,height:1080}});
const dir=process.argv[2];for(let i=1;i<=13;i++){const n=String(i).padStart(2,'0');await p.goto('file://'+process.cwd()+'/'+n+'.html');await p.waitForTimeout(250);await p.screenshot({path:dir+'/'+n+'.png'});}await b.close();})();
