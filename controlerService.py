#!/usr/bin/python3
import time
import urllib.request
import boto3
import json


def stopAddress(instance_name, region_name):
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


def startAddress(instance_name, region_name):
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


def updateAddress(instance_name, region_name):
    stopAddress(instance_name, region_name)
    time.sleep(120)
    startAddress(instance_name, region_name)
    time.sleep(120)


def getAddressAtatus(AddressAtatus):
    with urllib.request.urlopen(AddressAtatus) as url:
        addressAtatus = url.read().decode()
    addressAtatusList = addressAtatus.split(":")
    status = addressAtatusList[0]
    address = addressAtatusList[1]
    return {"status": status, "address": address}


if __name__ == '__main__':
    while True:
        SingaporeData = {
            "instance_name": "Singapore-Internet",
            "region_name": "ap-southeast-1",
            "AddressAtatus": "https://markdown-storage-service.s3.ap-southeast-1.amazonaws.com/InternetService/SingaporeInternetStatus.txt"
        }
        try:
            # 网络状态控制
            addressAtatusDict = getAddressAtatus(SingaporeData['AddressAtatus'])
            if addressAtatusDict['status'] == '0':
                updateAddress(SingaporeData['instance_name'], SingaporeData['region_name'])
                print(f"{SingaporeData['instance_name']}更新ip成功")
            else:
                print(f"{SingaporeData['instance_name']}国际ip正常")
        except Exception as e:
            print(e)
        time.sleep(30)

        AmericaData = {
            "instance_name": "America-Internet",
            "region_name": "us-east-1",
            "AddressAtatus": "https://markdown-storage-service.s3.ap-southeast-1.amazonaws.com/InternetService/AmericaInternetStatus.txt"
        }

        try:
            # 网络状态控制
            addressAtatusDict = getAddressAtatus(AmericaData['AddressAtatus'])
            if addressAtatusDict['status'] == '0':
                updateAddress(AmericaData['instance_name'], AmericaData['region_name'])
                print(f"{AmericaData['instance_name']}更新ip成功")
            else:
                print(f"{AmericaData['instance_name']}国际ip正常")
        except Exception as e:
            print(e)
        time.sleep(30)
