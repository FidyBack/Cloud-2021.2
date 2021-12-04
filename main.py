import boto3, boto3.session

from cred import SENHA, KEY_LOCAL
import deletions as delet
import creations as creat
import check


# Variáveis fixas
UBUNTU_20_OHIO = 'ami-0629230e074c580f2' # Pesquisar um jeito!!
SGPROJECT_OHIO = 'sg-0a6d8e0502f2e3dd9' # Criar um!!
OH_NAME = 'InsanceOH'
KEY_OH = 'project_key_oh'

UBUNTU_20_NV = 'ami-083654bd07b5da81d' # Pesquisar um jeito!!
SGPROJECT_NV = 'sg-01dd7bfe7fa6950c6' # Criar um!!
NV_NAME = 'InsanceNV'
KEY_NV = 'project_key_nv'
IMG_NAME = 'Django-AMI'
LB_NAME = 'ProjLoadBalancer'
TG_NAME = 'ProjTargetGroup'

LT_NAME = 'ProjLauchTemplate'
AS_NAME = 'ProjAutoScaling'


# Script de Ohio
USERDATA_OHIO = f'''#!/bin/bash
apt update
apt install mysql-server -y
mysql -e "CREATE USER 'cloud'@'%' IDENTIFIED BY '{SENHA}';"
mysql -e "GRANT ALL PRIVILEGES ON *.* TO 'cloud'@'%' WITH GRANT OPTION;"
mysql -e "FLUSH PRIVILEGES;"
mysql -e "CREATE DATABASE IF NOT EXISTS tasks;"
sed -i "31 c bind-address = 0.0.0.0" /etc/mysql/mysql.conf.d/mysqld.cnf
service mysql restart'''


# Sessões e Clients
ohio_session = boto3.session.Session(region_name = 'us-east-2')
ec2_resource_oh = ohio_session.resource('ec2')
ec2_client_oh = ohio_session.client('ec2')

nv_session = boto3.session.Session(region_name = 'us-east-1')
ec2_resource_nv = nv_session.resource('ec2')
ec2_client_nv = nv_session.client('ec2')

elb_client = nv_session.client('elbv2')
scaling_client = nv_session.client('autoscaling')
policies_client = nv_session.client('autoscaling-plans')


# Remoção de recursos que serão criados
print("Deletando configurações anteriores...")
delet.instance_termination(ec2_resource_oh, OH_NAME)
delet.instance_termination(ec2_resource_nv, NV_NAME)
delet.image_termination(ec2_resource_nv, IMG_NAME)
delet.load_balancer_termination(elb_client, LB_NAME)
delet.autoscaling_termination(ec2_client_nv, scaling_client, LT_NAME, AS_NAME)
print("Configurações deletadas com sucesso\n")


# Criação das instâncias
print("Criando instâncias...")
ohio_instance = creat.instance_creation(ec2_resource_oh, UBUNTU_20_OHIO, USERDATA_OHIO, KEY_OH, OH_NAME, [SGPROJECT_OHIO])

USERDATA_NV = f'''#!/bin/bash
apt update
apt-get install python3-pip -y
python3 -m pip install Django
apt install mysql-server -y
apt install libmysqlclient-dev -y
pip install mysqlclient
git clone https://github.com/FidyBack/django_teste /home/ubuntu/django_teste
sed -i "82 c\ \t'PASSWORD': '{SENHA}'," /home/ubuntu/django_teste/mysite/settings.py
sed -i "83 c\ \t'HOST': '{ohio_instance.public_dns_name}'," /home/ubuntu/django_teste/mysite/settings.py
./home/ubuntu/django_teste/install.sh
touch /home/ubuntu/complete
reboot'''

nv_instance = creat.instance_creation(ec2_resource_nv, UBUNTU_20_NV, USERDATA_NV, KEY_NV, NV_NAME, [SGPROJECT_NV])


# Cria uma AMI da instância e a destrói
print(f"Aguardando instância {nv_instance.instance_id} ficar disponível...")
nv_instance.wait_until_running()

check.ssh_connection(nv_instance, KEY_LOCAL,)
img = creat.image_creation(nv_instance, ec2_resource_nv, IMG_NAME)


# Criação do LoadBalancer + Autoscaling
print("Criando Load Balancer...")
load_balancer = creat.load_balancer_creation(elb_client, LB_NAME, TG_NAME, [SGPROJECT_NV])
print("Criando Auto Scaling...")
creat.autoscaling_creation(ec2_client_nv, scaling_client, LT_NAME, AS_NAME, img.image_id, KEY_NV, load_balancer[1], [SGPROJECT_NV])
