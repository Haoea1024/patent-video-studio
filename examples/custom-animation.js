// Runnable interface example: size-selective sieving. Use only when supported by the patent.
window.drawPatentCustom=function(v,t){
  if(v.key!=='sieve')throw Error('Unknown custom visual key: '+v.key);
  g.save();
  const y=680;
  for(let i=0;i<12;i++)panel(104+i*43,y,27,18,AM,'#9b713f',3);
  for(let i=0;i<14;i++){
    const small=i%3!==0,u=(t*.25+i*.071)%1,x=137+(i%11)*43;
    const yy=small?465+u*415:465+Math.min(u*415,195);
    const r=small?4:15;
    g.fillStyle=small?TE:AM;g.beginPath();g.arc(x,yy,r,0,Math.PI*2);g.fill();
  }
  fit('大颗粒截留',360,423,29,AM,580,24);
  fit('小颗粒通过',360,930,29,TE,580,24);
  g.restore();
};
