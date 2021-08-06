# coding: utf-8
"""
    Base on https://github.com/zfb132/frp_info/blob/master/app/model/HandleFrpMsg.py

"""

from datetime import datetime
import logging
import time

from pushover import send_text
from qqwry import QQwry

logging = logging.getLogger('runserver.handlefrpmsg')

CONN_LIMIT_SEC = 20
conn_event_cached = {}
banned_ip = []
BANNED_HOUR = 1
def ip_check(ip):
    """ 防骚扰规则配置 """
    global conn_event_cached, banned_ip
    print(conn_event_cached)
    print(banned_ip)
    cur_ts = time.time()
    # 在ban列表中，并且没有关满1小时的
    if ip in banned_ip:
        banned_ts = conn_event_cached.get(ip, 0)
        logging.info("ip {} in banned list, last ban time is {}".format(ip, banned_ts))
        if (cur_ts - banned_ts) > (3600 * BANNED_HOUR):  # 放出小黑屋
            banned_ip.remove(ip)
            conn_event_cached[ip] = cur_ts
            logging.info("ip {} release from banned.".format(ip))
            return True
        else:
            logging.info("ip {} keep banned".format(ip))
            return False  # 继续关

    # N秒内有两次连接的，ban
    if ip not in conn_event_cached:  # 首次访问，通过
        conn_event_cached[ip] = cur_ts
        logging.info("ip {} is first touch, pass".format(ip))
        return True

    last_conn_ts = conn_event_cached.get(ip, 0) 
    
    if (cur_ts - last_conn_ts) < CONN_LIMIT_SEC:
        logging.info("ip {} access limited".format(ip))
        if ip not in banned_ip:
            banned_ip.append(ip)
            logging.info("ip {} join the banned list".format(ip))
            conn_event_cached[ip] = cur_ts
        return False
    else:
        logging.info("normal access, let it {} go".format(ip))
        return True  # 放行


def ip2geo(ip):
    """ 采用纯真库 """
    try:
        q = QQwry()
        q.load_file('QQWry.Dat')
        geo = ' '.join(q.lookup(ip))
    except Exception:
        geo = 'QQwry lookup failed.'

    return geo


# 格式化时间戳
def timestamp_to_str(timestamp):
    return datetime.fromtimestamp(timestamp).strftime("%Y-%m-%d %H:%M:%S")


# 处理Login操作：frpc登录frps
def login_operation(data):
    """
        {
            "content": {
                "version": <string>,
                "hostname": <string>,
                "os": <string>,
                "arch": <string>,
                "user": <string>,
                "timestamp": <int64>,
                "privilege_key": <string>,
                "run_id": <string>,
                "pool_count": <int>,
                "metas": map<string>string
            }
        }
    :param data:
    :return:
    """
    str_fmt = "frp-client登录\nfrp版本：{}\n主机ID：{}\n主机名：{}\n系统类型：{}\n系统架构：{}\n登录时间：{}\n连接池大小：{}"
    txt = str_fmt.format(
        data['version'], data['run_id'], data['hostname'], data['os'],
        data['arch'], timestamp_to_str(data['timestamp']), data['pool_count']
    )
    return txt


# 处理NewProxy操作：frpc与frps之间建立通道用于内网穿透
# proxy_name是frpc与frps之间建立的连接的名称
def newproxy_operation(data):
    """
        {
            "content": {
                "user": {
                    "user": <string>,
                    "metas": map<string>string
                },
                "proxy_name": <string>,
                "proxy_type": <string>,
                "use_encryption": <bool>,
                "use_compression": <bool>,
                "group": <string>,
                "group_key": <string>,

                // tcp and udp only
                "remote_port": <int>,

                // http and https only
                "custom_domains": []<string>,
                "subdomain": <string>,
                "locations": <string>,
                "http_user": <string>,
                "http_pwd": <string>,
                "host_header_rewrite": <string>,
                "headers": map<string>string,

                "metas": map<string>string
            }
        }
    :param data:
    :return:
    """
    run_id = data['user']['run_id']
    str_fmt = "frp-client建立穿透代理\n主机ID：{}\n代理名称：{}\n代理类型：{}\n远程端口：{}\n"
    txt = str_fmt.format(
        run_id, data['proxy_name'], data['proxy_type'], data['remote_port']
    )
    return txt


# 处理NewUserConn操作：用户连接内网机器；用户（ssh）-->云服务器（frps）-->内网主机（frpc）
def newuserconn_operation(data):
    """
        {
            "content": {
                "user": {
                    "user": <string>,
                    "metas": map<string>string
                    "run_id": <string>
                },
                "proxy_name": <string>,
                "proxy_type": <string>,
                "remote_addr": <string>
            }
        }
    :param data:
    :return:
    """
    run_id = data['user']['run_id']
    ip = data['remote_addr'].split(':')[0]
    # 勿打扰时间
    banned = 0  # ban标记
    d = datetime.now()
    if d.hour in [23, 24, 0, 1, 2 ,3 ,4, 5, 6]:  # 睡觉时间不能连接，没有为什么
        is_allow = False
        banned = 1
    else:
        # 是否允许连接
        if ip in banned_ip:  # 预先判断是否被ban
            banned = 1
        is_allow = ip_check(ip)
        if is_allow:
            banned = 0  # 如果allow则banned设置掉，还是要显示的
        
    is_allow_txt = '放行' if is_allow else '拒绝'

    # 用户地理位置
    position = ip2geo(ip)

    str_fmt = "用户连接内网机器\n内网主机ID：{}\n代理名称：{}\n代理类型：{}\n登录时间：{}\n用户IP和端口：{}\n用户位置：{}\n允许用户连接：{}"
    txt = str_fmt.format(
        run_id, data['proxy_name'], data['proxy_type'], timestamp_to_str(data['timestamp']),
        data['remote_addr'], position, is_allow_txt
    )
    return txt, is_allow, banned


# 处理NewWorkConn操作
def newworkconn_operation(data):
    """
        新增 frpc 连接相关信息

        {
                "content": {
                    "user": {
                        "user": <string>,
                        "metas": map<string>string
                        "run_id": <string>
                    },
                    "run_id": <string>
                    "timestamp": <int64>,
                    "privilege_key": <string>
                }
        }
    :param data:
    :return:
    """
    run_id = data.get('user', {}).get('run_id', 'empty run id')
    txt = f"新work连接\n内网主机ID: {run_id}\n连接时间：{timestamp_to_str(data['timestamp'])}\n" \
          f"权限密钥{data.get('privilege_key', '')}"
    is_allowed = True
    return txt, is_allowed


def ping_operation(data):
    """
        {
            "content": {
                "user": {
                    "user": <string>,
                    "metas": map<string>string
                    "run_id": <string>
                },
                "timestamp": <int64>,
                "privilege_key": <string>
            }
        }
    :param data:
    :return:
    """
    return True


def handle_msg(data):
    """
        目前插件支持管理的操作类型有 Login、NewProxy、Ping、NewWorkConn 和 NewUserConn。

        POST /handler
        {
            "version": "0.1.0",
            "op": "Login",
            "content": {
                ... // 具体的操作信息
            }
        }

        请求 Header
        X-Frp-Reqid: 用于追踪请求
    :param data:
    :return:
    """
    # 当前建立frp的类型
    operation = data['op']
    # frp请求的具体信息
    content = data['content']
    logging.debug(content)
    # 发送给管理员用户的提示
    txt = ""
    # 是否允许用户ssh连接
    is_allowed = True
    # Ping操作每隔30s发送一次，不记录
    banned = 0
    if operation == 'Ping':
        return ping_operation(content)
    elif operation == 'Login':
        txt = login_operation(content)
    elif operation == 'NewProxy':
        txt = newproxy_operation(content)
    elif operation == 'NewUserConn':
        content['timestamp'] = int(time.time())
        txt, is_allowed, banned = newuserconn_operation(content)
    elif operation == 'NewWorkConn':
        txt, is_allowed = newworkconn_operation(content)
    else:
        # 基本不会出现此情况
        return True
    # pushover 推送
    if not banned:
        send_text(txt)
    return is_allowed
