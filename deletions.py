import time

def instance_termination(resource, instance_name):
    print(f"Deletando Instâncias {instance_name}...")
    inst = resource.instances.filter(
        Filters=[
            {
                'Name': 'tag:Name',
                'Values': [
                    f'{instance_name}',
                ]
            }
        ]
    ).terminate()

    time.sleep(60)

    # instance = resource.Instance(inst)
    # print(inst)


def image_termination(resource, image_name):
    print(f"Deletando Imagens {image_name}...")
    for image in resource.images.filter(
        Filters=[
            {'Name': 'name', 'Values': [f'{image_name}']}
        ]
    ):
        if image.name == image_name:
            image.deregister()


def load_balancer_termination(client, lb_name):
    paginator_lb = client.get_paginator('describe_load_balancers')
    paginator_ls = client.get_paginator('describe_listeners')
    paginator_tg = client.get_paginator('describe_target_groups')

    try:
        for lb in paginator_lb.paginate(Names=[lb_name]):
            lb_ARN = lb['LoadBalancers'][0]['LoadBalancerArn']
    except:
        print(f"Inexistente: Load Balancer {lb_name}")
        return None

    for ls in paginator_ls.paginate(LoadBalancerArn=lb_ARN):
        ls_ARN = ls['Listeners'][0]['ListenerArn']

    for tg in paginator_tg.paginate(LoadBalancerArn=lb_ARN):
        tg_ARN = tg['TargetGroups'][0]['TargetGroupArn']

    print(f"Deletando Listener {ls_ARN}...")
    client.delete_listener(ListenerArn=ls_ARN)
    print(f"Deletando Target Group {tg_ARN}...")
    client.delete_target_group(TargetGroupArn=tg_ARN)
    print(f"Deletando Load Balancer {lb_ARN}...")
    client.delete_load_balancer(LoadBalancerArn=lb_ARN)
    

def autoscaling_termination(client, as_client, lt_name, as_name):
    try:
        as_client.delete_auto_scaling_group(AutoScalingGroupName=as_name, ForceDelete=True)
        auto_scaling = as_client.describe_auto_scaling_groups(AutoScalingGroupNames=[as_name])
        print(f"Deletando Auto Scaling {as_name}...")

        while auto_scaling['AutoScalingGroups'][0]['Status'] == 'Delete in progress':
            auto_scaling = as_client.describe_auto_scaling_groups(AutoScalingGroupNames=[as_name])
            time.sleep(10)
    except:
        print(f"Inexistente: Auto Scaling {as_name}")


    try:
        client.delete_launch_template(LaunchTemplateName=lt_name)
        print(f"Deletando Lauch Template {lt_name}...")
    except:
        print(f"Inexistente: Lauch Template {lt_name}")


def key_termination(client, key_name):
    
    print(f"Deletando key {key_name}")
    client.delete_key_pair(KeyName=key_name)


def security_group_termination(client, sg_name):
    try:
        client.delete_security_group(GroupName=sg_name)
        print(f"Deletando security group {sg_name}")
    except Exception as e:
        print(e)
        print(f"Inexistente: Security Group {sg_name}")