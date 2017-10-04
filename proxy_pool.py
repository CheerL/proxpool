import os
import time
import random
import requests

import aiohttp
import asyncio
import async_timeout

from itertools import cycle
from lxml import etree
from util import Singleton, SRC_PATH
from util import parallel as pl
from util.logger import LogHandler
from util.async_run import async_run

from sqlalchemy import Column, String, Integer, Boolean, create_engine, and_, or_
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base

MAX_DELAY = 15
MAX_UPDATE_LENGTH = 60 * 30
MIN_PROXY_NUM = 100
DB_PATH = os.path.join(SRC_PATH, 'proxy.db')
HEADER = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 '
                  + '(KHTML, like Gecko) Chrome/55.0.2883.75 Safari/537.36',
    'X-Requested-With': 'XMLHttpRequest',
    'Accept': '*/*',
    'Connection': 'keep-alive',
    'Accept-Language': 'zh-CN,zh;q=0.8'
}

BASE = declarative_base()
ENGINE = create_engine('sqlite:///{}'.format(DB_PATH))
SESSION = sessionmaker(bind=ENGINE)()

async def fetch(url, proxy=None):
    async with aiohttp.ClientSession() as session:
        with async_timeout.timeout(MAX_DELAY):
            now = time.time()
            async with session.get(url, proxy=proxy) as response:
                assert response.status == 200
                return time.time() - now

class Proxy(BASE):
    __tablename__ = 'proxy'
    id = Column(Integer, primary_key=True)
    ip = Column(String(20))
    port = Column(String(20))
    addr = Column(String(20))
    delay = Column(Integer)
    verify = Column(Boolean)
    used = Column(Boolean)
    ver_last = Column(Integer)
    use_last = Column(Integer)
    fail_count = Column(Integer)
    wait_delete = Column(Boolean)

    def __init__(self, ip, port):
        self.ip = str(ip)
        self.port = str(port)
        self.addr = '{}:{}'.format(ip, port)
        self.delay = MAX_DELAY
        self.verify = False
        self.used = False
        self.ver_last = 0
        self.use_last = 0
        self.fail_count = 0
        self.wait_delete = False
    
    def __repr__(self):
        return '<Proxy (ip={}, port={}, delay={}, verify={}, used={}, fail_count={})>'.format(
            self.ip, self.port, self.delay, self.verify, self.used, self.fail_count
        )

    def __eq__(self, other):
        if isinstance(other, Proxy):
            return self.ip == other.ip and self.port == other.port
        else:
            return False

    def __ne__(self, other):
        return not self.__eq__(other)

    def __hash__(self):
        return hash(self.ip) + hash(self.port)

    def __lt__(self, other):
        return self.delay < other.delay

    def __le__(self, other):
        return self.delay <= other.delay

    def __str__(self):
        return self.addr

    async def test_delay(self):
        urls = ['http://www.baidu.com', 'http://music.163.com', 'http://www.runoob.com']
        proxy = 'http://{}'.format(self.addr)
        self.verify = True
        try:
            all_delay = 0
            for url in urls:
                all_delay += await fetch(url, proxy)
            self.delay = all_delay / len(urls)
            self.ver_last = time.time()
            self.used = False
            self.fail_count = 0
            self.wait_delete = False
        except:
            if self.fail_count >= 5:
                self.wait_delete = True
            else:
                self.fail_count += 1
        finally:
            SESSION.commit()

    def use(self):
        self.used = True
        self.use_last = time.time()
        SESSION.commit()

class ProxyGetter(object):
    def __init__(self):
        self.getter = ['getter_{}'.format(i) for i in range(4)]
        self.getter_0_url = cycle([
            'http://www.data5u.com/',
            'http://www.data5u.com/free/',
            'http://www.data5u.com/free/gngn/index.shtml',
            'http://www.data5u.com/free/gnpt/index.shtml'
        ])
        self.getter_2_url = cycle(((
            'http://www.xicidaili.com/nn/{}'.format(i),
            'http://www.xicidaili.com/nt/{}'.format(i)
        ) for i in range(1, 100)))
        self.getter_3_url = cycle((
            "http://www.goubanjia.com/free/gngn/index{}.shtml".format(i)
            for i in range(1, 20)
        ))
        self.proxy = None
        self.cold_time = {
            'getter_0': 0,
            'getter_1': 0,
            'getter_2': 0,
            'getter_3': 0
        }
        self.cold_limit = 60 * 20

    def get_getter(self):
        getters = list(filter(lambda x: time.time() - self.cold_time[x] > self.cold_limit, self.getter))
        return getattr(self, random.choice(getters))


    def getter_0(self):
        """
        抓取无忧代理 http://www.data5u.com/
        """
        url = next(self.getter_0_url)
        if url == 'http://www.data5u.com/free/gnpt/index.shtml':
            self.cold_time['getter_0'] = time.time()
        response = requests.get(url, headers=HEADER, proxies=self.proxy)
        html = etree.HTML(response.text)
        ul_list = html.xpath('//ul[@class="l2"]')
        for ul in ul_list:
            proxy = ul.xpath('.//li/text()')[0:2]
            yield Proxy(proxy[0], proxy[1])
        

    def getter_1(self):
        """
        抓取ip181 http://www.ip181.com/
        :param days:
        :return:
        """
        url = 'http://www.ip181.com/'
        self.cold_time['getter_1'] = time.time()
        response = requests.get(url, headers=HEADER, proxies=self.proxy)
        html = etree.HTML(response.text)
        tr_list = html.xpath('//tr')[1:]
        for tr in tr_list:
            proxy = tr.xpath('./td/text()')[0:2]
            yield Proxy(proxy[0], proxy[1])

    def getter_2(self):
        urls = next(self.getter_2_url)
        tr_list = []
        for url in urls:
            try:
                response = requests.get(url, headers=HEADER,proxies=self.proxy)
                html = etree.HTML(response.text)
                tr_list += html.xpath('//tr')[1:]
            except Exception as e:
                print(e)

        for tr in tr_list:
            proxy = tr.xpath('./td/text()')[0:2]
            yield Proxy(proxy[0], proxy[1])

    def getter_3(self):
        """
        抓取guobanjia http://www.goubanjia.com/free/gngn/index.shtml
        :return:
        """
        url = next(self.getter_3_url)
        response = requests.get(url,headers=HEADER,proxies=self.proxy)
        html = etree.HTML(response.text)
        proxy_list = html.xpath('//td[@class="ip"]')
        # 此网站有隐藏的数字干扰，或抓取到多余的数字或.符号
        # 需要过滤掉<p style="display:none;">的内容
        xpath_str = """.//*[not(contains(@style, 'display: none'))
                            and not(contains(@style, 'display:none'))
                            and not(contains(@class, 'port'))
                            ]/text()
                    """
        for each_proxy in proxy_list:
            # :符号裸放在td下，其他放在div span p中，先分割找出ip，再找port
            ip_addr = ''.join(each_proxy.xpath(xpath_str))
            port = each_proxy.xpath(".//span[contains(@class, 'port')]/text()")[0]
            yield Proxy(ip_addr, port)

@Singleton
class ProxyPool(object):
    def __init__(self):
        self.getter = ProxyGetter()
        self.logger = LogHandler('proxy_pool')
        self.keep_check = False
        self.pool = SESSION.query(Proxy)

    def daemon(self, block=False):
        def _daemon():
            try:
                self.logger.info('打开守护进程')
                while True:
                    try:
                        if not pl.search_thread(name='keep_cheek'):
                            self.time_out_update_swich()
                        time.sleep(30)
                    except Exception as e:
                        self.logger.error(e)
            except Exception as e:
                self.logger.error(e)
            finally:
                self.logger.info('结束守护进程')
                SESSION.commit()
                SESSION.close()

        BASE.metadata.create_all(ENGINE)
        if block:
            _daemon()
        else:
            pl.run_thread([(_daemon, ())], 'daemon', False, limit_num=8)

    @property
    def unused_pool(self):
        return self.pool.filter(and_(Proxy.verify == True, Proxy.used == False, Proxy.delay < MAX_DELAY))

    def get_new_proxy(self):
        getter = self.getter.get_getter()
        self.logger.info('开始获取新代理, 使用{}'.format(getter.__name__))
        try:
            proxy_list = set(getter())
            assert len(proxy_list), '未能成功获取新代理'

            for proxy in proxy_list - set(self.pool.all()):
                SESSION.add(proxy)
            SESSION.commit()
            self.logger.info('获取新代理{}个, 当前代理总数{}个'.format(len(proxy_list), self.pool.count()))
        except Exception as e:
            self.logger.error(e)
            self.logger.warning('更换自身代理')
            self_proxy = self.get_fast_proxy()
            if self_proxy:
                self.getter.proxy = {'http': self_proxy}
            else:
                self.logger.warning('代理池为空')

    def time_out_update(self):
        while self.keep_check:
            try:
                now = time.time()
                update_proxy_list = self.pool.filter(
                    or_(
                        Proxy.verify == False,
                        and_(Proxy.used == True, Proxy.use_last < now - 60 * 60),
                        and_(Proxy.used == False, Proxy.ver_last < now - MAX_UPDATE_LENGTH)
                    )
                ).all()
                if update_proxy_list:
                    tasks = [proxy.test_delay() for proxy in update_proxy_list]
                    async_run(tasks)

                    self.pool.filter(
                        or_(
                            Proxy.wait_delete == True,
                            and_(Proxy.verify == True, Proxy.delay >= MAX_DELAY)
                        )
                    ).delete()
                    SESSION.commit()
                    self.logger.info('本轮有效性检查结束')
                unused_num = self.unused_pool.count()
                if unused_num < MIN_PROXY_NUM:
                    self.logger.info('当前代理数目{}个, 获取新代理'.format(unused_num))
                    self.get_new_proxy()
                else:
                    self.logger.info('当前代理数目{}个, 代理有效性检查暂停'.format(unused_num))
                time.sleep(30)
            except Exception as e:
                self.logger.error(e)

    def time_out_update_swich(self):
        if not pl.search_thread(name='keep_cheek'):
            self.logger.info('开始代理有效性检查')
            self.keep_check = True
            pl.run_thread([(self.time_out_update, ())], 'keep_cheek', False, limit_num=8)
        else:
            self.logger.info('停止代理有效性检查')
            self.keep_check = False
            pl.kill_thread(name='keep_cheek')

    def get_fast_proxy(self):
        proxy = self.unused_pool.order_by(Proxy.delay).first()
        if proxy:
            proxy.use()
            return proxy.addr
        else:
            return ''

    def get_all(self):
        return self.unused_pool.all()

if __name__ == '__main__':
    try:
        ProxyPool().daemon(True)
    except:
        pass