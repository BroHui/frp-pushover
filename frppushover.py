# coding: utf-8
import sys
import os
import json
import traceback
from functools import wraps

from django.conf import settings
from django.urls import path
from django.http import HttpResponse, HttpResponseForbidden, JsonResponse, Http404
from django.core.wsgi import get_wsgi_application

from HandleFrpMsg import handle_msg

DEBUG = os.getenv('DEBUG', '0') == '1'
SECRET_KEY = os.getenv('SECRET_KEY', 'yoursecret_key')
ALLOWED_HOSTS = os.getenv('ALLOWED_HOSTS', 'localhost').split(',')
TOKEN_LIST = os.getenv('TOKEN_LIST', '')
TOKEN_LIST = TOKEN_LIST.split(',') if TOKEN_LIST else []
if not TOKEN_LIST: print("Run server as NO AUTH mode!")
settings.configure(
    DEBUG=DEBUG,
    ROOT_URLCONF=__name__,
    SECRET_KEY=SECRET_KEY,
    ALLOWED_HOSTS=ALLOWED_HOSTS,
    MIDDLEWARE_CLASSES=(
        'django.middleware.common.CommonMiddleware',
    ),
    TOKEN_LIST=TOKEN_LIST
)
"""  Simple auth  """


def verify_request(func):
    @wraps(func)
    def returned_wrapper(request, *args, **kwargs):
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        request_ip = x_forwarded_for.split(',')[0] if x_forwarded_for else request.META.get('REMOTE_ADDR')
        # Auth
        token = request.GET.get('token', '')
        if settings.TOKEN_LIST and (not token or token not in settings.TOKEN_LIST):
            print(f'Unauthorized Request from {request_ip}')
            return HttpResponseForbidden()
        # get dict
        get_dict = request.GET.dict()
        request.param = lambda x: get_dict.get(x, '')
        # get body
        request_body = request.body
        if request_body:
            try:
                request.json = json.loads(request_body)
            except json.decoder.JSONDecodeError:
                print('+verify_request Error: parse request body to json failed')
                request.json = {}
        return func(request, *args, **kwargs)

    return returned_wrapper


"""  Your Views here """


@verify_request
def handler(request):
    """
    :param request:
    :return:
        拒绝执行操作

        {
           "reject": true,
           "reject_reason": "invalid user"
        }
        允许且内容不需要变动

        {
            "reject": false,
            "unchange": true
        }
        允许且需要替换操作内容

        {
            "unchange": "false",
            "content": {
                ... // 替换后的操作信息，格式必须和请求时的一致
            }
        }
    """
    if request.method == 'GET':
        return HttpResponseForbidden()
    # 处理传入
    try:
        is_allowed = handle_msg(request.json)
        if is_allowed:
            # 不拒绝连接，保持不变；即不对内容进行任何操作
            response_data = {"reject": False, "unchange": True}
        else:
            # 拒绝连接，非法用户
            response_data = {"reject": True, "reject_reason": "invalid user"}
        return JsonResponse(response_data)
    except Exception as ex:
        traceback.print_exc()
        return Http404()


urlpatterns = [
    path('handler', handler),
]
# uWSGI Supports
application = get_wsgi_application()

if __name__ == '__main__':
    from django.core.management import execute_from_command_line

    execute_from_command_line(sys.argv)
