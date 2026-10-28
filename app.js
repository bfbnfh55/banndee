'use strict';
const $ = id => document.getElementById(id);
const labels = {low:'สต็อกต่ำ',out:'สินค้าหมด',review:'ต้องทบทวน',ok:'เพียงพอ'};
let stocks=[], requests=[], selected=null, editing=null, loadVersion=0;
const el=(tag,text,className)=>{const n=document.createElement(tag);if(text!==undefined)n.textContent=text;if(className)n.className=className;return n;};
async function api(path, method='GET', body){
  const controller=new AbortController(), timer=setTimeout(()=>controller.abort(),8000);
  try{
    const r=await fetch(path,{method,headers:body?{'Content-Type':'application/json'}:{},body:body?JSON.stringify(body):undefined,signal:controller.signal});
    const data=await r.json();if(!r.ok)throw new Error(`${r.status} · ${data.error}`);return data;
  }catch(e){if(e.name==='AbortError')throw new Error('เชื่อมต่อหมดเวลา กรุณาลองใหม่');if(e instanceof TypeError)throw new Error('เชื่อมต่อ API ไม่ได้ ตรวจสอบว่า run.py ยังทำงานอยู่');throw e;}
  finally{clearTimeout(timer);}
}
function notice(text,error=false){$('notice').textContent=text;$('notice').className='notice'+(error?' error':'');$('notice').hidden=!text;}
function cell(row,content){const td=el('td');if(content instanceof Node)td.append(content);else td.textContent=content??'—';row.append(td);return td;}
function badge(status){return el('span',labels[status]||status,'badge '+status);}
function showTab(name){for(const n of ['inventory','requests','quality','review','project'])$(n).hidden=n!==name;document.querySelectorAll('.tab').forEach(b=>b.classList.toggle('active',b.dataset.tab===name));}
async function load(){
  const ticket=++loadVersion;
  $('detail').close();stocks=[];renderStocks();['total','atRisk','reviewCount'].forEach(id=>$(id).textContent='—');
  $('modeNote').textContent=$('mode').value==='demo'?'ย้อนหลัง 31 ก.ค. 2026 • ไม่ใช่สต็อกปัจจุบัน':'ใช้เวลาปัจจุบัน • ข้อมูลเก่าจะหยุดเพื่อทบทวน';
  try{
    const data=await api(`/api/risks?mode=${$('mode').value}&unavailable=${$('outage').checked?'1':'0'}`);
    if(ticket!==loadVersion)return;stocks=data;
    $('total').textContent=stocks.length;$('atRisk').textContent=stocks.filter(r=>['low','out'].includes(r.status)).length;$('reviewCount').textContent=stocks.filter(r=>r.status==='review').length;
    notice($('mode').value==='demo'?'โหมดสาธิตย้อนหลัง: ใช้ข้อมูลวันที่ 31 ก.ค. 2026 และนโยบายสังเคราะห์ คำขอที่สร้างเป็นข้อมูลสาธิต':'โหมดปัจจุบัน: ระบบตรวจอายุสต็อกไม่เกิน 24 ชั่วโมง และนโยบายไม่เกิน 30 วัน');renderStocks();
  }catch(e){if(ticket===loadVersion){stocks=[];renderStocks();notice(e.message,true);}}
}
function renderStocks(){
  const q=$('search').value.toLowerCase(), f=$('filter').value;
  const data=stocks.filter(r=>(f==='all'||r.status===f)&&`${r.product_id} ${r.product_name}`.toLowerCase().includes(q));
  const order={out:0,low:1,review:2,ok:3};data.sort((a,b)=>order[a.status]-order[b.status]||a.product_id.localeCompare(b.product_id));
  $('stockRows').replaceChildren();
  for(const r of data){const row=el('tr'),name=el('div',r.product_name);name.append(el('small',r.product_id+' · '+r.category));cell(row,name);cell(row,r.available_qty);cell(row,r.min_qty);cell(row,r.suggested_qty);cell(row,badge(r.status));const btn=el('button','ดูหลักฐาน');btn.onclick=()=>openStock(r);cell(row,btn);$('stockRows').append(row);}
  if(!data.length){const row=el('tr');const td=cell(row,stocks.length?'ไม่พบสินค้าตามคำค้นหรือสถานะที่เลือก':'ไม่มีข้อมูลให้แสดง กรุณาโหลดข้อมูลอีกครั้ง');td.colSpan=6;$('stockRows').append(row);}
  if(typeof renderReview==='function')renderReview();
  $('rowCount').textContent=`แสดง ${data.length} จาก ${stocks.length} รายการ · สต็อกอ้างอิง 31 ก.ค. 2026 เวลา 06:00 น. (UTC+07)`;
}
function evidenceView(r){
  const root=$('evidence');root.replaceChildren(badge(r.status));const grid=el('div',undefined,'evidencegrid');
  for(const [label,val] of [['คงเหลือ',r.available_qty],['แนะนำเติม',r.suggested_qty],['ขั้นต่ำ / เป้าหมาย',`${r.min_qty??'—'} / ${r.target_qty??'—'}`],['ระยะเวลาจัดหา (สมมติ)',`${r.lead_days??'—'} วัน`]]){const b=el('div');b.append(el('small',label),el('strong',val??'ยังสรุปไม่ได้'));grid.append(b);}root.append(grid);
  root.append(el('p',`เวลาสต็อก: ${r.as_of}`,'footnote'),el('p',`ประเมิน ณ: ${r.evaluated_at} · โหมด ${r.mode}`,'footnote'),el('p',`นโยบาย ณ: ${r.policy_updated_at??'ไม่ผ่านการตรวจสอบ'}`,'footnote'));
  root.append(el('p',r.policy_assumption,'callout'));
  if(r.reasons.length)root.append(el('p','หยุดเพื่อทบทวน: '+r.reasons.join(' / '),'notice error'));
  else root.append(el('p',r.status==='ok'?'ปริมาณสูงกว่าเกณฑ์ขั้นต่ำ ยังไม่เสนอเติม':`หลักเกณฑ์: คงเหลือ ≤ ขั้นต่ำ; แนะนำเติม = เป้าหมาย − คงเหลือ = ${r.target_qty} − ${r.available_qty} = ${r.suggested_qty}`,'callout'));
  if(r.policy_review)root.append(el('p',`นโยบายทบทวน v${r.policy_version} · ${r.policy_review.reviewer} · บันทึกจริง ${r.policy_review.saved_at} · ${r.policy_review.reason}`,'callout'));
  for(const source of r.sources)root.append(el('div',source,'footnote'));
}
function openStock(r){selected=r;editing=null;$('detailTitle').textContent=r.product_id+' · '+r.product_name;evidenceView(r);$('quantity').value=r.suggested_qty||1;$('note').value='';$('formMessage').textContent='';$('history').replaceChildren();$('cancelRequest').hidden=true;$('save').textContent='บันทึกคำขอ';$('requestForm').hidden=!['low','out'].includes(r.status);$('detail').showModal();if(typeof setupPolicy==='function')setupPolicy(r);}
async function loadRequests(){
  try{requests=await api('/api/requests');$('draftCount').textContent=requests.filter(r=>r.status==='draft').length;$('requestRows').replaceChildren();
    for(const r of requests){const row=el('tr');cell(row,`#${r.id} · ${r.product_id}`);cell(row,r.quantity);cell(row,r.mode==='demo'?'สาธิตย้อนหลัง':'ปัจจุบัน');cell(row,r.status==='draft'?'ฉบับร่าง':'ยกเลิกแล้ว');cell(row,r.version);const btn=el('button','เปิด / แก้ไข');btn.onclick=()=>editRequest(r.id);cell(row,btn);$('requestRows').append(row);}
    if(!requests.length){const tr=el('tr');cell(tr,'ยังไม่มีคำขอ เลือกสินค้าสต็อกต่ำเพื่อสร้างคำขอ').colSpan=6;$('requestRows').append(tr);}
  }catch(e){notice(e.message,true);}
}
async function editRequest(id){try{
  $('policyTools').hidden=true;editing=await api('/api/requests/'+id);selected=JSON.parse(editing.evidence);$('detailTitle').textContent=`คำขอ #${editing.id} · ${editing.product_id}`;evidenceView(selected);
  $('evidence').append(el('p','หลักฐานขณะสร้างคำขอ · ระบบตรวจความพร้อมอีกครั้งก่อนบันทึกการแก้ไข','footnote'));
  $('quantity').value=editing.quantity;$('note').value=editing.note;$('formMessage').textContent='';$('save').textContent='บันทึกการแก้ไข';$('requestForm').hidden=editing.status!=='draft';$('cancelRequest').hidden=editing.status!=='draft';
  const history=await api(`/api/requests/${id}/history`);$('history').replaceChildren(el('h3','ประวัติการเปลี่ยนแปลง'));
  for(const h of history){const d=JSON.parse(h.payload);$('history').append(el('p',`${h.at} · ${h.action} · จำนวน ${d.quantity} · ${d.note||'ไม่มีหมายเหตุ'}`));}$('detail').showModal();
}catch(e){notice(e.message,true);}}
async function saveRequest(cancel=false){
  const button=$('save');button.disabled=true;$('cancelRequest').disabled=true;
  try{
    if($('outage').checked&&!cancel)throw new Error('กำลังจำลองบริการไม่พร้อม กรุณาปิดการจำลองและโหลดข้อมูลก่อนบันทึก');
    const body={quantity:Number($('quantity').value),note:$('note').value};let saved;
    if(editing){body.version=editing.version;body.status=cancel?'cancelled':'draft';saved=await api('/api/requests/'+editing.id,'PUT',body);}
    else{Object.assign(body,{product_id:selected.product_id,location_id:selected.location_id,mode:selected.mode});saved=await api('/api/requests','POST',body);}
    const readback=await api('/api/requests/'+saved.id);$('detail').close();await loadRequests();showTab('requests');notice(`บันทึกสำเร็จและเรียกกลับแล้ว: คำขอ #${readback.id} · จำนวน ${readback.quantity} · เวอร์ชัน ${readback.version}`);
  }catch(e){$('formMessage').textContent=e.message;}finally{button.disabled=false;$('cancelRequest').disabled=false;}
}
async function loadQuality(){try{const q=await api('/api/quality'),s=q.summary;$('qualitySummary').textContent=`นโยบายสังเคราะห์ ${s.policy_before} แถว → ใช้ได้ ${s.policy_after} แถว | กักกัน ${s.quarantined_rows} แถว | สต็อกที่ไม่มีนโยบายผ่านการตรวจ ${s.inventory_without_policy} รายการ | ปัญหาในตาราง generated เป็นกรณีทดสอบที่ตั้งใจสร้าง`;
  $('qualityRows').replaceChildren();for(const r of q.log){const tr=el('tr'),d=el('div',r.issue);d.append(el('small',`${r.source} : แถว ${r.row}`));cell(tr,d);cell(tr,r.key);cell(tr,r.before);cell(tr,`${r.after||'ไม่แก้ค่าที่กำกวม'} · ${r.action}`);$('qualityRows').append(tr);}
}catch(e){notice(e.message,true);}}
document.querySelectorAll('.tab').forEach(b=>b.onclick=()=>showTab(b.dataset.tab));$('search').oninput=renderStocks;$('filter').onchange=renderStocks;$('mode').onchange=load;$('outage').onchange=load;$('refresh').onclick=load;$('reloadRequests').onclick=loadRequests;
$('requestForm').onsubmit=e=>{e.preventDefault();saveRequest();};$('cancelRequest').onclick=()=>{if(confirm('ยกเลิกคำขอนี้? รายการและประวัติยังคงอยู่ แต่จะแก้ไขต่อไม่ได้'))saveRequest(true);};
load();loadRequests();loadQuality();
