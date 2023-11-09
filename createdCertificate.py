import requests
import subprocess

def createdCertificate():
    try:
        # 发送GET请求到ifconfig.me，并获取响应内容
        response = requests.get('https://ifconfig.me')
        public_ip = response.text.strip()
        print(public_ip)
        subprocess.run("openssl ecparam -genkey -name prime256v1 -out ca.key", shell=True, check=True)
        subprocess.run(f"openssl req -new -x509 -days 36500 -key ca.key -out ca.crt -subj '/CN={public_ip}'",
                       shell=True, check=True)
    except Exception as e:
        return str(e)
    return public_ip

def updateNginxConf(certificateIP):
    with open('/etc/nginx/nginx2.conf', 'r') as file:
        text = file.read()
    text = text.replace("localhost", certificateIP)
    with open('/etc/nginx/nginx.conf', 'w') as file:
        file.write(text)

if __name__ == '__main__':
    # 生成证书
    certificateIP = createdCertificate()
    # 对nginx.conf文件进行更新
    updateNginxConf(certificateIP)
