import sys
import os

if getattr(sys, 'frozen', False):
    ROOT_PATH = os.path.dirname(os.path.dirname(sys.executable))
else:
    ROOT_PATH = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

SRC_PATH = os.path.join(ROOT_PATH, 'src')
LOG_PATH = os.path.join(ROOT_PATH, 'log')

for path in [SRC_PATH, LOG_PATH]:
    if not os.path.exists(path):
        os.mkdir(path)

def Singleton(cls, *args, **kw):
    instances = {}

    def _singleton():
        if cls not in instances:
            instances[cls] = cls(*args, **kw)
        return instances[cls]

    return _singleton
