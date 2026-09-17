const LB=document.getElementById('lb'),LBI=document.getElementById('lbi');
let G=[],GI=0;
function openLB(list,i){G=list;GI=i;LBI.src=G[GI];LB.classList.add('on');document.body.style.overflow='hidden';}
function closeLB(){LB.classList.remove('on');document.body.style.overflow='';}
function navLB(d){GI=(GI+d+G.length)%G.length;LBI.src=G[GI];}
document.querySelectorAll('.gcell').forEach(c=>c.onclick=()=>openLB(window.__G,c.dataset.i));
document.querySelectorAll('.post .body img').forEach(im=>im.onclick=()=>{LBI.src=im.getAttribute('data-full')||im.src;LB.classList.add('on');G=[];document.body.style.overflow='hidden';});
/* dropdown nav: click to toggle open (so you can scroll inside), click outside to close */
document.querySelectorAll('.nav-dd').forEach(dd=>{
  const trig=dd.querySelector('.dd-trigger');
  trig.addEventListener('click',e=>{e.stopPropagation();
    const open=dd.classList.contains('open');
    document.querySelectorAll('.nav-dd.open').forEach(o=>o.classList.remove('open'));
    if(!open)dd.classList.add('open');
  });
  trig.addEventListener('keydown',e=>{if(e.key==='Enter'||e.key===' '){e.preventDefault();trig.click();}});
});
document.addEventListener('click',()=>document.querySelectorAll('.nav-dd.open').forEach(o=>o.classList.remove('open')));
LB.onclick=e=>{if(e.target===LB)closeLB();};
document.addEventListener('keydown',e=>{if(e.key==='Escape')closeLB();if(e.key==='ArrowRight')navLB(1);if(e.key==='ArrowLeft')navLB(-1);});
