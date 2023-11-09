#!/usr/bin/python3
import subprocess
import time
import urllib.request
import boto3
from boto3.session import Session
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


def stopAddress(instance_name):
    region_name = 'ap-southeast-1'
    with open('key.json', 'r') as file:
        Data = json.load(file)
    access_key = Data['access_key']
    secret_key = Data['secret_key']
    lightsail = boto3.client('lightsail', region_name=region_name, aws_access_key_id=access_key,
                             aws_secret_access_key=secret_key)
    try:
        response = lightsail.stop_instance(
            instanceName=instance_name
        )
        print(f"成功停止实例 {instance_name}")
        return True
    except Exception as e:
        print(f"停止实例 {instance_name} 失败: {str(e)}")
        return False


def startAddress(instance_name):
    region_name = 'ap-southeast-1'
    with open('key.json', 'r') as file:
        Data = json.load(file)
    access_key = Data['access_key']
    secret_key = Data['secret_key']
    lightsail = boto3.client('lightsail', region_name=region_name, aws_access_key_id=access_key,
                             aws_secret_access_key=secret_key)
    try:
        # 启动实例
        response = lightsail.start_instance(
            instanceName=instance_name
        )
        print(f"成功启动实例 {response}")
        return True
    except Exception as e:
        print(f"启动实例 {instance_name} 失败: {str(e)}")
        return False


def putChineseNetStatusTODatabase(status):
    with open('InternetService-status.txt', 'w', encoding='utf-8') as file:
        file.write(str(status))
    uploadFile('InternetService-status.txt', 'InternetService/InternetService-status.txt', 'markdown-storage-service')


def updateAddress():
    instance_name = 'intetnetServer'
    stopAddress(instance_name)
    time.sleep(60)
    startAddress(instance_name)
    # 修改网络状态
    putChineseNetStatusTODatabase(1)


def updatetranspondAddress(address):
    command = f"./gost -L tcp://:443/{address}:443 &"
    subprocess.run(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, stdin=subprocess.DEVNULL)


def getAddressAtatus():
    with urllib.request.urlopen(
            'https://markdown-storage-service.s3.ap-southeast-1.amazonaws.com/InternetService/InternetService-status.txt') as url:
        addressAtatus = url.read().decode()
    addressAtatusList = addressAtatus.split(":")
    status = addressAtatusList[0]
    address = addressAtatusList[1]
    return {"status": status, "address": address}


if __name__ == '__main__':
    while True:
        try:
            # 网络状态控制
            preAddress = ''
            addressAtatusDict = getAddressAtatus()

            if addressAtatusDict['status'] == '0':
                updateAddress()

            # 端口流量转发控制
            if addressAtatusDict['address'] != preAddress:
                if preAddress == '':
                    preAddress = addressAtatusDict['address']
                    updatetranspondAddress(preAddress)
                else:
                    subprocess.run('reboot', shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                                   stdin=subprocess.DEVNULL)
        except Exception as e:
            print(e)
        time.sleep(10)
