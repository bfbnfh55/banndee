// Optional browser verification: npm install playwright; npx playwright install chromium
// Then: node tests/browser_smoke.cjs (Python must be available)
const { chromium }=require('playwright');
const fs=require('fs'),os=require('os'),path=require('path'),{spawn}=require('child_process');
const root=path.resolve(__dirname,'..'),temp=fs.mkdtempSync(path.join(os.tmpdir(),'stockguard-ui-'));
fs.cpSync(root,temp,{recursive:true,filter:src=>!src.includes('node_modules')&&!src.includes('__pycache__')&&!src.endsWith('.sqlite3')});
const server=spawn(process.env.PYTHON||'python',['-u','run.py','--port','0'],{cwd:temp});
const checks=[],errors=[];
function check(name,input,expected,actual){checks.push({name,input,expected,actual,result:expected===actual?'PASS':'FAIL'});if(expected!==actual)throw new Error(name+': '+actual);}
(async()=>{
 let browser;
 try{
  const url=await new Promise((resolve,reject)=>{const timer=setTimeout(()=>reject(new Error('startup timeout')),10000);server.stdout.on('data',b=>{const m=b.toString().match(/http:\/\/127\.0\.0\.1:\d+/);if(m){clearTimeout(timer);resolve(m[0]);}});server.on('error',reject);});
  browser=await chromium.launch({headless:true});const page=await browser.newPage({viewport:{width:1360,height:950}});page.on('pageerror',e=>errors.push(e.message));
  await page.goto(url);await page.waitForFunction(()=>document.getElementById('total').textContent==='82');
  check('initial inventory','open home','82',await page.locator('#total').innerText());
  await page.locator('#search').fill('SKU-0001');await page.locator('#stockRows button').click();
  check('suggested quantity','open SKU-0001','25',await page.locator('#quantity').inputValue());
  await page.locator('#note').fill('browser test');await page.locator('#save').click();await page.waitForFunction(()=>document.getElementById('notice').textContent.includes('เรียกกลับแล้ว'));
  check('create readback','save draft 25',true,(await page.locator('#requestRows').innerText()).includes('25'));
  await page.locator('#requestRows button').click();await page.locator('#quantity').fill('28');await page.locator('#note').fill('<img src=x onerror=alert(1)>');await page.locator('#save').click();
  await page.waitForFunction(()=>document.getElementById('notice').textContent.includes('เวอร์ชัน 2'));
  await page.reload();await page.locator('[data-tab=requests]').click();await page.locator('#requestRows button').click();
  check('persist and edit','reload saved draft','28',await page.locator('#quantity').inputValue());
  check('XSS rendered safely','HTML note shown as text',0,await page.locator('#detail img').count());
  check('audit trail','create plus edit',true,(await page.locator('#history').innerText()).includes('update'));
  await page.locator('.close').click();await page.locator('[data-tab=inventory]').click();await page.locator('#search').fill('SKU-0005');await page.locator('#stockRows button').click();
  check('ambiguous policy UI','SKU-0005',false,await page.locator('#requestForm').isVisible());await page.locator('.close').click();
  await page.locator('#mode').selectOption('live');await page.waitForFunction(()=>document.getElementById('reviewCount').textContent==='82');
  check('stale live mode','switch to current clock','82',await page.locator('#reviewCount').innerText());
  await page.locator('#outage').check();await page.waitForFunction(()=>document.getElementById('notice').textContent.includes('503'));
  check('503 clears stale table','simulate failure',0,await page.locator('#stockRows button').count());
  await page.locator('#outage').uncheck();await page.locator('#mode').selectOption('demo');await page.waitForFunction(()=>document.getElementById('total').textContent==='82');await page.locator('#search').fill('');
  if(process.env.SCREENSHOT_PATH)await page.screenshot({path:process.env.SCREENSHOT_PATH,fullPage:true});
  await page.setViewportSize({width:390,height:844});
  check('mobile viewport','390px',true,await page.evaluate(()=>document.documentElement.scrollWidth<=window.innerWidth));
  check('JS console','all flows',0,errors.length);
 }catch(e){checks.push({name:'runner',result:e.message.includes("Executable doesn't exist")?'BLOCKED':'FAIL',actual:e.message});process.exitCode=1;}
 finally{if(browser)await browser.close();server.kill();await new Promise(r=>server.once('exit',r));fs.rmSync(temp,{recursive:true,force:true});const result={executed_at:new Date().toISOString(),checks};fs.writeFileSync(path.join(root,'test_results/browser_results.json'),JSON.stringify(result,null,2));console.log(JSON.stringify(result,null,2));}
})();
