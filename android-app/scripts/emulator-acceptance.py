"""Install and test Python Android builds; capture real OS screenshots with ADB."""
import json
import re
import subprocess
import sys
import time
from pathlib import Path

PACKAGE='org.atlas.mobility'
ACTIVITY=PACKAGE+'/org.kivy.android.PythonActivity'
output=Path('test-output/android')
output.mkdir(parents=True,exist_ok=True)

def adb(*args,check=True):
    return subprocess.run(['adb',*args],check=check,stdout=subprocess.PIPE,stderr=subprocess.PIPE)

def private_text(name):
    result=adb('shell','run-as',PACKAGE,'cat','files/test-output/'+name,check=False)
    return result.stdout.decode(errors='replace').strip() if result.returncode==0 else ''

def save_log(name,buffer='crash'):
    (Path('test-output')/name).write_bytes(adb('logcat','-d','-b',buffer,check=False).stdout)

try:
    print(adb('install','-r','release/atlas-go-demo.apk').stdout.decode(),flush=True)
    adb('shell','pm','clear',PACKAGE)
    adb('logcat','-c')
    adb('shell','am','start','-n',ACTIVITY,'--ez','atlas_acceptance','true')
    captured=set()
    deadline=time.monotonic()+300
    result=None
    while time.monotonic()<deadline:
        request=private_text('capture-request.txt')
        if request and request not in captured:
            assert re.fullmatch(r'\d\d-[a-z-]+',request),request
            image=adb('exec-out','screencap','-p').stdout
            assert image.startswith(b'\x89PNG\r\n\x1a\n'),'System screenshot was not a PNG'
            (output/(request+'.png')).write_bytes(image)
            captured.add(request)
            adb('shell','run-as',PACKAGE,'cp','files/test-output/capture-request.txt','files/test-output/capture-ack.txt')
            print('Captured Android screenshot: '+request,flush=True)
        text=private_text('result.json')
        if text:
            try:result=json.loads(text)
            except json.JSONDecodeError:result=None
            if result is not None:break
        time.sleep(.25)
    assert result is not None,'Android acceptance timed out'
    (output/'result.json').write_text(json.dumps(result,indent=2))
    assert result['success'],result
    subprocess.run([sys.executable,'scripts/verify-acceptance.py',str(output)],check=True)
    save_log('crash-log.txt')
    assert 'FATAL EXCEPTION' not in Path('test-output/crash-log.txt').read_text()
    adb('shell','am','force-stop',PACKAGE)
    print(adb('install','-r','release/atlas-go-release-smoke.apk').stdout.decode(),flush=True)
    adb('logcat','-c')
    adb('shell','am','start','-n',ACTIVITY)
    time.sleep(10)
    assert adb('shell','pidof',PACKAGE,check=False).stdout.strip(),'Release process did not survive startup'
    assert adb('shell','run-as',PACKAGE,'pwd',check=False).returncode!=0,'Release must not be debuggable'
    Path('test-output/release-launch.png').write_bytes(adb('exec-out','screencap','-p').stdout)
    save_log('release-crash-log.txt')
    assert 'FATAL EXCEPTION' not in Path('test-output/release-crash-log.txt').read_text()
    print('PASS: Android UI, OS screenshots and non-debuggable release launch',flush=True)
except Exception:
    save_log('android-full-log.txt','main')
    save_log('crash-log.txt')
    raise
