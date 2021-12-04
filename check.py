import paramiko, time

def ssh_connection(instance, local_key):
    hostname = instance.public_dns_name
    port = 22
    username = "ubuntu"
    key_filename = local_key
    command = "ls"

    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())

    print(f"Aguardando instância {instance.instance_id} rodar o script...")
    lines = []
    i = 0
    while 'complete\n' not in lines:
        try:
            ssh.connect(hostname, port=port, username=username, pkey=key_filename)
            stdin, stdout, stderr = ssh.exec_command(command)
            lines = stdout.readlines()
            print(lines)
            # if lines[0] == 'django_teste\n' and i == 0:
            #     print('\tDjango_teste clonado com sucesso')
            #     i+=1
            # elif lines[0] == 'complete\n':
            #     print('\tScript concluído\n')
            time.sleep(10)
        except:
            pass