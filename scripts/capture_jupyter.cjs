// Screenshots of the real Jupyter Notebook interface, with executed input/output.
const fs = require('node:fs');
const path = require('node:path');
const {chromium} = require(process.env.PLAYWRIGHT_MODULE || 'playwright');
(async()=>{
 const root=path.resolve(__dirname,'..');
 const config=JSON.parse(fs.readFileSync(path.join(root,'tmp/jupyter/server.json'),'utf8'));
 const browser=await chromium.launch({channel:'chrome',headless:true});
 const page=await browser.newPage({viewport:{width:1440,height:1300},deviceScaleFactor:1.5});
 const port=config.ServerApp.port;
 await page.goto(`http://127.0.0.1:${port}/notebooks/google_local_analysis.ipynb?token=${encodeURIComponent(config.IdentityProvider.token)}`);
 await page.locator('.jp-Notebook .jp-CodeCell').first().waitFor({timeout:60000});
 await page.waitForFunction(()=>document.querySelectorAll('.jp-Notebook .jp-OutputArea-output').length>10);
 if(!process.argv.includes('--no-run')){
  await page.getByRole('menuitem',{name:'Run',exact:true}).click();
  await page.getByRole('menuitem',{name:'Run All Cells',exact:true}).click();
 }
 await page.waitForFunction(()=>{
  const cells=[...document.querySelectorAll('.jp-Notebook .jp-CodeCell')];
  return cells.length===11 && cells.every(cell=>/^\[\d+\]:/.test(cell.querySelector('.jp-InputPrompt')?.textContent?.trim()||'')) &&
   cells[cells.length-1].querySelector('img');
 },{},{timeout:180000});
 if(await page.locator('.jp-OutputArea-error').count()) throw new Error('Notebook contains execution errors');
 await page.keyboard.press('Control+s');
 const folder=path.join(root,'evidence/jupyter'); fs.mkdirSync(folder,{recursive:true});
 const cells=page.locator('.jp-Notebook .jp-Cell');
 const captures=[
  [2,'01_data_quality',3], [4,'02_preprocessing',5],
  [6,'03_places_over_three',7], [8,'04_closed_and_operating',9],
  [10,'05_top_twenty_phrases',11], [12,'06_it_specialists',13],
  [14,'07_most_reviewed_places',15], [16,'08_sentiment_counts',17],
  [18,'09_rating_comparison',20]
 ];
 for(const [heading,name,last] of captures){
  await cells.nth(heading).evaluate(el=>el.scrollIntoView({block:'start'}));
  await page.waitForFunction(index=>{
   const c=document.querySelectorAll('.jp-Notebook .jp-Cell')[index];
   return c && c.getBoundingClientRect().height>20;
  },last);
  const bounds=await cells.nth(last).boundingBox();
  if(bounds && bounds.y+bounds.height>1300){
   await page.setViewportSize({width:1440,height:Math.min(2200,Math.ceil(bounds.y+bounds.height+35))});
   await cells.nth(heading).evaluate(el=>el.scrollIntoView({block:'start'}));
  }
  const end=await cells.nth(last).boundingBox();
  const height=Math.min(page.viewportSize().height,Math.max(350,Math.ceil(end.y+end.height+8)));
  await page.screenshot({path:path.join(folder,name+'.png'),clip:{x:0,y:0,width:1440,height}});
  await page.setViewportSize({width:1440,height:1300});
  console.log('Captured '+name);
 }
 await browser.close();
})();
