"""Check the release metadata and that permissions match the privacy notice (1.6.0)."""
import sys
from xml.etree import ElementTree as ET
root=ET.parse(sys.argv[1]).getroot()
android='{http://schemas.android.com/apk/res/android}'
assert root.get('package')=='org.atlas.mobility'
assert int(root.find('uses-sdk').get(android+'targetSdkVersion'))>=36
assert int(root.get(android+'versionCode'))>=7, root.get(android+'versionCode')
app=root.find('application')
assert app.get(android+'debuggable','false')=='false'
assert app.get(android+'allowBackup','true')=='false'
permissions={p.get(android+'name') for p in root.findall('uses-permission')}
expected={'android.permission.INTERNET','android.permission.ACCESS_NETWORK_STATE',
          'android.permission.ACCESS_FINE_LOCATION','android.permission.ACCESS_COARSE_LOCATION'}
# Map tiles and the optional ATLAS server need the network; location is foreground-only and requested at run time.
# Bank payments use the app's own sandbox, not Google Play billing, and add no permission.
# SOS (1.6.0) opens the dialler and the messaging app with ACTION_DIAL / ACTION_SENDTO: the user places the call or
# sends the text there, so CALL_PHONE and SEND_SMS must never be declared.
assert permissions==expected,permissions
forbidden={'android.permission.ACCESS_BACKGROUND_LOCATION','com.android.vending.BILLING','android.permission.READ_CONTACTS',
           'android.permission.CALL_PHONE','android.permission.SEND_SMS'}
assert not permissions & forbidden,permissions
print('PASS: target API, release flags, backups and declared foreground-only permissions')
