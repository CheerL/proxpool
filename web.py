import os
import sys
import time
from flask import Flask, Blueprint, send_file
from proxy_pool_api import proxy
from proxy_pool import ProxyPool
from utils import parallel as pl

app = Flask('web')
app.register_blueprint(proxy, url_prefix='/proxy')

host = '0.0.0.0'
port = '80'

def run_web():
    ProxyPool().daemon(False)
    app.run(host=host, port=port)

if __name__ == '__main__':
    run_web()
