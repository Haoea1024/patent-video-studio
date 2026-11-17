#!/usr/bin/env python3
"""Data-driven patent video pipeline. No provider keys or host-specific paths."""
from pathlib import Path
import argparse, asyncio, base64, hashlib, importlib.util, json, math, os, re, shutil, subprocess, sys, time, wave

if hasattr(sys.stdout,'reconfigure'):sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr,'reconfigure'):sys.stderr.reconfigure(encoding='utf-8')

ROOT = Path(__file__).resolve().parents[1]
TYPES = {'flow','compare','sensor','thermal','separation','material','cards','image','cta'}
def read(p): return json.loads(Path(p).read_text(encoding='utf-8-sig'))
def write(p, data):
    p=Path(p);p.parent.mkdir(parents=True,exist_ok=True)
    p.write_text(json.dumps(data,ensure_ascii=False,indent=2),encoding='utf-8')
def digest(x): return hashlib.sha256(json.dumps(x,ensure_ascii=False,sort_keys=True).encode()).hexdigest()
def clean(s): return re.sub(r'[^\w\u4e00-\u9fff]','',s)
def asset(value, project):
    return (ROOT/value[7:]).resolve() if value.startswith('@skill/') else (Path(project).resolve().parent/value).resolve()
def ff():
    import imageio_ffmpeg
    return os.environ.get('PATENT_VIDEO_FFMPEG') or imageio_ffmpeg.get_ffmpeg_exe()
def run(args):
    p=subprocess.run([ff(),'-hide_banner','-y',*map(str,args)],capture_output=True)
    if p.returncode: raise RuntimeError(p.stderr.decode('utf-8',errors='replace')[-5000:])
    return p
def project(path):
    d=read(path);validate(d);return d
def validate(d):
    from jsonschema import Draft202012Validator
    errors=sorted(Draft202012Validator(read(ROOT/'references/project.schema.json')).iter_errors(d),key=lambda e:str(e.path))
    if errors: raise ValueError('\n'.join(f'{list(e.path)}: {e.message}' for e in errors[:15]))
    sources={s['id'] for s in d['sources']};facts={f['id']:f for f in d['facts']}
    if len(sources)!=len(d['sources']) or len(facts)!=len(d['facts']): raise ValueError('Duplicate source/fact ID')
    for f in facts.values():
        if f['source_id'] not in sources: raise ValueError('Unknown source: '+f['source_id'])
    for field in ['identity','maturity']:
        if d[field]['source_id'] not in sources: raise ValueError(field+' source_id missing')
    if d.get('contact') and d['contact']['source_id'] not in sources: raise ValueError('contact source_id missing')
    patent=d['identity'].get('patent_number','');digits=re.sub(r'\D','',patent)
    if d.get('closing_lines') and clean(''.join(d['closing_lines']))!=clean(d['title']):raise ValueError('closing_lines must reproduce the full title, only adding line breaks')
    ids=set()
    for s in d['scenes']:
        if s['id'] in ids: raise ValueError('Duplicate scene ID: '+s['id'])
        ids.add(s['id'])
        if not set(s['evidence_ids'])<=set(facts): raise ValueError(s['id']+': unknown evidence_ids')
        if re.search(r'CN\s*\d{6}|专利号|申请号|授权公告号',s['narration'],re.I) or (len(digits)>5 and digits in re.sub(r'\D','',s['narration'])):
            raise ValueError(s['id']+': remove patent number from narration')
        for chunk in split_phrases(s['narration']):
            if len(chunk)>36: raise ValueError(s['id']+': narration phrase >36 characters; add natural punctuation')
        v=s['visual'];kind=v['type']
        if kind in {'flow','cards','compare'} and not v.get('items'): raise ValueError(s['id']+': items required')
        if kind=='compare' and len(v['items'])!=2: raise ValueError(s['id']+': compare requires exactly 2 items')
        if kind=='image' and not v.get('path'): raise ValueError(s['id']+': image path required')
        if kind=='separation' and v.get('mode','oil_pass') not in {'oil_pass','water_pass'}: raise ValueError('Unknown separation mode')
        if kind=='thermal' and v.get('mode') not in {'hotspot','coil'}: raise ValueError('thermal requires mode hotspot or coil')
        if 'mode' in v and kind not in {'thermal','separation'}: raise ValueError(s['id']+': mode does not apply to this visual type')
    if d['scenes'][-1]['visual']['type']!='cta': raise ValueError('Last scene must be cta')
    if not d['cover'].get('image') and d['cover']['visual'] not in {s['visual']['type'] for s in d['scenes']}:raise ValueError('cover.visual must match a scene type')
    if d.get('music',{}).get('path') and not d['music'].get('credit'): raise ValueError('Music credit/license missing')
    return d
def split_phrases(text):
    return [re.sub(r'[，,。；;：:]','',s).strip() for s in re.split(r'(?<=[，,。！？!?；;：:])',text) if clean(s)]
def align(text,words,delay=.3):
    """Map punctuation-delimited captions to exact provider words. Reject guesses."""
    if clean(text)!=clean(''.join(w['text'] for w in words)):
        raise ValueError('Word timestamps do not match narration. Use correct text/audio; do not invent timings.')
    prev=0
    for w in words:
        if not (isinstance(w['start'],(int,float)) and isinstance(w['end'],(int,float))) or w['start']<prev-.02 or w['end']<=w['start']:
            raise ValueError('Invalid/nonmonotonic word timestamps')
        prev=w['end']
    caps=[];wi=0
    for chunk in split_phrases(text):
        target=clean(chunk);selected=[];acc=''
        while wi<len(words) and len(acc)<len(target):
            w=dict(words[wi]);w['start']+=delay;w['end']+=delay
            selected.append(w);acc+=clean(w['text']);wi+=1
        if acc!=target: raise ValueError('A word crosses caption punctuation. Fix provider word segmentation, not guessed timings.')
        caps.append({'text':chunk,'start':selected[0]['start'],'end':selected[-1]['end'],'words':selected})
    return caps
def duration(path):
    with wave.open(str(path)) as w:return w.getnframes()/w.getframerate()
def data_hash(d):return digest(d)
def checkpoint(d,out):
    tl=read(out/'timeline.json')
    if tl.get('project_hash')!=data_hash(d):raise ValueError('Project changed. Run audio again; stale voice/timeline cannot be rendered.')
    return tl
def launch(p):
    exe=os.environ.get('PATENT_VIDEO_CHROME')
    if exe:return p.chromium.launch(headless=True,executable_path=exe)
    try:return p.chromium.launch(headless=True)
    except Exception as first:
        for channel in ['msedge','chrome']:
            try:return p.chromium.launch(headless=True,channel=channel)
            except Exception:pass
        raise RuntimeError('No Chromium browser. Run: python -m playwright install chromium; or set PATENT_VIDEO_CHROME.') from first
def doctor():
    modules=['PIL','numpy','playwright','edge_tts','pypdf','pypdfium2','imageio_ffmpeg','jsonschema']
    result={'python':sys.version,'dependencies':{m:importlib.util.find_spec(m) is not None for m in modules},'browser':False,'ffmpeg':False,'font_check_is_advisory':'Inspect actual Chinese glyphs in rendered preview; browser font API may report fallback as available.'}
    try:result['ffmpeg']=run(['-version']).returncode==0
    except Exception as e:result['ffmpeg_error']=str(e)
    if result['dependencies']['playwright']:
        from playwright.sync_api import sync_playwright
        try:
            with sync_playwright() as p:
                b=launch(p);page=b.new_page();result['browser']=True
                result['font_candidates']={f:page.evaluate('(f)=>document.fonts.check(`32px "${f}"`)',f) for f in ['SimSun','Microsoft YaHei','Songti SC','Noto Serif CJK SC']}
                b.close()
        except Exception as e:result['browser_error']=str(e)
    print(json.dumps(result,ensure_ascii=False,indent=2))
    if not all(result['dependencies'].values()) or not result['browser'] or not result['ffmpeg']:raise RuntimeError('Doctor failed; see references/SETUP.md')
def extract(pdf,out,pages):
    from pypdf import PdfReader
    import pypdfium2 as pdfium
    out.mkdir(parents=True,exist_ok=True);reader=PdfReader(pdf)
    write(out/'index.json',{'pages':len(reader.pages),'input':str(Path(pdf).resolve())})
    (out/'document.txt').write_text('\n\n'.join(f'PDF PAGE {i+1}\n'+(p.extract_text() or '') for i,p in enumerate(reader.pages)),encoding='utf-8')
    if pages:
        doc=pdfium.PdfDocument(str(pdf))
        for n in [int(v) for v in pages.split(',')]:
            if not 1<=n<=len(reader.pages):raise ValueError('PDF page out of range')
            pg=doc[n-1];im=pg.render(scale=2).to_pil();im.save(out/f'page-{n:03}.png');pg.close()
        doc.close()
    print('Extracted text and requested pages:',out)
async def tts_scene(s,d,out,external):
    voice=d.get('voice',{});name=s['id'];target=out/'audio'/name;target.mkdir(parents=True,exist_ok=True)
    wav=target/'voice.wav';meta=target/'cache.json'
    if external:
        ext=read(external);item=ext['scenes'].get(name)
        if not item:raise ValueError('External audio missing scene '+name)
        f=(Path(external).resolve().parent/item['audio']).resolve()
        key=digest({'text':s['narration'],'file':hashlib.sha256(f.read_bytes()).hexdigest(),'words':item.get('words'),'captions':item.get('captions')})
        if not meta.exists() or read(meta).get('key')!=key or not wav.exists():run(['-i',f,'-ar','48000','-ac','1',wav])
        if item.get('words'):
            caps=align(s['narration'],item['words']);quality='word'
        else:
            caps=item.get('captions',[])
            if clean(s['narration'])!=clean(''.join(c['text'] for c in caps)):raise ValueError('External captions do not match narration')
            caps=[{**c,'start':c['start']+.3,'end':c['end']+.3,'words':[]} for c in caps];quality='phrase'
    else:
        import edge_tts
        key=digest({'text':s['narration'],'voice':voice,'provider':'edge'})
        if not meta.exists() or read(meta).get('key')!=key or not wav.exists():
            mp3=target/'voice.mp3';boundary=target/'words.jsonl'
            for attempt in range(3):
                try:
                    c=edge_tts.Communicate(s['narration'],voice.get('name','zh-CN-YunxiNeural'),rate=voice.get('rate','-3%'),boundary='WordBoundary')
                    await asyncio.wait_for(c.save(str(mp3),str(boundary)),timeout=90);break
                except Exception:
                    if attempt==2:raise RuntimeError('Edge TTS unavailable after 3 attempts. Use external audio manifest; see references/AUDIO.md')
                    await asyncio.sleep(2)
            run(['-i',mp3,'-ar','48000','-ac','1',wav])
        events=[json.loads(l) for l in (target/'words.jsonl').read_text(encoding='utf-8').splitlines() if l.strip()]
        words=[{'text':e['text'],'start':e['offset']/1e7,'end':(e['offset']+e['duration'])/1e7} for e in events if e.get('type')=='WordBoundary']
        caps=align(s['narration'],words);quality='word'
    dur=duration(wav);prev=0
    for cap in caps:
        if cap['start']<prev-.02 or cap['end']<=cap['start'] or cap['end']>dur+.4:raise ValueError('Caption timing outside audio or overlaps')
        prev=cap['end']
    write(meta,{'key':key,'narration':s['narration'],'alignment':quality})
    return wav,dur,caps,quality
def audio(d,path,out,external):
    out.mkdir(parents=True,exist_ok=True);scenes=[];start=0;files=[]
    for i,s in enumerate(d['scenes']):
        wav,dur,caps,quality=asyncio.run(tts_scene(s,d,out,external))
        sec=max(6,math.ceil(dur+(.9 if i<len(d['scenes'])-1 else 2)))
        for j,c in enumerate(caps):c['until']=caps[j+1]['start'] if j+1<len(caps) else sec-.3
        timed=out/'audio'/s['id']/'timed.wav'
        run(['-i',wav,'-af',f'adelay=300:all=1,apad,atrim=end_sample={sec*48000},asetpts=N/SR/TB',timed])
        files.append(timed);scenes.append({**s,'start':start,'duration':sec,'captions':caps,'alignment':quality});start+=sec
        print(f'Audio {i+1}/{len(d["scenes"])} ready ({sec}s)',flush=True)
    # Concatenate PCM without shell quoting or ffmpeg concat path escaping.
    with wave.open(str(out/'raw-narration.wav'),'wb') as dst:
        dst.setnchannels(1);dst.setsampwidth(2);dst.setframerate(48000)
        for f in files:
            with wave.open(str(f)) as src:dst.writeframes(src.readframes(src.getnframes()))
    run(['-i',out/'raw-narration.wav','-af','loudnorm=I=-16:TP=-1.5:LRA=7','-ar','48000','-ac','1',out/'narration.wav'])
    music=d.get('music',{});mp=asset(music['path'],path) if music.get('path') else None
    if mp:
        if not mp.exists():raise ValueError('Music asset not found: '+str(mp))
        run(['-stream_loop','-1','-i',mp,'-t',start,'-af',f'highpass=f=75,lowpass=f=8500,equalizer=f=2400:t=o:w=1.3:g=-3,loudnorm=I=-27:TP=-5:LRA=7,afade=t=in:st=0:d=0.8,afade=t=out:st={start-3.2}:d=3.2','-ar','48000','-ac','2',out/'music-bed.wav'])
        run(['-i',out/'narration.wav','-i',out/'music-bed.wav','-filter_complex','[1:a][0:a]sidechaincompress=threshold=0.07:ratio=4:attack=15:release=650:makeup=1:knee=2.5:detection=rms[a]','-map','[a]','-ar','48000','-ac','2',out/'music-ducked.wav'])
        run(['-i',out/'narration.wav','-i',out/'music-ducked.wav','-filter_complex','[0:a]pan=stereo|c0=c0|c1=c0[v];[v][1:a]amix=inputs=2:duration=first:normalize=0,volume=-2.3dB,alimiter=limit=0.8414:attack=5:release=80:level=0:latency=1[a]','-map','[a]','-ar','48000',out/'mix.wav'])
    else:run(['-i',out/'narration.wav','-af','volume=-2.3dB','-ac','2','-ar','48000',out/'mix.wav'])
    write(out/'timeline.json',{'project_hash':data_hash(d),'total':start,'scenes':scenes})
    lines=[]
    def stamp(t):
        ms=round(t*1000);return f'{ms//3600000:02}:{ms//60000%60:02}:{ms//1000%60:02},{ms%1000:03}'
    for s in scenes:
        for c in s['captions']:lines.append(f'{len(lines)+1}\n{stamp(s["start"]+c["start"])} --> {stamp(s["start"]+c["until"])}\n{c["text"]}\n')
    (out/'captions.srt').write_text('\n'.join(lines),encoding='utf-8')
    (out/'narration.txt').write_text('\n\n'.join(s['narration'] for s in scenes),encoding='utf-8')
    (out/'publish-notes.txt').write_text(music.get('credit','No background music.')+'\n\nCover is attached metadata only; select cover.png manually if platform ignores it.\n',encoding='utf-8')
    print(f'Total: {start}s')
def prepare_page(d,path,out,tl):
    import mimetypes
    images={}
    for s in d['scenes']:
        if s['visual']['type']=='image':
            f=asset(s['visual']['path'],path)
            images[s['id']]='data:'+str(mimetypes.guess_type(f)[0] or 'image/png')+';base64,'+base64.b64encode(f.read_bytes()).decode()
    data={'project':d,'timeline':tl,'images':images}
    (out/'data.js').write_text('const DATA='+json.dumps(data,ensure_ascii=False)+';',encoding='utf-8')
    shutil.copy2(ROOT/'assets/renderer.html',out/'index.html')
def render(d,path,out,preview_only=False):
    from PIL import Image
    from playwright.sync_api import sync_playwright
    tl=checkpoint(d,out);prepare_page(d,path,out,tl)
    with sync_playwright() as p:
        b=launch(p);page=b.new_page(viewport={'width':1080,'height':1920});errors=[]
        page.on('pageerror',lambda e:errors.append(str(e)))
        page.goto((out/'index.html').as_uri());page.evaluate('ready()')
        layout=page.evaluate('audit()');write(out/'layout-check.json',layout)
        if layout or errors:raise ValueError('Layout/JS checks failed: '+str(layout or errors))
        times=[0]+[s['start']+s['duration']*.55 for s in tl['scenes']]+[tl['total']-1]
        cols=4;rows=math.ceil(len(times)/cols);sheet=Image.new('RGB',(cols*270,rows*480),'#050e14')
        for i,t in enumerate(times):
            raw=page.evaluate('(t)=>{draw(t);return c.toDataURL("image/png").split(",")[1]}',t)
            f=out/f'preview-{i:02}.png';f.write_bytes(base64.b64decode(raw))
            with Image.open(f) as im:sheet.paste(im.resize((270,480)),((i%cols)*270,(i//cols)*480))
        sheet.save(out/'storyboard.jpg',quality=95)
        if d['cover'].get('image'):
            source=asset(d['cover']['image'],path)
            run(['-i',source,'-vf','scale=1080:1920:force_original_aspect_ratio=decrease:flags=lanczos,pad=1080:1920:(ow-iw)/2:(oh-ih)/2:color=0x050e14','-frames:v','1',out/'cover.png'])
        else:
            raw=page.evaluate('()=>{drawCover();return c.toDataURL("image/png").split(",")[1]}')
            (out/'cover.png').write_bytes(base64.b64decode(raw))
        if preview_only:b.close();print('Preview ready:',out/'storyboard.jpg');return
        if not d['review']['facts_checked'] or not d['review']['visual_meaning_checked']:raise ValueError('Review source facts and visual direction, then set review flags. Preview remains available.')
        credit=d.get('music',{}).get('credit','');frames=round(tl['total']*24)
        log=(out/'encode.log').open('wb');temp=out/'video.partial.mp4'
        cmd=[ff(),'-hide_banner','-y','-f','image2pipe','-framerate','24','-vcodec','mjpeg','-i','pipe:0','-i',str(out/'mix.wav'),'-i',str(out/'cover.png'),'-map','0:v:0','-map','1:a:0','-map','2:v:0','-t',str(tl['total']),'-c:v:0','libx264','-preset:v:0','medium','-crf:v:0','18','-filter:v:0','scale=in_range=full:out_range=limited:out_color_matrix=bt709,format=yuv420p','-r:v:0','24','-color_range:v:0','tv','-colorspace:v:0','bt709','-c:a','aac','-b:a','192k','-c:v:1','png','-disposition:v:1','attached_pic','-metadata:s:v:1','title=Cover','-metadata','title='+d['title'],'-metadata','comment='+credit,'-movflags','+faststart',str(temp)]
        enc=subprocess.Popen(cmd,stdin=subprocess.PIPE,stdout=subprocess.DEVNULL,stderr=log);started=time.monotonic()
        try:
            for frame in range(frames):
                raw=page.evaluate('(t)=>{draw(t);return c.toDataURL("image/jpeg",.97).split(",")[1]}',frame/24)
                enc.stdin.write(base64.b64decode(raw))
                if frame%120==0:print(f'Render {frame}/{frames}, {time.monotonic()-started:.0f}s',flush=True)
            enc.stdin.close();code=enc.wait();log.close()
            if code or errors:raise RuntimeError(str(errors)+(out/'encode.log').read_text(errors='replace')[-2000:])
        except BaseException:
            enc.kill();log.close();raise
        b.close();temp.replace(out/'video.mp4')
    check(d,path,out)
def check(d,path,out):
    import numpy as np
    tl=checkpoint(d,out);video=out/'video.mp4'
    decoded=run(['-i',video,'-map','0:v:0','-map','0:a:0','-f','null','-']).stderr.decode(errors='replace')
    (out/'decode-check.txt').write_text(decoded,encoding='utf-8')
    measurements=run(['-i',video,'-map','0:a:0','-af','loudnorm=I=-16:TP=-1.5:LRA=7:print_format=json','-f','null','-']).stderr.decode(errors='replace')
    loud=json.loads(measurements[measurements.rfind('{'):measurements.rfind('}')+1])
    def pcm(name):
        with wave.open(str(out/name)) as w:return np.frombuffer(w.readframes(w.getnframes()),dtype=np.int16).astype(float).reshape(-1,w.getnchannels()).mean(axis=1)/32768
    gap=None
    if d.get('music',{}).get('path'):
        v=pcm('narration.wav');m=pcm('music-ducked.wav');n=min(len(v),len(m))//4800*4800
        vr=np.sqrt(np.mean(v[:n].reshape(-1,4800)**2,axis=1));mr=np.sqrt(np.mean(m[:n].reshape(-1,4800)**2,axis=1));a=vr>.04
        gap=round(float(np.median(20*np.log10((vr[a]+1e-9)/(mr[a]+1e-9)))),2)
    frame_counts=re.findall(r'frame=\s*(\d+)',decoded);actual=int(frame_counts[-1]) if frame_counts else None
    report={'project_hash':data_hash(d),'duration_seconds':tl['total'],'frame_count':actual,'expected_frames':tl['total']*24,'size':'1080x1920','attached_cover':'attached pic' in decoded,'integrated_lufs':float(loud['input_i']),'true_peak_dbfs':float(loud['input_tp']),'music_below_voice_median_db':gap,'caption_alignment':sorted(set(s['alignment'] for s in tl['scenes'])),'decode_passed':True,'manual_review':'Inspect storyboard/cover and listen to video; automatic checks do not certify technical facts or pronunciation.'}
    passed=actual==tl['total']*24 and report['attached_cover'] and -21<=report['integrated_lufs']<=-13 and report['true_peak_dbfs']<=-1 and (gap is None or gap>=14)
    report['passed']=passed;write(out/'validation.json',report)
    for name,t in [('first',0),('last',tl['total']-1)]:run(['-ss',t,'-i',video,'-map','0:v:0','-frames:v','1',out/f'final-{name}.png'])
    if not passed:raise RuntimeError('AV checks failed. See validation.json')
    print(json.dumps(report,ensure_ascii=False,indent=2))
def registry(path,patent,title,add=False):
    p=Path(path);r=read(p) if p.exists() else {'completed':[]}
    matches=[x for x in r['completed'] if clean(x.get('patent','')).lower()==clean(patent).lower() or (title and clean(x.get('title',''))==clean(title))]
    if matches:print(json.dumps({'already_completed':True,'matches':matches},ensure_ascii=False));return
    if add:r['completed'].append({'patent':patent,'title':title});write(p,r)
    print(json.dumps({'already_completed':False,'added':add}))
def main():
    ap=argparse.ArgumentParser(description=__doc__);sub=ap.add_subparsers(dest='cmd',required=True)
    sub.add_parser('doctor')
    ex=sub.add_parser('extract');ex.add_argument('pdf');ex.add_argument('--out',required=True);ex.add_argument('--pages',default='')
    init=sub.add_parser('init');init.add_argument('--out',required=True);init.add_argument('--example',choices=['oil','thermal','mesh'],default='mesh')
    for cmd in ['validate','audio','preview','render','check','build']:
        sp=sub.add_parser(cmd);sp.add_argument('project');sp.add_argument('--out',default='build');sp.add_argument('--external-audio')
    reg=sub.add_parser('registry');reg.add_argument('--file',required=True);reg.add_argument('--patent',required=True);reg.add_argument('--title',default='');reg.add_argument('--add',action='store_true')
    a=ap.parse_args()
    if a.cmd=='doctor':doctor();return
    if a.cmd=='extract':extract(a.pdf,Path(a.out).resolve(),a.pages);return
    if a.cmd=='registry':registry(a.file,a.patent,a.title,a.add);return
    if a.cmd=='init':
        dest=Path(a.out).resolve();dest.mkdir(parents=True,exist_ok=True)
        if (dest/'project.json').exists():raise ValueError('project.json already exists; use a new directory')
        d=read(ROOT/f'examples/{a.example}.json');d['review']={'facts_checked':False,'visual_meaning_checked':False};write(dest/'project.json',d)
        if not (dest/'completed-projects.json').exists():shutil.copy2(ROOT/'examples/completed-projects.json',dest/'completed-projects.json')
        print('Template copied. Replace facts/content/identity; do not only rename the title:',dest/'project.json');return
    path=Path(a.project).resolve();d=project(path);out=Path(a.out).resolve()
    # Never generate into the installed skill, or overwrite a different project's output.
    if out==ROOT or ROOT in out.parents:raise ValueError('Output must be outside installed skill folder')
    out.mkdir(parents=True,exist_ok=True);owner=out/'owner.json'
    if owner.exists() and read(owner).get('project')!=str(path):raise ValueError('Output belongs to another project; use a new --out directory')
    write(owner,{'project':str(path)})
    if a.cmd=='validate':print('Configuration and evidence references valid. Truth still requires source review.');return
    if a.cmd in {'audio','build'}:audio(d,path,out,a.external_audio)
    if a.cmd in {'preview','render','build'}:render(d,path,out,a.cmd=='preview')
    if a.cmd=='check':check(d,path,out)
if __name__=='__main__':
    try:main()
    except Exception as e:print(f'ERROR: {e}',file=sys.stderr);sys.exit(1)
