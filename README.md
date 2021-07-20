# frppushover

Requirements:
1. Python 3.8
2. Django 3.2LTS (Should be work with lower or higher version, but I'ver not tested.)

Quick Start:
1. Build your own docker image.
```
#docker build -t frppushover .
```
2. Boost your app with docker power!
```
docker run -d --restart=always --name frppushover -p 127.0.0.1:8081:8081 -e PUSHOVER_TOKEN=x -e PUSHOVER_USER=x frppushover
```

frps 中插件配置
```ini
[common]
bind_port = 7000

[plugin.frp-info]
addr = 127.0.0.1:8081
path = /handler
ops = Login,NewProxy,NewWorkConn,NewUserConn
```
addr: 插件监听的网络地址。 path: 插件监听的 HTTP 请求路径。 ops: 插件需要处理的操作列表，多个 op 以英文逗号分隔。


元数据
为了减少 frps 的代码修改，同时提高管理插件的扩展能力，在 frpc 的配置文件中引入自定义元数据的概念。元数据会在调用 RPC 请求时发送给插件。
元数据以 meta_ 开头，可以配置多个，元数据分为两种，一种配置在 common 下，一种配置在各个 proxy 中。
```ini
# frpc.ini
[common]
server_addr = 127.0.0.1
server_port = 7000
user = fake
meta_token = fake
meta_version = 1.0.0

[ssh]
type = tcp
local_port = 22
remote_port = 6000
meta_id = 123
```
