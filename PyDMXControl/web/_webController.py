"""
 *  PyDMXControl: A Python 3 module to control DMX via Python. Featuring fixture profiles and working with uDMX.
 *  <https://github.com/MattIPv4/PyDMXControl/>
 *  Copyright (C) 2018 Matt Cowley (MattIPv4) (me@mattcowley.co.uk)
"""

import builtins  # Builtins for Jinja context
import contextlib  # Silent flask
import io  # Silent flask
import logging  # Logging
from os import path  # OS Path
from threading import Thread  # Threading
from time import sleep  # Sleep
from typing import Dict, Callable  # Typing

from flask import Flask  # Flask

from ._routes import routes  # Web Routes
from ..utils.timing import DMXMINWAIT

# Set error only logging
log = logging.getLogger('werkzeug')
log.setLevel(logging.ERROR)


# WebController
class WebController:

    def __init__(self, controller: 'Controller', callbacks: Dict[str, Callable] = None, host: str = "0.0.0.0",
                 port: int = 8080):
        # Setup flask
        self.__thread = None
        self.__host = host
        self.__port = port
        self.__app = Flask("PyDMXControl Web Controller")
        self.__app.template_folder = path.dirname(__file__) + "/templates"
        self.__app.static_url_path = "/static"
        self.__app.static_folder = path.dirname(__file__) + "/static"
        self.__app.register_blueprint(routes)
        self.__app.parent = self

        # Setup controller
        self.controller = controller

        # Setup callbacks
        self.callbacks = {} if callbacks is None else callbacks
        self.__default_callbacks()
        self.__check_callbacks()

        # Setup template context
        @self.__app.context_processor
        def variables() -> dict:
            brand = "<span class='brand'><span>P</span><span>y</span><span>DMX</span><span>Control</span></span>"
            return dict({"controller": self.controller, "callbacks": self.callbacks, "brand": brand},
                        **dict(globals(), **builtins.__dict__))  # Dictionary stacking to concat

        # Setup thread
        self.__running = False
        self.run()

    def __default_callbacks(self):
        # Some default callbacks
        if 'all_on' not in self.callbacks:
            self.callbacks['all_on'] = self.controller.all_on
        if 'all_off' not in self.callbacks:
            self.callbacks['all_off'] = self.controller.all_off
        if 'all_locate' not in self.callbacks:
            self.callbacks['all_locate'] = self.controller.all_locate

    def __check_callbacks(self):
        for key in self.callbacks.keys():
            if not self.callbacks[key] or not callable(self.callbacks[key]):
                del self.callbacks[key]

    def __run(self):
        has_run = False
        self.__running = True
        while self.__running:
            # Run flask if not yet launched
            if not has_run:
                self.__app.run(host=self.__host, port=self.__port)
                has_run = True
            # Sleep DMX delay time
            sleep(DMXMINWAIT)

        return

    def run(self):
        if not self.__running:
            with contextlib.redirect_stdout(io.StringIO()):
                self.__thread = Thread(target=self.__run)
                self.__thread.daemon = True
                self.__thread.start()
            print("Started web controller: http://{}:{}".format(self.__host, self.__port))

    def stop(self):
        self.__running = False
