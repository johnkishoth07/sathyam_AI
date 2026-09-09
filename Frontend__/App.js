const API="http://127.0.0.1:8000";
async function api(path,opt={}){const r=await fetch(API+path,opt),t=await r.text();let d={};try{d=t?JSON.parse(t):{}}catch{}if(!r.ok)throw Error(d.detail||d.message||`HTTP ${r.status}`);return d}
function esc(v){return String(v??"").replace(/[&<>"']/g,m=>({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#39;"}[m]))}
function guard(){if(!localStorage.getItem("satyam_auth"))location.href="01_login.html"}
function logout(){localStorage.removeItem("satyam_auth");location.href="01_login.html"}
function nav(x){document.querySelectorAll(".nav a").forEach(a=>{if(a.dataset.page===x)a.classList.add("active")})}
function msg(id,t,c="info"){document.getElementById(id).innerHTML=`<div class="notice ${c}">${esc(t)}</div>`}
function tag(s){s=(s||"PENDING").toUpperCase();return `<span class="status ${s==="PASS"?"pass":s==="FAIL"?"fail":s==="REVIEW"?"review":"pending"}">${esc(s)}</span>`}
async function biddersSelect(id){try{let r=await api("/api/bidders");document.getElementById(id).innerHTML='<option value="">Select Bidder</option>'+r.map(b=>`<option value="${b.id}">${esc(b.company_name)} — ID ${b.id}</option>`).join("")}catch{document.getElementById(id).innerHTML='<option>Backend unavailable</option>'}}
