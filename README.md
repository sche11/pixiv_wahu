# PixivWahu

Pixiv 插画收藏工具

## 简介
PixivWahu 的目的在于解决p站只能建一个收藏夹的痛点.
围绕「在本地储存插画数据」这个主题， PixivWahu 主要实现了下述功能
- 在本地数据库文件中储存收藏的插画，精确到页
- 将数据库中收藏的插画下载到本地储存库，精确到页
- 浏览 Pixiv 内容，如查看推荐、关注的画师、作品排行等

PixivWahu 使用了一些黑魔法，可以无需其他*工具*访问p站 API 以及图片服务，也不需要用卡的一批的 `i.pixiv.re`
实现细节主要来自 `pixivpy` 的 `ByPassSniAPI` ，也受到了 [@mashiro](https://2heng.xin/2017/09/19/pixiv/) 的启发

PixivWahu 直接基于的开源库
- `aiohttp` 异步 HTTP 库
- `click` 命令行处理
- `fuzzywuzzy` 字符串模糊匹配
- `vue` 前端框架
- `quasar` 前端 UI 框架


## 安装
### 使用系统级 Python 解释器

下载源码

构建依赖：
- `pipenv`
- `node.js`
- `quasar-cli`

安装依赖项
```shell
pipenv install
```

打包前端
```shell
quasar build
```

将打包好前端文件复制到 `static` 目录下

启动 PixivWahu
```shell
python -m wahu_backend.__init__
```

### 使用打包好的 Python Embeded 解释器
下载发行版，解压

找到 `PixivWahu.ps1` ，右键 - 使用 powershell 运行
> 要执行本地 powershell 脚本，可能需要修改本地脚本执行策略，详见微软文档

浏览器会自动打开


## 配置
PixivWahu 使用 TOML 格式配置

配置文件路径默认为 `conf.toml` ，可以使用命令行选项 `--config/-c` 覆盖

配置文件内容详见配置文件中的注释

## 说明
### `refresh_token`
由于p站的用户名/密码登录的接口无法使用（用于登录p站的程序不是本人写的，所以本人只知道不支持，具体原因不清楚），
所以为了连接p站服务，需要使用另一种方式：`refresh_token`，刷新密钥

通过 `refresh_token` 可以获得 `access_token` ，而 `access_token` 直接用于访问 Pixiv 服务

`refresh_token`是一个 `Cookie` ，形如`a8sD23d2fU6758zdfDdF`，可以标识用户身份，且长期有效，所以`pixivpy` 的作者使用它来登录p站
> 为了使用异步架构，本人用异步网络库 `aiohttp` 重构了 `pixivpy` ，命名为 `aiopixivpy`

要获得 `refresh_token` ，需要一个现代浏览器如Edge, Chrome, Firefox
运行 `GetToken.ps1` ，浏览器会自动打开，按照说明操作即可
> 来自[PixivBiu@txperl](https://github.com/txperl/PixivBiu)
> 还可参考[@ZipFile Pixiv OAuth Flow](https://gist.github.com/ZipFile/c9ebedb224406f4f11845ab700124362) 及 [OAuth with Selenium/ChromeDriver]( https://gist.github.com/upbit/6edda27cb1644e94183291109b8a5fde)

`refresh_token` 默认储存在 `user/refresh_token.txt` 中
**明码储存，注意保管**

### `access_token`
用于直接访问 Pixiv 服务

认证 `refresh_token` 获得了 `access_token` 后，`access_token` 将会被写入一个文件，默认为 `user/account_session.toml` ，在 `access_token` 的有效期内可以不用再次认证 `refresh_token`

### 插画详情
从 Pixiv 返回的插画信息的数据结构，包含了插画 ID ，标题，描述，标签，作者等信息

### 出现的简写
- `iid`: Illust ID ，插画 ID ，在 Pixiv 上用于标记每幅插画
- `uid`: User ID ，用户 ID ，在 Pixiv 上用于标记用户
- `fid`: File ID ，插画图片文件 ID ，其格式为 `<iid>-<page>` ，其中 `page` 为图片对应的页码；对于单页插画， `page` 为 `0`

### 插画数据库
每个「插画数据库」是一个 `sqlite` `.db` 文件，默认存放在 `user/databases` 下，内部储存了插画的详情和每幅插画收藏的页码

在浏览「插画数据库」时，图片文件将按下属顺序查找
- 查看所有连接到此「插画数据库」的「插画储存库」，如果找到了请求的文件，则返回
- 从 Pximg 服务器下载. 使用的清晰度默认为 `medium` ，可在配置文件中修改 `image.fallback_size`

### 插画储存库
每个「插画储存库」是一个目录，内有一个 `index.db` 文件，用于索引「文件」和「插画ID」

每个「插画储存库」连接到多个「插画数据库」，其连接关系默认在文件 `user/repos.toml` 中定义，运行时该文件会被更新，如要直接修改此文件，需要 PixivWahu 关闭后再修改

#### 同步流程
- 选择要连接到的「插画数据库」，可以多选
- 计算差集，即分别求得储存库中「多余的文件」和「没有的文件」
- 将「没有的文件」的索引插入 `index.db` 的「缓存区」
- 下载 「没有的文件」到储存库目录下
- 扫描「储存库目录」，将下载完成的文件的索引从「缓存区」移到「索引区」
- 扫描「储存库目录」，发现无效的索引和无效的文件，将其删除

### 命令行脚本
使用 [`click`](https://click.palletsprojects.com/en/8.1.x/) 创建命令行脚本，
在 「Home」 的命令行终端上执行

PixivWahu 预置了几个命令行脚本；也可以自行创建

用户命令行脚本默认存放在 `user/scripts` 下

### 缓存池
PixivWahu 为了优化体验使用了两个缓存池

- 插画详情缓存池：缓存一切从 Pixiv 加载的插画详情. 这是为了防止频繁调用 Pixiv 服务接口，因为每次只能查询一张插画，当插画量较大时会有一定的效率影响
- 图片缓存池：缓存从 Pximg 加载的图片

两个缓存池的大小可在配置文件中设定

### 临时下载目录
浏览 Pixiv 上的插画时，可以下载插画到这个目录. 默认为 `user/temp_dl`

### 插画下载
由于「储存库同步」和加载页面上的图片使用同一个模块，所以下载面板内两者都会被显示

### `WebSocket RPC`
即 `WebSocket Remote Procedure Call` ，是 PixivWahu 前后端的连接，如果连接断开，前端将无法使用

PixivWahu 分为前端和后端，后端由 Python 实现，前端在浏览器中运行，因此使用了 `WebSocket` 协议进行前后端通信
