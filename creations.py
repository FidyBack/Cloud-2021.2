import time


def instance_creation(resource, imgId, UserData, key, instance_name, sgList = []):
    new_instance = resource.create_instances(
        ImageId=imgId,
        UserData=UserData,
        SecurityGroupIds=sgList,
        InstanceType='t2.micro',
        KeyName=key,
        MinCount=1, MaxCount=1,
        TagSpecifications=[{
            'ResourceType': 'instance',
            'Tags': [{
                'Key': 'Name',
                'Value': instance_name
            }]
        }]
    )

    instance = resource.Instance(new_instance[0].id)
    instance.wait_until_exists()

    while instance.public_dns_name == '':
        try:
            instance.load()
        except:
            time.sleep(0.5)

    print(f"Instância em Ohio criada:\n\tID: {instance.id}\n\tDNS Público: {instance.public_dns_name}\n")

    return instance


def image_creation(instance, resource, img_name):
    new_image = instance.create_image(Name=img_name)
    image = resource.Image(new_image.image_id)

    print("Criando Imagem...")
    while image.state== 'pending':
        time.sleep(2)
        image.load()

    instance.terminate()

    print(f"\tImagem '{image.image_id}' foi criada da Instância '{instance.instance_id}'\n\tA Instância '{instance.instance_id}' foi terminada ")

    return image


def load_balancer_creation(client, lb_name, tg_name, sgList = []):
    load_balancer = client.create_load_balancer(
        Name=lb_name,
        Subnets=[
            'subnet-759aae3f',
            'subnet-125f3e4e',
            'subnet-d787e3b0',
            'subnet-62afcc4c',
            'subnet-1957ff27',
            'subnet-4e8ad441',
        ],
        SecurityGroups=sgList,
        Type='application'
    )
    lb_ARN = load_balancer['LoadBalancers'][0]['LoadBalancerArn']

    target_groups = client.create_target_group(
        Name=tg_name,
        Protocol='HTTP',
        Port=8080,
        VpcId='vpc-3cca7a46',
        HealthCheckProtocol='HTTP',
        HealthCheckPath='/admin/login/?next=/admin'
    )
    tg_ARN = target_groups['TargetGroups'][0]['TargetGroupArn']

    listener = client.create_listener(
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

    lb_waiter = client.get_waiter('load_balancer_available')
    lb_waiter.wait(LoadBalancerArns=[lb_ARN])

    print(f'\tLoad Balancer: {lb_ARN}\n\tTarget Group: {tg_ARN}\n\tListener: {ln_ARN}')

    return lb_ARN, tg_ARN, ln_ARN


def autoscaling_creation(client, as_client, lt_name, as_name, image_id, key, tg_arm, sgList = []):
    scaling_template = client.create_launch_template(
        LaunchTemplateName=lt_name,
        LaunchTemplateData={
            'ImageId': image_id,
            'InstanceType': 't2.micro',
            'KeyName': key,
            'SecurityGroupIds': sgList
        }
    )

    template_id = scaling_template['LaunchTemplate']['LaunchTemplateId']

    auto_scaling = as_client.create_auto_scaling_group(
        AutoScalingGroupName=as_name,
        LaunchTemplate={
            'LaunchTemplateId': template_id
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
            tg_arm
        ],
        MinSize=1,
        MaxSize=100
    )

    auto_scaling_desc = as_client.describe_auto_scaling_groups(AutoScalingGroupNames=[as_name])

    print(f"\tLaunch Template: {template_id}\n\tAuto Scaling: {auto_scaling_desc['AutoScalingGroups'][0]['AutoScalingGroupARN']}")

    return auto_scaling


def key_creation(client, key_name):
    print(f"Criando key {key_name}")
    return client.create_key_pair(KeyName=key_name)


def security_group_creation(client, sg_name, description):
    print(f"Criando security group {sg_name}")
    return client.create_security_group(
        Description=description,
        GroupName=sg_name
    )