from flask import jsonify, Blueprint
from proxy_pool import ProxyPool

proxy = Blueprint('proxy', 'web')

@proxy.route('/')
def index():
    api_list = {
        'get': 'get an usable proxy',
        'get_all': 'get all proxy from proxy pool',
    }
    return jsonify(api_list)


@proxy.route('/get/')
def get():
    return ProxyPool().get_fast_proxy()


@proxy.route('/get_all/')
def getAll():
    proxies = ProxyPool().get_all()
    return jsonify([len(proxies)] + [each.addr for each in proxies])
