import requests
import subprocess

def createdCertificate():
    try:
        response = requests.get('https://ifconfig.me')
        public_ip = response.text.strip()
        print(public_ip)
        subprocess.run("openssl ecparam -genkey -name prime256v1 -out ca.key", shell=True, check=True)
        subprocess.run(f"openssl req -new -x509 -days 36500 -key ca.key -out ca.crt -subj '/CN={public_ip}'",
                       shell=True, check=True)
    except Exception as e:
        return str(e)
createdCertificate()
