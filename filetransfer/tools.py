import time

from threading import Timer

get_milliseconds = lambda: int(round(time.time() * 1000))
def create_interval(func, time):
    def wrapper():
        func()
        create_interval(func, time)
    return Timer(time, wrapper).start()