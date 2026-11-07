"""Device location for the live map. Android: LocationManager through pyjnius, after the user
grants the runtime permission. Desktop: optional ATLAS_FAKE_GPS="lat,lon" for previews and tests.

The position is used on this device only (blue dot, nearest pickup point, a driver's position
for dispatch). It is never written anywhere except a signed-in driver's local profile.
"""
import os
from kivy.clock import Clock
from kivy.logger import Logger
from kivy.utils import platform


class DeviceLocation:
    def __init__(self, on_fix, on_status=None):
        self.on_fix = on_fix
        self.on_status = on_status or (lambda text: None)
        self.point = None
        self.accuracy = None
        self.running = False
        self._manager = None
        self._listener = None

    @property
    def available(self) -> bool:
        return platform == 'android' or bool(os.environ.get('ATLAS_FAKE_GPS'))

    def start(self):
        if self.running:
            return
        if platform == 'android':
            self._android_start()
        elif os.environ.get('ATLAS_FAKE_GPS'):
            lat, lon = (float(v) for v in os.environ['ATLAS_FAKE_GPS'].split(','))
            self.running = True
            Clock.schedule_once(lambda _dt: self._fix(lat, lon, 12.0), 0)
        else:
            self.on_status('Location is available in the Android app.')

    def stop(self):
        if platform == 'android' and self._manager is not None and self._listener is not None:
            try:
                self._manager.removeUpdates(self._listener)
            except Exception:
                Logger.exception('ATLAS: could not stop location updates')
        self.running = False

    def _fix(self, lat, lon, accuracy):
        self.point, self.accuracy = (float(lat), float(lon)), float(accuracy)
        self.on_fix(self.point, self.accuracy)

    # ------------------------------------------------------------------ Android
    def _android_start(self):
        try:
            from android.permissions import Permission, check_permission, request_permissions
        except ImportError:
            self.on_status('Location permission API is unavailable.')
            return
        wanted = [Permission.ACCESS_FINE_LOCATION, Permission.ACCESS_COARSE_LOCATION]
        if any(check_permission(p) for p in wanted):
            self._android_listen()
            return
        self.on_status('Waiting for location permission…')

        def answered(_permissions, grants):
            if any(grants):
                Clock.schedule_once(lambda _dt: self._android_listen(), 0)
            else:
                Clock.schedule_once(lambda _dt: self.on_status('Location permission was not granted. '
                                                               'The map still works without it.'), 0)
        request_permissions(wanted, answered)

    def _android_listen(self):
        try:
            from jnius import PythonJavaClass, autoclass, java_method
            outer = self

            class Listener(PythonJavaClass):
                __javainterfaces__ = ['android/location/LocationListener']
                __javacontext__ = 'app'

                @java_method('(Landroid/location/Location;)V')
                def onLocationChanged(self, location):
                    lat, lon, accuracy = location.getLatitude(), location.getLongitude(), location.getAccuracy()
                    Clock.schedule_once(lambda _dt: outer._fix(lat, lon, accuracy), 0)

                @java_method('(Ljava/lang/String;)V')
                def onProviderEnabled(self, provider):
                    pass

                @java_method('(Ljava/lang/String;)V')
                def onProviderDisabled(self, provider):
                    Clock.schedule_once(lambda _dt: outer.on_status('Turn on location in Android settings.'), 0)

                @java_method('(Ljava/lang/String;ILandroid/os/Bundle;)V')
                def onStatusChanged(self, provider, status, extras):
                    pass

            context = autoclass('org.kivy.android.PythonActivity').mActivity
            Context = autoclass('android.content.Context')
            Looper = autoclass('android.os.Looper')
            manager = context.getSystemService(Context.LOCATION_SERVICE)
            listener = Listener()
            providers = [p for p in ('gps', 'network') if manager.isProviderEnabled(p)]
            if not providers:
                self.on_status('Turn on location in Android settings.')
                return
            for provider in providers:
                manager.requestLocationUpdates(provider, 3000, 5.0, listener, Looper.getMainLooper())
                last = manager.getLastKnownLocation(provider)
                if last is not None and self.point is None:
                    self._fix(last.getLatitude(), last.getLongitude(), last.getAccuracy())
            self._manager, self._listener, self.running = manager, listener, True
            self.on_status('Finding your location…' if self.point is None else '')
        except Exception:
            Logger.exception('ATLAS: location updates could not start')
            self.on_status('Location could not start on this device.')
