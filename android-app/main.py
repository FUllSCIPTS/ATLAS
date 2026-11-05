"""ATLAS Go entry point. Application code and screens are Python."""
import os
from kivy.config import Config
from kivy.utils import platform
# Configure the desktop surface before Window is imported to prevent clipping.
if platform != 'android':
    width, height = os.environ.get('ATLAS_PREVIEW_SIZE','440x940').split('x')
    Config.set('graphics', 'width', width)
    Config.set('graphics', 'height', height)
from atlas_go.app import AtlasGoApp
if __name__ == '__main__':
    AtlasGoApp().run()
