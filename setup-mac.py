import os
import subprocess
import sys

from setuptools import setup

# Add src directory to Python path so py2app can find whacked4 module
sys.path.insert(0, 'src')

APP = ['src/main.py']
DATA_FILES = [
    'res',
    'cfg',
    'docs',
    'LICENSE',
    'README.md'
]

OPTIONS = {
    'argv_emulation': False,
    'iconfile': 'res/icon-hatchet.icns',
    'plist': {
        'CFBundleName': os.environ.get('app_title', 'WhackEd4'),
        'CFBundleDisplayName': os.environ.get('app_title', 'WhackEd4'),
        'CFBundleIdentifier': f'com.teamhellspawn.{os.environ.get("app_name_lower", "whacked4")}',
        'CFBundleVersion': os.environ.get('app_version_value', '1.3.3'),
        'CFBundleShortVersionString': os.environ.get('app_version_value', '1.3.3'),
        'CFBundleInfoDictionaryVersion': '6.0',
        'CFBundlePackageType': 'APPL',
        'NSHighResolutionCapable': True,
        'LSMinimumSystemVersion': '10.12',
        'NSHumanReadableCopyright': '© 2025 Dennis Meuwissen',
        'CFBundleDocumentTypes': [
            {
                'CFBundleTypeName': 'DeHackEd Patch',
                'CFBundleTypeExtensions': ['deh', 'bex'],
                'CFBundleTypeRole': 'Editor',
                'CFBundleTypeIconFile': 'icon-hatchet.icns',
                'LSHandlerRank': 'Owner'
            }
        ],
    },
    'packages': ['wx', 'pyaudio', 'platformdirs'],
    'includes': [],
    'excludes': [
        'wx.tools', 'wx.py', 'wx.lib.agw', 'wx.lib.plot', 'wx.lib.floatcanvas',
        'wx.lib.ogl', 'wx.lib.editor', 'wx.lib.mixins', 'wx.demo',
        'wx.tools.Editra', 'wx.tools.XRCed', 'wx.lib.inspection',
        'tkinter', 'turtle', 'test', 'unittest', 'doctest',
        'pydoc', 'xml.etree', 'xml.sax', 'xml.dom'
    ],
    'site_packages': True,
    'strip': True,
    'optimize': 2,
}

setup(
    app=APP,
    name=os.environ.get('app_title', 'WhackEd4'),
    version=os.environ.get('app_version_value', '1.3.3'),
    description=os.environ.get('app_description', 'A DeHackEd editor for macOS'),
    data_files=DATA_FILES,
    options={'py2app': OPTIONS},
    setup_requires=['py2app'],
    install_requires=['pyaudio', 'wxPython', 'platformdirs']
)

# Clean up broken symbolic links after build

if 'py2app' in sys.argv:
    print("Cleaning up broken symbolic links...")
    # Find and remove broken symlinks in the app bundle
    try:
        result = subprocess.run([
            'find', 'dist/', '-type', 'l', '-exec', 'test', '!', '-e', '{}', ';',
            '-print0'
        ], capture_output=True, text=True)

        if result.stdout:
            broken_links = result.stdout.strip('\0').split('\0')
            for link in broken_links:
                if link and link.endswith('.pyo'):
                    print(f"Removing broken symlink: {link}")
                    os.unlink(link)
    except Exception as e:
        print(f"Warning: Could not clean up symlinks: {e}")
    print("Cleanup complete.")
