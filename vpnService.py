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

    overflow = round((current_timestamp - monthStart) / (monthEnd - monthStart) * 1000 - used, 3)
    position = {
        "used": used,
        "free": 1000 - used,
        "overflow": overflow
    }
    return position

# 测试连接中国网络是否畅通 通过中国境内控制服务器的IP地址测试
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


def putChineseNetStatusTODatabase(status,statusAddress):
    with open('InternetService-status.txt', 'w', encoding='utf-8') as file:
        file.write(f"{status}:")
    uploadFile('InternetService-status.txt', 'InternetService/SingaporeInternetStatus.txt', 'markdown-storage-service')

def controlSpeed(usageDict,InternetPortName):
    def set_bandwidth_limit(interface, download, upload):
        # 清除在指定接口上的所有限制
        subprocess.run(['wondershaper', 'clear', interface], check=True)
        # 设置下载和上传速度限制
        subprocess.run(['wondershaper', interface, str(download), str(upload)], check=True)

    def remove_bandwidth_limit(interface):
        # 清除限制
        subprocess.run(['wondershaper', 'clear', interface], check=True)

    if usageDict != None and usageDict['overflow'] < 0:
        set_bandwidth_limit(InternetPortName, '375', '375')
    else:
        try:
            remove_bandwidth_limit(InternetPortName)
        except Exception as e:
            print(f"{e}：不需要清除eth0")
    print("controlSpeed")


def selectChineseNet(chineseAddress, PublicInternetAddress,statusAddress):
    chineseNetStatus = getChineseNetStatus(chineseAddress)
    if chineseNetStatus:
        putChineseNetStatusTODatabase(f"1:{PublicInternetAddress}", statusAddress)
    else:
        putChineseNetStatusTODatabase(f"0:{PublicInternetAddress}", statusAddress)
    print(f"chineseNetStatus:{chineseNetStatus}")


# 生成 v2ray 订阅链接b64编码
def v2ray_subscribe(address, name):
    with open('nginxPort', 'r', encoding='utf-8') as file:
        port = file.read()
    server_info = {
        "v": "2",
        "ps": name,
        "add": address,
        "port": port,
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


def controlSubscribeForV2ray(PublicInternetAddress, InternetName, V2rayAddress):
    subscribe1 = v2ray_subscribe(PublicInternetAddress, InternetName)
    v2rayString = f'{subscribe1}'
    with open('SubscribeForV2ray.txt', 'w', encoding='utf-8') as file:
        file.write(v2rayString)
    uploadFile('SubscribeForV2ray.txt', V2rayAddress,
               'markdown-storage-service')
    print(v2rayString)


if __name__ == '__main__':
    chineseAddress = '8.134.39.24'
    InternetServiceName = "Singapore-Intetnet"
    SingaporeInternetStatus = "InternetService/SingaporeInternetStatus.txt"
    V2rayAddressName = "InternetService/SubscribeForV2ray-ICJwb3J0IjogIjQ0.txt"
    InternetPortName = "ens5"  # 网口名称 通过 ip link show   命令查看
    while True:
        try:
            PublicInternetAddress = getPublicInternetAddress()  # 获取公网IP
            usageDict = get_instance_data_usage(InternetServiceName)  # 获取目标服务器的流量使用情况
            time.sleep(10)
            selectChineseNet(chineseAddress, PublicInternetAddress, SingaporeInternetStatus)  # 查询中国网络状态 并提交状态到数据库
            time.sleep(10)
            controlSpeed(usageDict,InternetPortName)  # 控制当前服务网络速度
            time.sleep(10)
            controlSubscribeForV2ray(PublicInternetAddress, InternetServiceName, V2rayAddressName)  # 提交链接到数据库
        except Exception as e:
            print(e)
        time.sleep(120)
