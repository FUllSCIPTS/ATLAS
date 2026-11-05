"""Sign an Android App Bundle with the owner's private upload key."""
import argparse
import os
from pathlib import Path
import shutil
import subprocess

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('input',type=Path,help='Unsigned AAB')
    parser.add_argument('output',type=Path,help='Signed output AAB')
    args=parser.parse_args()
    required=('ATLAS_UPLOAD_KEYSTORE','ATLAS_UPLOAD_ALIAS','ATLAS_UPLOAD_PASSWORD')
    missing=[name for name in required if not os.environ.get(name)]
    if missing:parser.error('Set private environment values: '+', '.join(missing))
    if not args.input.is_file():parser.error('Input AAB does not exist')
    if args.input.resolve()==args.output.resolve():parser.error('Choose a separate signed output path')
    if not Path(os.environ['ATLAS_UPLOAD_KEYSTORE']).is_file():parser.error('Private keystore does not exist')
    args.output.parent.mkdir(parents=True,exist_ok=True)
    shutil.copy2(args.input,args.output)
    tool=[shutil.which('jarsigner')] if shutil.which('jarsigner') else ['java','-m','jdk.jartool/sun.security.tools.jarsigner.Main']
    subprocess.run(tool+['-keystore',os.environ['ATLAS_UPLOAD_KEYSTORE'],'-storetype','PKCS12',
                        '-storepass:env','ATLAS_UPLOAD_PASSWORD','-keypass:env','ATLAS_UPLOAD_PASSWORD',
                        '-sigalg','SHA256withRSA','-digestalg','SHA-256',str(args.output),os.environ['ATLAS_UPLOAD_ALIAS']],check=True)
    subprocess.run(tool+['-verify',str(args.output)],check=True)
    print('Signed and verified: '+str(args.output))

if __name__=='__main__':
    main()
