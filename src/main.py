import logging

import initialization  # noqa: F401 keep this first, to ensure we're set up for other imports
from android_utils import share_by_intent
from android_utils import start_service
from jnius import autoclass
from kolibri.main import enable_plugin
from kolibri.plugins.app.utils import interface
from kolibri.utils.cli import initialize
from kolibri.utils.server import BaseKolibriProcessBus
from kolibri.utils.server import KolibriServerPlugin
from kolibri.utils.server import ZeroConfPlugin
from kolibri.utils.server import ZipContentServerPlugin
from lifecycle import register_activity_lifecycle_callbacks
from magicbus.plugins import SimplePlugin
from runnable import Runnable


def on_activity_started(activity):
    logging.info("onActivityStarted")


def on_activity_paused(activity):
    logging.info("onActivityPaused")


def on_activity_resumed(activity):
    logging.info("onActivityResumed")


def on_activity_stopped(activity):
    logging.info("onActivityStopped")


def on_activity_destroyed(activity):
    logging.info("onActivityDestroyed")


register_activity_lifecycle_callbacks(
    onActivityStarted=on_activity_started,
    onActivityPaused=on_activity_paused,
    onActivityResumed=on_activity_resumed,
    onActivityStopped=on_activity_stopped,
    onActivityDestroyed=on_activity_destroyed,
)

PythonActivity = autoclass("org.kivy.android.PythonActivity")

FullScreen = autoclass("org.learningequality.FullScreen")
configureWebview = Runnable(FullScreen.configureWebview)
configureWebview(PythonActivity.mActivity)

loadUrl = Runnable(PythonActivity.mWebView.loadUrl)


class AppPlugin(SimplePlugin):
    def __init__(self, bus):
        self.bus = bus
        self.bus.subscribe("SERVING", self.SERVING)

    def SERVING(self, port):
        start_url = (
            "http://127.0.0.1:{port}".format(port=port) + interface.get_initialize_url()
        )
        loadUrl(start_url)
        start_service("workers")


logging.info("Initializing Kolibri and running any upgrade routines")

# activate app mode
enable_plugin("kolibri.plugins.app")

# we need to initialize Kolibri to allow us to access the app key
initialize()

interface.register(share_file=share_by_intent)

# start kolibri server
logging.info("Starting kolibri server.")

kolibri_bus = BaseKolibriProcessBus()
# Setup zeroconf plugin
zeroconf_plugin = ZeroConfPlugin(kolibri_bus, kolibri_bus.port)
zeroconf_plugin.subscribe()
kolibri_server = KolibriServerPlugin(
    kolibri_bus,
    kolibri_bus.port,
)

alt_port_server = ZipContentServerPlugin(
    kolibri_bus,
    kolibri_bus.zip_port,
)
# Subscribe these servers
kolibri_server.subscribe()
alt_port_server.subscribe()
app_plugin = AppPlugin(kolibri_bus)
app_plugin.subscribe()
kolibri_bus.run()
