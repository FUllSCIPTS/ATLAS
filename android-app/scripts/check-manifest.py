"""Check the release metadata and that demo-only data claims match permissions."""
import sys
from xml.etree import ElementTree as ET
root=ET.parse(sys.argv[1]).getroot()
android='{http://schemas.android.com/apk/res/android}'
assert root.get('package')=='org.atlas.mobility'
assert int(root.find('uses-sdk').get(android+'targetSdkVersion'))>=36
app=root.find('application')
assert app.get(android+'debuggable','false')=='false'
assert app.get(android+'allowBackup','true')=='false'
permissions={p.get(android+'name') for p in root.findall('uses-permission')}
forbidden={'android.permission.INTERNET','android.permission.ACCESS_FINE_LOCATION','android.permission.ACCESS_COARSE_LOCATION','com.android.vending.BILLING'}
assert not permissions & forbidden,permissions
print('PASS: target API, release flags, backups and offline permission declarations')
