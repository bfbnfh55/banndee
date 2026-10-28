'use strict';
function renderReview(){
  const root=$('reviewRows');root.replaceChildren();
  for(const r of stocks.filter(r=>r.status==='review')){
    const item=el('article');item.append(el('strong',r.product_id+' · '+r.product_name),el('p',r.reasons.join(' / ')));
    const b=el('button','ดูหลักฐาน / ทบทวน');b.onclick=()=>openStock(r);item.append(b);root.append(item);
  }
  if(!root.children.length)root.append(el('p',stocks.length?'ไม่มีรายการที่ต้องทบทวน':'ยังไม่มีข้อมูล กรุณาโหลดสต็อกให้สำเร็จก่อน'));
}
async function setupPolicy(r){
  $('policyTools').hidden=false;
  $('policyMin').value=r.min_qty??'';$('policyTarget').value=r.target_qty??'';$('policyLead').value=r.lead_days??'';
  $('reviewer').value='';$('policyReason').value='';$('simulation').replaceChildren();$('policyMessage').textContent='';
  $('policyTime').textContent=r.mode==='demo'?'สาธิตย้อนหลัง: เวลาใช้นโยบาย 31 ก.ค. 2026 08:00; เก็บเวลาบันทึกจริงแยกต่างหาก ไม่เปลี่ยนเวลาสต็อก':'นโยบายใช้เวลาบันทึกจริง สต็อกเก่ายังคงถูกหยุด';
  $('policyHistory').replaceChildren(el('p','กำลังโหลดประวัติ…'));
  try{
    const history=await api(`/api/policy-history/${encodeURIComponent(r.product_id)}?mode=${r.mode}&location=${encodeURIComponent(r.location_id)}`);
    if(selected!==r||editing)return;
    $('policyHistory').replaceChildren(el('h3','ประวัติทบทวนนโยบาย'));
    for(const h of history){const a=JSON.parse(h.payload);$('policyHistory').append(el('p',`${h.at} · v${a.after.version} · ${a.after.reviewer} · ขั้นต่ำ ${a.before.min_qty??'ไม่ผ่าน'} → ${a.after.min_qty} / เป้าหมาย ${a.before.target_qty??'ไม่ผ่าน'} → ${a.after.target_qty} · ${a.after.reason}`));}
    if(!history.length)$('policyHistory').append(el('p','ยังไม่มีการทบทวนที่บันทึกไว้'));
  }catch(e){$('policyHistory').textContent=e.message;}
}
function policyBody(){
  for(const id of ['policyMin','policyTarget','policyLead'])if(!$(id).reportValidity())throw new Error('กรอกตัวเลขนโยบายให้ครบ');
  return {product_id:selected.product_id,location_id:selected.location_id,mode:selected.mode,
    min_qty:Number($('policyMin').value),target_qty:Number($('policyTarget').value),lead_days:Number($('policyLead').value),
    version:selected.policy_version,reviewer:$('reviewer').value,reason:$('policyReason').value};
}
$('simulate').onclick=async()=>{
  $('simulate').disabled=true;$('simulation').replaceChildren();
  try{if($('outage').checked)throw new Error('บริการสต็อกไม่พร้อม');const result=await api('/api/what-if','POST',policyBody());
    $('simulation').append(el('p',`เดิม: ${labels[result.before.status]} เติม ${result.before.suggested_qty} → สมมติ: ${labels[result.after.status]} เติม ${result.after.suggested_qty}`,'callout'),el('p',result.assumption,'footnote'));
  }catch(e){$('simulation').textContent=e.message;}finally{$('simulate').disabled=false;}
};
$('policyForm').onsubmit=async e=>{
  e.preventDefault();$('savePolicy').disabled=true;
  try{
    if($('outage').checked)throw new Error('กรุณาปิดการจำลองบริการไม่พร้อมก่อน');
    const result=await api('/api/policy-reviews','POST',policyBody());
    const fresh=await api(`/api/risks/${encodeURIComponent(result.product_id)}?mode=${result.mode}&location=${encodeURIComponent(result.location_id)}`);
    stocks=stocks.map(r=>r.product_id===fresh.product_id&&r.location_id===fresh.location_id?fresh:r);
    $('atRisk').textContent=stocks.filter(r=>['low','out'].includes(r.status)).length;
    $('reviewCount').textContent=stocks.filter(r=>r.status==='review').length;
    renderStocks();$('detail').close();openStock(fresh);
    $('policyMessage').textContent=`บันทึกและอ่านกลับแล้ว v${fresh.policy_version} · ${labels[fresh.status]}`;
    notice('บันทึกนโยบายแล้ว ข้อมูล raw และรายการกักกันเดิมยังคงอยู่');
  }catch(err){$('policyMessage').textContent=err.message;}finally{$('savePolicy').disabled=false;}
};
async function loadProject(){
  try{const data=await api('/api/project'),root=$('sourceComparison');
    for(const r of data.raw_files){const block=el('div');block.append(el('h3',r.file),el('p',`${r.rows} แถว · ${r.matches_teacher?'ตรงกับไฟล์อาจารย์ทุกไบต์':'ไม่ตรงกับต้นฉบับ'}`),el('pre',`SHA-256: ${r.sha256}`));root.append(block);}
    root.append(el('p','เพิ่มใหม่: replenishment_policy.csv 85 แถว ก่อนทำความสะอาด → 79 แถวใช้ได้ + 5 แถวกักกัน และตัดแถวซ้ำ 1 แถว','callout'));
    root.append(el('p','ข้อมูล orders, order_lines, customers, support_tickets และ delay_policy ของอาจารย์ไม่ได้ใช้ในหัวข้อนี้ โค้ด StockGuard เป็นแอปคนละชุดกับตัวอย่าง FastAPI/Gradio ของอาจารย์'));
  }catch(e){$('sourceComparison').textContent=e.message;}
}
async function loadQuarantine(){
  try{const q=await api('/api/quality');const box=el('div');box.append(el('h3','รายการกักกันจากขั้นตอนเตรียมข้อมูล'),el('p','หลักฐานต้นทางคงเดิม แม้มีนโยบายทบทวนใหม่แล้ว ให้ดูสถานะปัจจุบันที่คิวทบทวน'));
    for(const r of q.quarantine)box.append(el('p',`${r.product_id} / ${r.location_id} · ${r.reason} · ขั้นต่ำ ${r.min_qty||'(ว่าง)'} / เป้าหมาย ${r.target_qty}`));$('quality').append(box);
  }catch(e){notice(e.message,true);}
}
renderReview();loadProject();loadQuarantine();

api('/api/health').then(h=>{$('storageNote').textContent=h.temporary_session?'โหมดซ้อมแยกฐานข้อมูล: ข้อมูลที่สร้าง/แก้ไขจะถูกทิ้งเมื่อปิดเซิร์ฟเวอร์ ใช้ run.py แบบปกติเมื่อต้องการเก็บข้อมูลข้ามการเปิดระบบ':'โหมดบันทึกถาวร: คำขอและนโยบายที่ทบทวนเก็บใน SQLite และเรียกกลับได้หลังปิดเปิดระบบ';}).catch(e=>{$('storageNote').textContent=e.message;});
