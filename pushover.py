# coding: utf-8

import http.client
import urllib
import os
import json
import socket

PUSHOVER_TIMEOUT = 5


def send_text(msg):
    """
        增加一个retry的机制
    :param msg:
    :return:
    """
    for i in range(3):  # retry times
        push_ret = pushover(msg)
        if push_ret.get('status', -1) == 1:
            break
        print('Pushover failed, retry')


def pushover(msg):
    token = os.getenv('PUSHOVER_TOKEN', None)
    user = os.getenv('PUSHOVER_USER', None)
    msg_utf8 = msg.encode('utf-8')
    abnormal_resp = {'status': -1, 'request': 'err'}
    if not token or not user:
        print('Pushover token or user empty!')
        return abnormal_resp

    content = ""
    conn = http.client.HTTPSConnection("api.pushover.net:443", timeout=PUSHOVER_TIMEOUT)
    try:
        conn.request("POST", "/1/messages.json",
                     urllib.parse.urlencode({
                         "token": token,
                         "user": user,
                         "message": msg_utf8,
                     }), {"Content-type": "application/x-www-form-urlencoded"})
    except socket.timeout as st:
        print('timeout received')
        return abnormal_resp
    except http.client.HTTPException as e:
        print('request error')
        return abnormal_resp
    except ConnectionResetError as e:
        print('ConnectionResetError')
        return abnormal_resp
    except Exception as e:
        print('Exception on connect request to pushover.net')
        return abnormal_resp
    else:
        try:
            resp = conn.getresponse()
            content_b = resp.read()
            content = json.loads(content_b.decode('utf-8'))
            print(f"resp {resp.status} {resp.reason} {content}")
        except http.client.RemoteDisconnected:
            return abnormal_resp
    finally:
        conn.close()

    return content


if __name__ == '__main__':
    print(send_text("aloha!"))
