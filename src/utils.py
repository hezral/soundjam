# SPDX-License-Identifier: GPL-3.0-or-later
# SPDX-FileCopyrightText: 2021 Adi Hezral <hezral@gmail.com>

from datetime import datetime

class HelperUtils:
    @staticmethod
    def run_async(func):
        '''
        https://github.com/learningequality/ka-lite-gtk/blob/341813092ec7a6665cfbfb890aa293602fb0e92f/kalite_gtk/mainwindow.py
        http://code.activestate.com/recipes/576683-simple-threading-decorator/
        run_async(func): 
        function decorator, intended to make "func" run in a separate thread (asynchronously).
        Returns the created Thread object
        Example:
            @run_async
            def task1():
                do_something
            @run_async
            def task2():
                do_something_too
        '''
        from threading import Thread
        from functools import wraps

        @wraps(func)
        def async_func(*args, **kwargs):
            func_hl = Thread(target=func, args=args, kwargs=kwargs)
            func_hl.start()
            # Never return anything, idle_add will think it should re-run the
            # function because it's a non-False value.
            return None

        return async_func
