import sys
import os
from functools import wraps

if getattr(sys, 'frozen', False):
    ROOT_PATH = os.path.dirname(os.path.dirname(sys.executable))
else:
    ROOT_PATH = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

SRC_PATH = os.path.join(ROOT_PATH, 'src')
LOG_PATH = os.path.join(ROOT_PATH, 'log')

for path in [SRC_PATH, LOG_PATH]:
    if not os.path.exists(path):
        os.mkdir(path)

def Singleton(cls):
    instances = {}
    @wraps(cls)
    def _singleton(*args, **kw):
        if cls not in instances:
            instances[cls] = cls(*args, **kw)
        return instances[cls]

    return _singleton
