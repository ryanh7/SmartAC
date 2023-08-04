# SmartAC
[![hacs_badge](https://img.shields.io/badge/HACS-Custom-41BDF5.svg)](https://github.com/hacs/integration)

适配开源项目 [irext](https://site.irext.net/) 红外码库文件格式的 home assistant 红外空调插件。借助 irext 丰富的红外空调码库，可将众多红外空调接入 home assistant。

# 硬件准备
支持以下红外发射器
* 基于esphome的红外遥控器
* 基于mqtt的红外遥控器
* 博联红外遥控器
* 小米红外遥控器
## 使用基于esphome的红外遥控器
在esphome的配置文件中添加以下示例配置:
```yaml
api:
  services:
    - service: send_ir_raw
      variables:
        command: int[]
      then:
        - remote_transmitter.transmit_raw:
            code: !lambda 'return command;'
            carrier_frequency: 38k

remote_transmitter: # 参考esphome文档
  pin: GPIO23
  carrier_duty_percent: 50%
```
更新固件后接入 home assistant
## 基于mqtt的红外发射器
发射器应能接收并处理mqtt消息。mqtt消息内容为json字符串格式的高低电平信号持续时长序列：
```json
[450,320,450,320,450,320,450,320]
```

## 基于博联或小米红外遥控器
自行接入 home assistant

# 安装
* 方法一：通过 hacs 自定义存储库添加并安装
* 方法二：将 custom_components/smartac 目录复制至 home assistant 配置目录下的 custom_components 目录
# 安装码库
1. 按需从 [https://site.irext.net/sdk/](https://site.irext.net/sdk/) 下载离线码库并解压bin文件至 custom_components/smartac/codes/ 目录下
2. 按需编辑码库索引 codes/index.json

# 配置
安装完成后应至少重启一次 home assistant 以加载SmartAC插件。在 home assistant 的“配置>设备与服务>添加集成”中搜索SmartAC并配置一到多个空调。