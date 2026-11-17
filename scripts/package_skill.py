#!/usr/bin/env python3
"""Build a portable Skill ZIP using an explicit file allowlist."""
from pathlib import Path
import argparse, hashlib, json, zipfile

ROOT=Path(__file__).resolve().parents[1]
FILES=['SKILL.md','README.md','THIRD_PARTY_NOTICES.md','requirements.txt','requirements-tested.txt']
DIRECTORIES=['assets','examples','references','scripts','tests']

def build(out):
    out=Path(out).resolve();out.mkdir(parents=True,exist_ok=True)
    files=[ROOT/n for n in FILES]
    for directory in DIRECTORIES:
        files.extend(f for f in (ROOT/directory).rglob('*') if f.is_file() and '__pycache__' not in f.parts and f.suffix!='.pyc')
    for f in files:
        if f.is_symlink() or not f.resolve().is_relative_to(ROOT):raise ValueError('Refusing external/symlink asset: '+str(f))
        if f.name.startswith('.env') or f.suffix.lower() in {'.key','.pem'}:raise ValueError('Refusing credential-like file: '+str(f))
    archive=out/'patent-video-studio.zip'
    with zipfile.ZipFile(archive,'w',zipfile.ZIP_DEFLATED,compresslevel=6) as z:
        for f in sorted(set(files)):z.write(f,f.relative_to(ROOT).as_posix())
    with zipfile.ZipFile(archive) as z:
        assert 'SKILL.md' in z.namelist() and z.testzip() is None
    checksum=hashlib.sha256(archive.read_bytes()).hexdigest()
    (out/'SHA256SUMS.txt').write_text(checksum+'  '+archive.name+'\n',encoding='ascii')
    return {'archive':str(archive),'bytes':archive.stat().st_size,'sha256':checksum,'files':len(set(files))}

if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--out',default='dist')
    print(json.dumps(build(parser.parse_args().out),ensure_ascii=True,indent=2))
