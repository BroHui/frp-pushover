# coding: utf-8

import http.client
import urllib
import os
import socket


def send_text(msg):
    token = os.getenv('PUSHOVER_TOKEN', None)
    user = os.getenv('PUSHOVER_USER', None)
    msg_utf8 = msg.encode('utf-8')
    if not token or not user:
        print('Pushover token or user empty!')
        return -1

    content = ""
    conn = http.client.HTTPSConnection("api.pushover.net:443", timeout=3)
    try:
        conn.request("POST", "/1/messages.json",
                     urllib.parse.urlencode({
                         "token": token,
                         "user": user,
                         "message": msg_utf8,
                     }), {"Content-type": "application/x-www-form-urlencoded"})
    except socket.timeout as st:
        print('timeout received')
        return -3
    except http.client.HTTPException as e:
        print('request error')
    else:
        try:
            resp = conn.getresponse()
            content = resp.read()
            print(f"resp {resp.status} {resp.reason} {content}")
        except http.client.RemoteDisconnected:
            return -2
    finally:
        conn.close()

    return content


if __name__ == '__main__':
    send_text("aloha!")
