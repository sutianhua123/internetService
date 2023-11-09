#!/usr/bin/python3
import subprocess
import time
import boto3
from datetime import datetime
from boto3.session import Session
import base64
import json


def uploadFile(originalPath, endPath, bucketName):

    with open('key.json', 'r') as file:
        Data = json.load(file)
    access_key = Data['access_key']
    secret_key = Data['secret_key']
    session = Session(aws_access_key_id=access_key, aws_secret_access_key=secret_key)
    s3 = session.resource("s3")
    upload_data = open(originalPath, 'rb')
    file_obj = s3.Bucket(bucketName).put_object(Key=endPath, Body=upload_data)
    print(file_obj)


def get_current_month_first_day_zero_time():
    return datetime.strptime(datetime.fromtimestamp(int(time.time())).strftime("%Y-%m"), "%Y-%m")


def get_current_month_last_day_last_time():
    return datetime.now().replace(month=datetime.now().month + 1, day=1, hour=0, minute=0, second=0)


def get_instance_data_usage(instance_name):
    import time
    region_name = 'ap-southeast-1'
    with open('key.json', 'r') as file:
        Data = json.load(file)
    access_key = Data['access_key']
    secret_key = Data['secret_key']
    client = boto3.client('lightsail', region_name=region_name, aws_access_key_id=access_key,
                          aws_secret_access_key=secret_key)
    start_time = get_current_month_first_day_zero_time()
    end_time = get_current_month_last_day_last_time()
    start_time_str = start_time.strftime('%Y-%m-%dT%H:%M:%SZ')
    end_time_str = end_time.strftime('%Y-%m-%dT%H:%M:%SZ')

    response = client.get_instance_metric_data(
        instanceName=instance_name,
        metricName='NetworkOut',
        period=6 * 600 * 24,
        unit='Bytes',
        statistics=[
            'Sum'
        ],
        startTime=start_time_str,
        endTime=end_time_str
    )
    data_points = response['metricData']
    total_data_usage = sum([data_point['sum'] for data_point in data_points])
    used = round(total_data_usage / (1024 * 1024 * 1024), 3)

    monthStart = datetime.strptime(datetime.fromtimestamp(int(time.time())).strftime("%Y-%m"), "%Y-%m").timestamp()
    monthEnd = datetime.now().replace(month=datetime.now().month + 1, day=1, hour=0, minute=0, second=0).timestamp()
    current_timestamp = time.time()

    overflow = round((current_timestamp - monthStart) / (monthEnd - monthStart) * 2000 - used, 3)
    position = {
        "used": used,
        "free": 2000 - used,
        "overflow": overflow
    }
    return position


def getChineseNetStatus(address):
    index = 0
    while True:
        String = ''
        try:
            output = subprocess.check_output(f"ping -c 4 {address}", shell=True, text=True)
            String = String + output
        except subprocess.CalledProcessError as e:
            pass

        if "4 received" in String or "3 received" in String or "2 received" in String:
            return True
        else:
            index = index + 1
            if index == 10:
                return False
            time.sleep(5)


def getPublicInternetAddress():
    internetAddress = ""
    try:
        internetAddress = subprocess.check_output("curl -4 ifconfig.me", shell=True, text=True)
    except subprocess.CalledProcessError as e:
        pass
    return internetAddress


def putChineseNetStatusTODatabase(status):
    with open('InternetService-status.txt', 'w', encoding='utf-8') as file:
        file.write(str(status))
    uploadFile('InternetService-status.txt', 'InternetService/InternetService-status.txt', 'markdown-storage-service')


def controlSpeed(usageDict):
    def set_bandwidth_limit(interface, download, upload):
        # 清除在指定接口上的所有限制
        subprocess.run(['wondershaper', 'clear', interface], check=True)
        # 设置下载和上传速度限制
        subprocess.run(['wondershaper', interface, str(download), str(upload)], check=True)

    def remove_bandwidth_limit(interface):
        # 清除限制
        subprocess.run(['wondershaper', 'clear', interface], check=True)

    if usageDict != None and usageDict['overflow'] < 0:
        set_bandwidth_limit('ens5', '750', '750')
    else:
        try:
            remove_bandwidth_limit('ens5')
        except Exception as e:
            print(f"{e}：不需要清除eth0")
    print("controlSpeed")


def getClashString():
    String = """
port: 7890
socks-port: 7891
allow-lan: false
mode: Rule
log-level: info
external-controller: 127.0.0.1:9090
proxies:
  - {name: Singapore Internet Service, server: serverName1, port: 443, type: vmess, uuid: af41686b-cb85-494a-a554-eeaa1514bca7, alterId: 0, cipher: auto, tls: true,skip-cert-verify: true, servername: www.harvard.edu, network: ws, ws-opts: {path: /xNGJjYTciLA0KICAiYWlkIjogIjAiLA0KICAic2N5IjogInplcm8iLA0KICAibmV0, headers: {Host: www.harvard.edu}}}
  - {name: GuangZhou Transfer Service, server: serverName2, port: 443, type: vmess, uuid: af41686b-cb85-494a-a554-eeaa1514bca7, alterId: 0, cipher: auto, tls: true,skip-cert-verify: true, servername: www.harvard.edu, network: ws, ws-opts: {path: /xNGJjYTciLA0KICAiYWlkIjogIjAiLA0KICAic2N5IjogInplcm8iLA0KICAibmV0, headers: {Host: www.harvard.edu}}}

proxy-groups:
  - name: 国际互联网
    type: select
    proxies:
      - Singapore Internet Service
      - GuangZhou Transfer Service
  
  - name: 中国互联网
    type: select
    proxies:
    - DIRECT

rules:
  - GEOIP,CN,中国互联网
  - MATCH,国际互联网
"""
    return String


def controlChineseNet(chineseAddress):
    chineseNetStatus = getChineseNetStatus(chineseAddress)
    if not chineseNetStatus:
        putChineseNetStatusTODatabase(0)
    print(f"chineseNetStatus:{chineseNetStatus}")


def v2ray_subscribe(address, name):
    server_info = {
        "v": "2",
        "ps": name,
        "add": address,
        "port": "443",
        "id": "af41686b-cb85-494a-a554-eeaa1514bca7",
        "aid": "0",
        "scy": "zero",
        "net": "ws",
        "type": "none",
        "host": "www.harvard.edu",
        "path": "/xNGJjYTciLA0KICAiYWlkIjogIjAiLA0KICAic2N5IjogInplcm8iLA0KICAibmV0",
        "tls": "tls",
    }
    json_str = json.dumps(server_info)
    base64_str = base64.urlsafe_b64encode(json_str.encode()).decode()
    subscription_link = f"vmess://{base64_str}"
    return subscription_link


def controlSubscribeForV2ray(usageDict, chineseAddress, PublicInternetAddress):
    used = round(usageDict['used'])
    free = round(usageDict['free'])
    overflow = round(usageDict['overflow'])
    statusString = f"used:{used} free:{free} overflow:{overflow}"
    subscribe1 = v2ray_subscribe(PublicInternetAddress, "Singapore Internet Service")
    subscribe2 = v2ray_subscribe(chineseAddress, "GuangZhou Transfer Service")
    subscribe3 = v2ray_subscribe(statusString, 'internetStatus')
    v2rayString = f'{subscribe1}\n{subscribe2}\n{subscribe3}'
    with open('SubscribeForV2ray.txt', 'w', encoding='utf-8') as file:
        file.write(v2rayString)
    uploadFile('SubscribeForV2ray.txt', 'InternetService/SubscribeForV2ray-ICJwb3J0IjogIjQ0.txt',
               'markdown-storage-service')
    print(v2rayString)


def controlSubscribeForClash(usageDict, chineseAddress, PublicInternetAddress):
    ClashString = getClashString()
    used = round(usageDict['used'])
    free = round(usageDict['free'])
    overflow = round(usageDict['overflow'])
    statusString = f"used:{used} free:{free} overflow:{overflow}"
    ClashString = ClashString.replace('serverName1', PublicInternetAddress)
    ClashString = ClashString.replace('serverName2', chineseAddress)
    with open('SubscribeForClash.yml', 'w', encoding='utf-8') as file:
        file.write(ClashString)
    uploadFile('SubscribeForClash.yml', 'InternetService/SubscribeForClash-wgInBvcnQiOiAiND.yml',
               'markdown-storage-service')
    print(statusString)


if __name__ == '__main__':
    chineseAddress = '8.134.39.24'
    while True:
        PublicInternetAddress = getPublicInternetAddress()
        usageDict = get_instance_data_usage('intetnetServer')
        time.sleep(10)
        controlChineseNet(chineseAddress)  # 控制中国网络状态
        time.sleep(10)
        controlSpeed(usageDict)  # 控制当前服务网络速度
        time.sleep(10)
        controlSubscribeForV2ray(usageDict, chineseAddress, PublicInternetAddress)
        controlSubscribeForClash(usageDict, chineseAddress, PublicInternetAddress)
        time.sleep(30)
