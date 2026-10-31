import argparse
import hashlib
import json
from pathlib import Path
import sys
import zipfile

sys.dont_write_bytecode = True
sys.stdout.reconfigure(encoding='utf-8')
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from smart_image import __version__
from check_release_privacy import audit


def build(output_dir):
    out = Path(output_dir).resolve()
    out.mkdir(parents=True,exist_ok=True)
    target = out/('codex-smart-image-'+__version__+'.zip')
    files = [ROOT/'.mcp.json',ROOT/'README.md',ROOT/'.gitignore']
    allowed={'.py','.ps1','.md','.json','.yaml','.yml'}
    for root in ['smart_image','skills','scripts','tests','docs','.codex-plugin','installer-skill','development-skill']:
        files.extend(p for p in (ROOT/root).rglob('*') if p.is_file() and '__pycache__' not in p.parts and p.suffix in allowed)
    report=audit(files)
    if not report['passed']:
        raise RuntimeError('Release privacy scan failed: '+json.dumps(report['issues'],ensure_ascii=False))
    with zipfile.ZipFile(target,'w',zipfile.ZIP_DEFLATED) as z:
        for path in sorted(files):
            z.write(path,'codex-smart-image-'+__version__+'/'+path.relative_to(ROOT).as_posix())
    digest = hashlib.sha256(target.read_bytes()).hexdigest()
    target.with_suffix('.zip.sha256').write_text(digest+'  '+target.name+'\n',encoding='ascii')
    skill_target=out/('codex-smart-image-install-'+__version__+'-skill.zip')
    with zipfile.ZipFile(skill_target,'w',zipfile.ZIP_DEFLATED) as z:
        for path in sorted((ROOT/'installer-skill/codex-smart-image-install').rglob('*')):
            if path.is_file() and path.suffix in allowed:
                z.write(path,'codex-smart-image-install/'+path.relative_to(ROOT/'installer-skill/codex-smart-image-install').as_posix())
    skill_digest=hashlib.sha256(skill_target.read_bytes()).hexdigest()
    skill_target.with_suffix('.zip.sha256').write_text(skill_digest+'  '+skill_target.name+'\n',encoding='ascii')
    final=audit([target,skill_target])
    if not final['passed']:
        target.unlink(missing_ok=True)
        skill_target.unlink(missing_ok=True)
        raise RuntimeError('Archive privacy scan failed')
    return {'path':str(target),'sha256':digest,'size':target.stat().st_size,'file_count':len(files),
            'skill_path':str(skill_target),'skill_sha256':skill_digest}


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--output-dir',default=str(ROOT/'release'))
    print(json.dumps(build(parser.parse_args().output_dir),ensure_ascii=False))
