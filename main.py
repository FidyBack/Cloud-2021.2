#=======================================================================================================================================#
# A criação do User Data foi feita a partir dos seguintes tutoriais:
# https://towardsdatascience.com/running-mysql-databases-on-aws-ec2-a-tutorial-for-beginners-4301faa0c247
# https://stackoverflow.com/questions/33470753/create-mysql-database-and-user-in-bash-script
# https://stackoverflow.com/questions/4606919/in-python-try-until-no-error
# https://stackoverflow.com/questions/4870253/sed-replace-single-double-quoted-text
# https://stackoverflow.com/questions/19101243/error-1130-hy000-host-is-not-allowed-to-connect-to-this-mysql-server
# https://stackoverflow.com/questions/50177216/how-to-grant-all-privileges-to-root-user-in-mysql-8-0
# https://serverfault.com/questions/415334/django-syncdb-cant-connect-to-mysql-on-seperate-ec2-instance
# https://askubuntu.com/questions/583415/import-error-no-module-named-mysqldb/1048285#1048285
# https://stackoverflow.com/questions/40759565/django-unable-to-connect-to-mysql-server
# https://stackoverflow.com/questions/19054081/ec2-waiting-until-a-new-instance-is-in-running-state/38925075
# https://stackoverflow.com/questions/26175050/python-boto-ec2-how-do-i-wait-till-an-image-is-created-or-failed
# https://www.kite.com/python/answers/how-to-ssh-using-paramiko-in-python
# https://stackoverflow.com/questions/52461244/how-to-create-and-attach-a-elb-properly-in-boto3
#=======================================================================================================================================#
import boto3, boto3.session
import time
import paramiko

from cred import SENHA, KEY_LOCAL


#===========================#
#           Ohio            #
#===========================#
# Configurações iniciais
UBUNTU_20_OHIO = 'ami-0629230e074c580f2'
SGPROJECT_OHIO = 'sg-0a6d8e0502f2e3dd9'

USERDATA_OHIO = f'''#!/bin/bash
apt update
apt install mysql-server -y
mysql -e "CREATE USER 'cloud'@'%' IDENTIFIED BY '{SENHA}';"
mysql -e "GRANT ALL PRIVILEGES ON *.* TO 'cloud'@'%' WITH GRANT OPTION;"
mysql -e "FLUSH PRIVILEGES;"
mysql -e "CREATE DATABASE IF NOT EXISTS tasks;"
sed -i "31 c bind-address = 0.0.0.0" /etc/mysql/mysql.conf.d/mysqld.cnf
service mysql restart
'''

# Inicialização da seção, recursos e clientes
ohio_session = boto3.session.Session(region_name = 'us-east-2')
ec2_resourse_oh = ohio_session.resource('ec2')
ec2_client_oh = ohio_session.client('ec2')

# Criação das instâncias
new_ohio_instance = ec2_resourse_oh.create_instances(
    ImageId=UBUNTU_20_OHIO, 
    InstanceType='t2.micro',
    UserData=USERDATA_OHIO,
    KeyName='project_key_oh',
    MinCount=1, MaxCount=1,
    SecurityGroupIds=[SGPROJECT_OHIO],
    TagSpecifications=[{
        'ResourceType': 'instance',
        'Tags': [{
            'Key': 'Name',
            'Value': 'InsanceOH'
        }]
    }]
)

ohio_id = new_ohio_instance[0].id
response_oh = ec2_client_oh.describe_instances(InstanceIds = [ohio_id])

public_dns_oh = None
while public_dns_oh is None:
    try:
        public_dns_oh = response_oh['Reservations'][0]['Instances'][0]['NetworkInterfaces'][0]['Association']['PublicDnsName']
    except:
        time.sleep(0.01)

print(f"Instância em Ohio criada:\nID: {ohio_id}\nDNS Público: {public_dns_oh}\n")


#===================================#
#           North Virginia          #
#===================================#
# Configurações iniciais
UBUNTU_20_NV = 'ami-083654bd07b5da81d'
SGPROJECT_NV = 'sg-01dd7bfe7fa6950c6'

USERDATA_NV = f'''#!/bin/bash
apt update
apt-get install python3-pip -y
python3 -m pip install Django
apt install mysql-server -y
apt install libmysqlclient-dev -y
pip install mysqlclient
git clone https://github.com/FidyBack/django_teste /home/ubuntu/django_teste
sed -i "82 c\ \t'PASSWORD': '{SENHA}'," /home/ubuntu/django_teste/mysite/settings.py
sed -i "83 c\ \t'HOST': '{public_dns_oh}'," /home/ubuntu/django_teste/mysite/settings.py
./home/ubuntu/django_teste/install.sh
touch /home/ubuntu/complete
reboot
'''

#Inicialização da seção, recursos e clientes
nv_session = boto3.session.Session(region_name = 'us-east-1')
ec2_resourse_nv = nv_session.resource('ec2')
ec2_client_nv = nv_session.client('ec2')


# Criação das instâncias
new_nv_instance = ec2_resourse_nv.create_instances(
    ImageId=UBUNTU_20_NV, 
    InstanceType='t2.micro',
    UserData=USERDATA_NV,
    KeyName='project_key_nv',
    MinCount=1, MaxCount=1,
    SecurityGroupIds=[SGPROJECT_NV],
    TagSpecifications=[{
        'ResourceType': 'instance',
        'Tags': [{
            'Key': 'Name',
            'Value': 'InsanceNV'
        }]
    }]
)

nv_id = new_nv_instance[0].id

response_nv = ec2_client_nv.describe_instances(InstanceIds = [nv_id])

public_dns_nv = None
while public_dns_nv is None:
    try:
        public_dns_nv = response_nv['Reservations'][0]['Instances'][0]['NetworkInterfaces'][0]['Association']['PublicDnsName']
    except:
        time.sleep(0.01)

print(f"Instância em North Virginia criada:\nID: {nv_id}\nDNS Público: {public_dns_nv}\n")


# Cria uma AMI da instância e a destrói
instance_nv = ec2_resourse_nv.Instance(nv_id)

instance_nv.wait_until_running()

hostname = public_dns_nv
port = 22
username = "ubuntu"
key_filename = KEY_LOCAL
command = "ls"


ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())


lines = []
while 'complete\n' not in lines:
    try:
        ssh.connect(hostname, port=port, username=username, key_filename=key_filename)
        stdin, stdout, stderr = ssh.exec_command(command)
        lines = stdout.readlines()
        print(lines)
        time.sleep(10)
    except:
        pass

image_creator = ec2_client_nv.create_image(InstanceId=nv_id, Name="Django-AMI")
image_id = image_creator['ImageId']
image = ec2_resourse_nv.Image(image_id)

print("Criando Imagem...")
while image.state== 'pending':
    time.sleep(2)
    image.load()

instance_nv.terminate()

print(
    f'''Imagem '{image_id}' foi criada da Instância '{nv_id}'
A Instância '{nv_id}' foi terminada '''
)


#Criação do LoadBalancer + AutoScaling
elb_client = nv_session.client('elbv2')
scaling_client = nv_session.client('autoscaling')
policies_client = nv_session.client('autoscaling-plans')

load_balancer = elb_client.create_load_balancer(
    Name='ProjLoadBalancer',
    Subnets=[
        'subnet-759aae3f',
        'subnet-125f3e4e',
        'subnet-d787e3b0',
        'subnet-62afcc4c',
        'subnet-1957ff27',
        'subnet-4e8ad441',
    ],
    SecurityGroups=[SGPROJECT_NV],
    Type='application'
)

lb_ARN = load_balancer['LoadBalancers'][0]['LoadBalancerArn']

target_groups = elb_client.create_target_group(
    Name='ProjTargetGroup',
    Protocol='HTTP',
    Port=8080,
    VpcId='vpc-3cca7a46',
    HealthCheckProtocol='HTTP',
    HealthCheckPath='/admin/login/?next=/admin'
)

tg_ARN = target_groups['TargetGroups'][0]['TargetGroupArn']

listener = elb_client.create_listener(
    LoadBalancerArn=lb_ARN,
    Protocol='HTTP',
    Port=80,
    DefaultActions=[
        {
            'Type': 'forward',
            'TargetGroupArn': tg_ARN,
        }
    ]
)

ln_ARN = listener['Listeners'][0]['ListenerArn']

print("Criando Load Balancer...")
lb_waiter = elb_client.get_waiter('load_balancer_available')
lb_waiter.wait(LoadBalancerArns=[lb_ARN])

print(f'Load Balancer: {lb_ARN}\nTarget Group: {tg_ARN}\nListener: {ln_ARN}')


scaling_template = ec2_client_nv.create_launch_template(
    LaunchTemplateName='ProjLauchTemplate',
    LaunchTemplateData={
        'ImageId': ami, # MUDAR!!!
        'InstanceType': 't2.micro',
        'KeyName': 'project_key_nv',
        'SecurityGroupIds': [SGPROJECT_NV]
    }
)

response_AS = scaling_client.create_auto_scaling_group(
    AutoScalingGroupName='ProjAutoScaling',
    LaunchTemplate={
        'LaunchTemplateId': 'lt-0ffc4734f0e123243' # MUDAR!!!
    },
    AvailabilityZones=[
        'us-east-1a',
        'us-east-1b',
        'us-east-1c',
        'us-east-1d',
        'us-east-1e',
        'us-east-1f',
    ],
    TargetGroupARNs=[
       'arn:aws:elasticloadbalancing:us-east-1:690246486040:targetgroup/Teste2/ba45af2cbc84d752'  # Mudar!!!
    ],
    MinSize=1,
    MaxSize=100
)

# response_policies = policies_client.create_scaling_plan(
#     ScalingPlanName='ProjTracker',
#     ApplicationSource='',
#     ScalingInstructions=''
# )
