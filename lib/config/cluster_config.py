import logging, paramiko, requests


def check_ssh_is_ready(node_desc, env_desc):
    try:
        logger = logging.getLogger("CLUSTER_CONFIG")
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh.connect(node_desc.get("ip"), username=env_desc.get("ssh_user"), timeout=1.0)
        ssh.close()
        return True
    except:
        logger.warning("Could not connect to %s" % node_desc.get("ip"))
        return False


def check_cloud9_is_ready(node_desc, env_desc):
    logger = logging.getLogger("CLUSTER_CONFIG")
    ret_bool = False
    cloud9_ide_url = "http://%s/ide.html" % (node_desc.get("public_ip"))
    result = requests.get(cloud9_ide_url)
    if result.status_code == 200 and "<title>Cloud9</title>" in result.text:
        ret_bool = True
    if result.status_code == 401 and "Unauthorized" in result.text:
        ret_bool = True
    if not ret_bool:
        logger.error("%s: status code %d" % (node_desc.get("ip"), result.status_code))
    return ret_bool


def check_jupyter_is_ready(node_desc, env_desc):
    logger = logging.getLogger("CLUSTER_CONFIG")
    ret_bool = False
    cloud9_ide_url = "http://%s/tree?" % (node_desc.get("public_ip"))
    result = requests.get(cloud9_ide_url)
    if "<title>Home</title>" in result.text:
        ret_bool = True
    if "/static/style/style.min.css" in result.text:
        ret_bool = True
    if not ret_bool:
        logger.error("%s: status code %d" % (node_desc.get("ip"), result.status_code))
    return ret_bool


CLUSTER_CONFIG = {
    "controller": {
        "ip": "192.168.122.236",
        "user": "pipi",
        "public_key": """ssh-rsa AAAAB3NzaC1yc2EAAAADAQABAAABAQDBYucLioUp4HsoQccYrgkEjpDm92tN9O5pWAkEpb2CnzjL9+a6rwF0Qs6n8ulwG2AYiUC5p7IINCoMgKXuNEBgB14eMiyy7yqNy81VuHOTzL3+cM8zz81rROyCbgA7rtwqaSnwrMH3GBRRUuUg7p8lwlBNm3rforGg5469htr+n1oenquSu836O4EC6PQblwkjfJrlO/dXBsuSlgQg8a4SFXpoGn/yCaNdkvswqyOQTFogKfVEfbxAz4UMIWakTXCvvNwxZnjCR8itQDCk/nWNDh1fOvvhyrCA27C0z2Fa4VZS7fMpQTFgAAUN+P9uwuEKRdrW7Khn8FuEUsQ7IaQn pipi@piserver"""
    },
    "nodes":  [
        {
            "name": "node-1",
            "id": "ea76306b",
            "port_number": 1,
            "ip": "192.168.1.51",
            "model": "RPI3B+",
            "public_ip": "pi1.seduce.fr",
            "public_port": "22001"
        },
        {
            "name": "node-2",
            "id": "071f11f3",
            "port_number": 2,
            "ip": "192.168.1.52",
            "model": "RPI3B+",
            "public_ip": "pi2.seduce.fr",
            "public_port": "22002"
        },
        {
            "name": "node-3",
            "id": "1c2085b9",
            "port_number": 3,
            "ip": "192.168.1.53",
            "model": "RPI3B+",
            "public_ip": "pi3.seduce.fr",
            "public_port": "22003"
        },
        {
            "name": "node-4",
            "id": "4fb9704c",
            "port_number": 4,
            "ip": "192.168.1.54",
            "model": "RPI3B+",
            "public_ip": "pi4.seduce.fr",
            "public_port": "22004"
        },
        {
            "name": "node-5",
            "id": "091a30c2",
            "port_number": 5,
            "ip": "192.168.1.55",
            "model": "RPI3B+",
            "public_ip": "pi5.seduce.fr",
            "public_port": "22005"
        },
        {
            "name": "node-6",
            "id": "ebe8629c",
            "port_number": 6,
            "ip": "192.168.1.56",
            "model": "RPI3B+",
            "public_ip": "pi6.seduce.fr",
            "public_port": "22006"
        },
        {
            "name": "node-7",
            "id": "2ebf44b1",
            "port_number": 7,
            "ip": "192.168.1.57",
            "model": "RPI3B+",
            "public_ip": "pi7.seduce.fr",
            "public_port": "22007"
        },
        {
            "name": "node-8",
            "id": "23ff05a5",
            "port_number": 8,
            "ip": "192.168.1.58",
            "model": "RPI3B+",
            "public_ip": "pi8.seduce.fr",
            "public_port": "22008"
        },
        {
            "name": "node-9",
            "id": "6fa8f83c",
            "port_number": 9,
            "ip": "192.168.1.59",
            "model": "RPI3B+",
            "public_ip": "pi9.seduce.fr",
            "public_port": "22009"
        },
        {
            "name": "node-10",
            "id": "5e8fa6a1",
            "port_number": 10,
            "ip": "192.168.1.60",
            "model": "RPI3B+",
            "public_ip": "pi10.seduce.fr",
            "public_port": "22010"
        },
        {
            "name": "node-11",
            "id": "a67c64be",
            "port_number": 11,
            "ip": "192.168.1.61",
            "model": "RPI3B+",
            "public_ip": "pi11.seduce.fr",
            "public_port": "22011"
        },
        {
            "name": "node-12",
            "id": "1760325b",
            "port_number": 12,
            "ip": "192.168.1.62",
            "model": "RPI3B+",
            "public_ip": "pi12.seduce.fr",
            "public_port": "22012"
        },
        {
            "name": "node-13",
            "id": "dd5cfc3a",
            "port_number": 13,
            "ip": "192.168.1.63",
            "model": "RPI3B+",
            "public_ip": "pi13.seduce.fr",
            "public_port": "22013"
        },
        {
            "name": "node-14",
            "id": "0a1c5d6c",
            "port_number": 14,
            "ip": "192.168.1.64",
            "model": "RPI3B+",
            "public_ip": "pi14.seduce.fr",
            "public_port": "22014"
        },
        {
            "name": "node-15",
            "id": "f495d2ae",
            "port_number": 15,
            "ip": "192.168.1.65",
            "model": "RPI3B+",
            "public_ip": "pi15.seduce.fr",
            "public_port": "22015"
        },
        {
            "name": "node-16",
            "id": "2bae2643",
            "port_number": 16,
            "ip": "192.168.1.66",
            "model": "RPI3B+",
            "public_ip": "pi16.seduce.fr",
            "public_port": "22016"
        },
        {
            "name": "node-17",
            "id": "dc41d65c",
            "port_number": 17,
            "ip": "192.168.1.67",
            "model": "RPI3B+",
            "public_ip": "pi17.seduce.fr",
            "public_port": "22017"
        },
        {
            "name": "node-18",
            "id": "1d5a94f5",
            "port_number": 18,
            "ip": "192.168.1.68",
            "model": "RPI3B+",
            "public_ip": "pi18.seduce.fr",
            "public_port": "22018"
        },
        {
            "name": "node-19",
            "id": "8a759e2c",
            "port_number": 19,
            "ip": "192.168.1.69",
            "model": "RPI3B+",
            "public_ip": "pi19.seduce.fr",
            "public_port": "22019"
        },
        {
            "name": "node-20",
            "id": "057a8080",
            "port_number": 20,
            "ip": "192.168.1.70",
            "model": "RPI3B+",
            "public_ip": "pi20.seduce.fr",
            "public_port": "22020"
        },
        {
            "name": "node-21",
            "id": "d896c498",
            "port_number": 21,
            "ip": "192.168.1.71",
            "model": "RPI3B+",
            "public_ip": "pi21.seduce.fr",
            "public_port": "22021"
        },
        {
            "name": "node-22",
            "id": "5d1c4aa6",
            "port_number": 22,
            "ip": "192.168.1.72",
            "model": "RPI3B+",
            "public_ip": "pi22.seduce.fr",
            "public_port": "22022"
        },
        {
            "name": "node-23",
            "id": "2dd19393",
            "port_number": 23,
            "ip": "192.168.1.73",
            "model": "RPI3B+",
            "public_ip": "pi23.seduce.fr",
            "public_port": "22023"
        },
        {
            "name": "node-24",
            "id": "f91086c5",
            "port_number": 24,
            "ip": "192.168.1.74",
            "model": "RPI3B+",
            "public_ip": "pi24.seduce.fr",
            "public_port": "22024"
        }
    ],
    "switch": {
        "address": "192.168.1.23",
        "username": b"admin",
        "password": b"seduce"
    },
    "environments": [
        {
            "name": "raspbian_cloud9",
            "img_path": "/nfs/raspi1/environments/2019-09-19-Raspbian-lite.img",
            "img_size": 2277507072,
            "sector_start": 106496,
            "ssh_user": "root",
            "shell": "bash",
            "script_test": "echo 'riri\nfifi\nloulou' > /root/picsou.txt",
            "kernel": '4.19.66-v7+',
            "ready": check_cloud9_is_ready
        },
        {
            "name": "raspbian_buster",
            "img_path": "/nfs/raspi1/environments/2020-02-13-raspbian-buster-lite.img",
            "img_size": 1849688064,
            "sector_start": 532480,
            "ssh_user": "root",
            "shell": "bash",
            "script_test": "echo 'riri\nfifi\nloulou' > /root/picsou.txt",
            "kernel": "4.19.97-v8+",
            "ready": check_ssh_is_ready
        },
        {
            "name": "tiny_core",
            "img_path": "/nfs/raspi1/environments/piCore-10.0beta12b.img",
            "img_size": 67186688,
            "sector_start": 92160,
            "ssh_user": "tc",
            "shell": "sh",
            "script_test": "echo 'riri\nfifi\nloulou' > /home/tc/picsou.txt",
            "kernel": "4.19.13-piCore-v7",
            "ready": check_ssh_is_ready
        },
        {
            "name": "raspbian_jupyter",
            "img_path": "/nfs/raspi1/environments/2019-09-20-Raspbian-lite.img",
            "img_size": 2025848832,
            "sector_start": 106496,
            "ssh_user": "root",
            "shell": "bash",
            "script_test": "echo 'riri\nfifi\nloulou' > /root/picsou.txt",
            "kernel": "4.19.66-v7+",
            "ready": check_jupyter_is_ready
        }
    ]
}
