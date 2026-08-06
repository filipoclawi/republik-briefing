document.addEventListener('DOMContentLoaded',()=>{
  const progress=document.querySelector('.progress');
  const update=()=>{const max=document.documentElement.scrollHeight-innerHeight;const pct=max>0?(scrollY/max)*100:0;progress.style.width=`${pct}%`};
  addEventListener('scroll',update,{passive:true});update();
  document.querySelectorAll('[data-filter]').forEach(button=>button.addEventListener('click',()=>{
    const filter=button.dataset.filter;
    document.querySelectorAll('[data-filter]').forEach(x=>{x.classList.toggle('active',x===button);x.setAttribute('aria-pressed',String(x===button))});
    let visible=0;document.querySelectorAll('.item-card[data-type]').forEach(card=>{const show=filter==='all'||card.dataset.type===filter;card.hidden=!show;if(show)visible++});
    const status=document.querySelector('#result-count');if(status)status.textContent=`${visible} item${visible===1?'':'s'}`;
  }));
  const all=document.querySelector('[data-filter="all"]');if(all)all.click();
  document.documentElement.dataset.ready='true';
});
