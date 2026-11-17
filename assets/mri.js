(function(){
// Project-specific explanatory animation; synthetic phantom, not clinical evidence.
const TAU=Math.PI*2;
function ellipse(x,y,rx,ry,col,rot=0){g.beginPath();g.ellipse(x,y,rx,ry,rot,0,TAU);g.fillStyle=col;g.fill()}
function glowDot(x,y,r=4,col=AM){g.save();g.shadowColor=col;g.shadowBlur=13;ellipse(x,y,r,r,col);g.restore()}
function phantomValue(x,y){let q=x*x/.72**2+y*y/.93**2;if(q>1)return 0;let z=.48;if(q>.84)z=.85;let ell=(cx,cy,rx,ry)=>(x-cx)**2/rx**2+(y-cy)**2/ry**2<1;if(ell(-.23,-.1,.2,.5))z=.23;if(ell(.23,-.1,.2,.5))z=.66;if(ell(0,.42,.15,.2))z=.92;if(ell(-.28,.48,.09,.13))z=.75;if(ell(.33,.38,.1,.1))z=.12;return z}
const PH=[];
for(let frame=0;frame<42;frame++){
 let cv=document.createElement('canvas');cv.width=cv.height=144;let cx=cv.getContext('2d'),im=cx.createImageData(144,144),e=1-frame/41;
 for(let j=0;j<144;j++)for(let i=0;i<144;i++){
  let x=(i-72)/66,y=(j-72)/66,z=phantomValue(x+e*.022*Math.sin(j*.22),y);
  let ghost=phantomValue(x,y+.42)*e*.16+phantomValue(x,y-.42)*e*.10;
  z=cl(z*(1-e*.15)+ghost+(rnd(j*144+i)-.5)*e*.20);
  let k=(j*144+i)*4;im.data[k]=z*235;im.data[k+1]=z*242;im.data[k+2]=z*244;im.data[k+3]=255;
 }cx.putImageData(im,0,0);PH.push(cv);
}
function phaseMap(x,y,w,t){g.save();rr(x,y,w,w,10);g.clip();for(let j=0;j<24;j++)for(let i=0;i<24;i++){let ph=i*.23+j*.16+Math.sin(t*.55)*2;g.fillStyle=`hsl(${185+Math.sin(ph)*43} 65% ${22+18*(.5+.5*Math.cos(ph))}%)`;g.fillRect(x+i*w/24,y+j*w/24,w/24+1,w/24+1)}for(let j=0;j<4;j++)for(let i=0;i<4;i++){let xx=x+(i+.5)*w/4,yy=y+(j+.5)*w/4,a=t*.9+i*.4+j*.25;line(xx,yy,xx+11*Math.cos(a),yy+11*Math.sin(a),IV,1.5);glowDot(xx,yy,1.5)}g.restore()}
function kspace(x,y,w,h,t,ratio=1){panel(x-5,y-5,w+10,h+10,TE,'#020b11',10);for(let j=0;j<32;j++){let active=j/32<ratio;for(let i=0;i<40;i++){let xx=(i-20)/20,yy=(j-16)/16,z=Math.exp(-(xx*xx*8+yy*yy*12))*.7+(.5+.5*Math.cos(i*.9+j*.23+t*.2))*.12;g.fillStyle=active?`rgba(${Math.round(60+160*z)},${Math.round(130+110*z)},${Math.round(155+80*z)},${.18+z})`:'rgba(50,80,95,.12)';g.fillRect(x+i*w/40,y+j*h/32,w/40-.6,h/32-.6)}}let yy=y+(t*.23%1)*h;line(x,yy,x+w,yy,AM,2)}
function hookDemo(t){scanner(260,585,.95,t);travel(365,570,492,570,t,5);network(535,570,142,220,t);text('物理模型',237,850,29,AM);text('智能重建',534,850,29,TE);for(let i=0;i<3;i++){let y=755+i*21;g.beginPath();for(let k=0;k<180;k++){let x=139+k*1.1,yy=y+Math.sin(k*.11-t*3+i)*8;k?g.lineTo(x,yy):g.moveTo(x,yy)}g.strokeStyle=i===1?AM:TE;g.lineWidth=1.5;g.stroke()}note('成像与数据流示意 · 非真实设备运行画面')}
function sensitivityMap(x,y,w){g.save();rr(x,y,w,w,10);g.clip();for(let j=0;j<28;j++)for(let i=0;i<28;i++){let u=i/27,v=j/27,z=Math.exp(-((u-.15)**2+(v-.45)**2)*3.2);g.fillStyle=`hsl(${188-z*35} 60% ${12+z*39}%)`;g.fillRect(x+i*w/28,y+j*w/28,w/28+1,w/28+1)}g.restore()}
function dataDemo(t){
 phantom(72,423,145,1);sensitivityMap(288,423,145);phaseMap(504,423,145,t+2.5);
 text('磁共振图像',144,604,24,IV);text('通道灵敏度',360,604,24,IV);text('运动相位',576,604,24,AM);
 // Static receive-coil sensitivity envelope drawn over the center map.
 for(let i=0;i<3;i++){g.strokeStyle='rgba(243,238,226,.55)';g.lineWidth=1.5;g.beginPath();g.ellipse(360,495,29+i*16,52+i*7,0,0,TAU);g.stroke()}
 [144,360,576].forEach(x=>travel(x,632,360,700,t,4));glowDot(360,704,10);
 for(let i=0;i<6;i++){let x=83+i*94,delay=i*.35,appear=sm(t,2+delay,2.6+delay);alpha(appear,()=>{let yy=766+Math.sin(t*1.2+i)*5;kspace(x,yy,80,96,t+i,1);text(String(i+1).padStart(2,'0'),x+40,889,18,MU,SANS)})}
 text('生成不同相位条件下的训练数据',360,946,27,AM);note('数据生成机制示意 · 色彩表示相位差异')
}
function tinyMatrix(x,y,w,t,mode){let n=7,sz=w/n;for(let j=0;j<n;j++)for(let i=0;i<n;i++){let z=mode===0?(.4+.5*Math.sin(i*.4+t)*Math.cos(j*.3)):mode===1?(rnd(i+j*7)>.8?1:.04):((j%3===Math.floor(t)%3)?1:.16);g.fillStyle=`rgba(${mode===1?'240,166,64':'92,194,201'},${cl(z,.08,.95)})`;g.fillRect(x+i*sz,y+j*sz,sz-2,sz-2)}}
function modulesDemo(t){let nodes=[[160,484,'低秩约束'],[560,484,'稀疏约束'],[360,812,'数据校验']];let ang=t*1.25;g.strokeStyle='rgba(92,194,201,.3)';g.lineWidth=2;g.beginPath();g.ellipse(360,635,211,173,0,0,TAU);g.stroke();for(let i=0;i<9;i++){let a=ang+i*TAU/9;glowDot(360+211*Math.cos(a),635+173*Math.sin(a),3)}
 nodes.forEach(([x,y,s],i)=>{panel(x-81,y-72,162,146,TE,'#091c27');tinyMatrix(x-43,y-53,86,t,i);text(s,x,y+50,25,IV)});
 let prog=sm(t,1.6,8.5);phantom(276,548,168,prog);text('迭代重建',360,745,25,AM);
 alpha(sm(t,6.8,7.4),()=>{panel(134,904,452,60,AM,'#14252b');for(let i=0;i<16;i++){let u=(t*.6+i/16)%1;alpha(1-u,()=>glowDot(156+u*150,934+(rnd(i)-.5)*32,2,TE))}text('末轮去噪',451,934,27,AM)});
 note('合成体模与模块作用示意 · 非实测效果')
}
function rebuildDemo(t){let p=sm(t,1,8.2);kspace(83,421,225,179,t,cl(t/2.5));text('采集数据',195,643,24,TE);network(520,506,173,150,t);text('已训练网络',519,643,24,AM);travel(330,506,414,506,t,4);travel(520,681,447,736,t,5);
 phantom(229,729,235,p);let xx=229+235*((t*.24)%1);g.save();g.beginPath();g.rect(229,729,235,235);g.clip();line(xx,729,xx,964,TE,2);g.restore();
 text('图像重建',135,844,24,IV);text('输出图像',575,844,24,AM);note('合成体模演示 · 不代表本专利实测效果')
}
function valueDemo(t){scanner(215,574,.73,t);panel(411,449,235,193,TE,'#07121c',12);phantom(467,465,135,1);line(527,647,527,682,MU,8);line(473,686,581,686,MU,6);travel(341,564,406,564,t,4);text('磁共振设备',207,761,27,IV);text('影像重建软件',528,761,27,IV);pill('小批量生产、工程应用阶段',360,899,592,AM);note('应用方向示意 · 成熟度依据专利手册')}
// Polished geometry and lighting shared by every MRI mode. No raster/service dependency.
function metal(x,y,w,h){let q=g.createLinearGradient(x,y,x+w,y+h);q.addColorStop(0,'#edf5f1');q.addColorStop(.26,'#b9cbd1');q.addColorStop(.55,'#638092');q.addColorStop(.8,'#c1d2d7');q.addColorStop(1,'#496174');return q}
function softHalo(x,y,r,col='92,194,201'){let q=g.createRadialGradient(x,y,0,x,y,r);q.addColorStop(0,`rgba(${col},.16)`);q.addColorStop(1,`rgba(${col},0)`);g.fillStyle=q;g.fillRect(x-r,y-r,r*2,r*2)}
function pathCurve(x,y,x2,y2){g.beginPath();g.moveTo(x,y);let bend=(y2-y)*.55;g.bezierCurveTo(x+(x2-x)*.18,y+bend,x2-(x2-x)*.18,y2-bend,x2,y2)}
function curvePoint(x,y,x2,y2,u){let b=(y2-y)*.55,v=1-u;return [v*v*v*x+3*v*v*u*(x+(x2-x)*.18)+3*v*u*u*(x2-(x2-x)*.18)+u*u*u*x2,v*v*v*y+3*v*v*u*(y+b)+3*v*u*u*(y2-b)+u*u*u*y2]}
function travel(x,y,x2,y2,t,n=6,col=AM){g.save();pathCurve(x,y,x2,y2);g.strokeStyle='rgba(92,194,201,.24)';g.lineWidth=2;g.stroke();for(let i=0;i<n;i++){let u=(t*.25+i/n)%1;for(let k=5;k>=0;k--){let a=curvePoint(x,y,x2,y2,cl(u-k*.009));alpha((1-k/6)*Math.sin(u*Math.PI),()=>glowDot(a[0],a[1],k?1.2:2.7,col))}}g.restore()}
function scanner(x,y,s,t){g.save();g.translate(x,y);g.scale(s,s);softHalo(0,0,230);ellipse(31,205,194,30,'rgba(0,0,0,.32)');ellipse(20,196,153,14,'rgba(92,194,201,.07)');
 // Short, extruded cylindrical housing; a shaded inner bore makes depth legible.
 ellipse(-28,-8,157,174,'#263f51');ellipse(-11,-4,156,174,metal(-160,-175,310,345));ellipse(5,0,145,166,metal(-145,-165,270,320));
 g.strokeStyle='rgba(242,249,245,.6)';g.lineWidth=1.5;g.beginPath();g.ellipse(5,0,144,165,0,0,TAU);g.stroke();
 let bore=g.createRadialGradient(-14,-20,4,5,1,116);bore.addColorStop(0,'#020910');bore.addColorStop(.62,'#071b28');bore.addColorStop(.85,'#3a5362');bore.addColorStop(1,'#a8bcc5');ellipse(5,0,103,126,bore);
 ellipse(-12,-4,75,105,'#04101a');g.save();g.shadowColor=AM;g.shadowBlur=14;g.strokeStyle='#ffd58a';g.lineWidth=2.8;g.beginPath();g.ellipse(5,0,106,129,0,0,TAU);g.stroke();g.restore();
 g.strokeStyle='rgba(243,250,247,.5)';g.lineWidth=1.3;g.beginPath();g.ellipse(5,0,114,139,0,Math.PI*.98,Math.PI*1.75);g.stroke();
 panel(-126,5,24,13,'#8af2ef','#245e6b',3);line(-121,11,-108,11,TE,2);
 // A table slab, padded top, side rail and pedestal; eased travel into the bore.
 let shift=9*Math.sin(t*.38),bx=shift*.58,by=shift;
 g.beginPath();g.moveTo(-43+bx,46+by);g.lineTo(42+bx,39+by);g.lineTo(185+bx,139+by);g.lineTo(63+bx,163+by);g.closePath();g.fillStyle=metal(-25,35,210,140);g.fill();
 g.beginPath();g.moveTo(63+bx,163+by);g.lineTo(185+bx,139+by);g.lineTo(185+bx,153+by);g.lineTo(63+bx,179+by);g.closePath();g.fillStyle='#496779';g.fill();
 g.beginPath();g.moveTo(-30+bx,45+by);g.lineTo(36+bx,43+by);g.lineTo(163+bx,137+by);g.lineTo(69+bx,155+by);g.closePath();g.fillStyle='#cedbdf';g.fill();line(66+bx,166+by,180+bx,143+by,TE,2.4);
 g.beginPath();g.moveTo(93,175+by);g.lineTo(139,165+by);g.lineTo(139,207);g.lineTo(92,215);g.closePath();g.fillStyle=metal(90,170,50,45);g.fill();ellipse(112,215,71,14,'#253f51');ellipse(110,211,64,10,'#527184');
 // Acquisition plane moves inside the bore, clipped to it.
 g.save();g.beginPath();g.ellipse(-12,-4,74,103,0,0,TAU);g.clip();let scan=-70+(t*.3%1)*145;let q=g.createLinearGradient(0,scan-18,0,scan+18);q.addColorStop(0,'rgba(92,194,201,0)');q.addColorStop(.5,'rgba(92,194,201,.3)');q.addColorStop(1,'rgba(92,194,201,0)');g.fillStyle=q;g.fillRect(-89,scan-18,170,36);ellipse(-12,scan,69,10,'rgba(144,245,242,.24)');g.restore();g.restore()}
function phantom(x,y,w,progress=1){g.save();softHalo(x+w/2,y+w/2,w*.8);g.shadowColor='rgba(0,0,0,.48)';g.shadowBlur=17;panel(x-8,y-8,w+16,w+16,'rgba(110,203,214,.5)','#030c13',17);g.shadowBlur=0;g.save();rr(x,y,w,w,12);g.clip();g.imageSmoothingEnabled=true;g.drawImage(PH[Math.round(cl(progress)*41)],x,y,w,w);g.restore();let q=g.createLinearGradient(x,y,x+w,y+w);q.addColorStop(0,'rgba(207,246,248,.07)');q.addColorStop(.45,'rgba(207,246,248,0)');g.fillStyle=q;rr(x,y,w,w,12);g.fill();g.strokeStyle='rgba(160,221,226,.5)';g.lineWidth=1;for(let [xx,yy,dx,dy] of [[x-3,y-3,1,1],[x+w+3,y-3,-1,1],[x-3,y+w+3,1,-1],[x+w+3,y+w+3,-1,-1]]){line(xx,yy,xx+13*dx,yy,'#4a8490',1);line(xx,yy,xx,yy+13*dy,'#4a8490',1)}g.restore()}
function network(cx,cy,w,h,t){softHalo(cx,cy,w*.85);let layers=[3,5,5,3],points=layers.map((n,l)=>Array.from({length:n},(_,j)=>[cx-w/2+l*w/3,cy+(j-(n-1)/2)*h/(n+1)]));for(let l=0;l<3;l++)for(let [j,a] of points[l].entries())for(let [k,b] of points[l+1].entries()){let pulse=(t*.5-l*.19+10)%1;line(...a,...b,`rgba(92,194,201,${.13+.08*Math.sin(t+j+k)})`,.8);if((j+k)%3===0){let u=cl(pulse);alpha(Math.sin(u*Math.PI),()=>glowDot(a[0]+(b[0]-a[0])*u,a[1]+(b[1]-a[1])*u,2.1))}}points.forEach((ps,l)=>ps.forEach((a,i)=>{let q=g.createRadialGradient(a[0]-1.5,a[1]-2,0,a[0],a[1],5.8);q.addColorStop(0,'#fff9df');q.addColorStop(.3,(i+l)%3?TE:AM);q.addColorStop(1,'#184859');ellipse(a[0],a[1],5.8,5.8,q);g.strokeStyle=`rgba(92,194,201,${.15+.15*Math.sin(t*2-l)})`;g.lineWidth=.8;g.beginPath();g.arc(a[0],a[1],9,0,TAU);g.stroke()}))}

window.drawMRI=(v,t)=>({acquisition:hookDemo,training:dataDemo,iteration:modulesDemo,reconstruction:rebuildDemo,application:valueDemo}[v.mode])(t);
})();
