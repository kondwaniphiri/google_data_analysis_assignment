// Capture genuine browser screenshots of the generated analysis evidence pages.
const fs = require('node:fs');
const path = require('node:path');
const {pathToFileURL} = require('node:url');
const {chromium} = require(process.env.PLAYWRIGHT_MODULE || 'playwright');
(async()=>{
 const root=path.resolve(__dirname,'..');
 const browser=await chromium.launch({channel:'chrome',headless:true});
 const page=await browser.newPage({viewport:{width:900,height:300},deviceScaleFactor:1.5});
 for(const name of fs.readdirSync(path.join(root,'evidence')).filter(x=>x.endsWith('.html'))){
  await page.goto(pathToFileURL(path.join(root,'evidence',name)).href);
  await page.screenshot({path:path.join(root,'evidence',name.replace('.html','.png')),fullPage:true});
 }
 await browser.close();
})();
