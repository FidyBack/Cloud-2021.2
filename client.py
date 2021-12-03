import requests
from sys import argv
from datetime import datetime


url = "http://projloadbalancer-290465352.us-east-1.elb.amazonaws.com/polls/" 

COMMANDS = ["get_all"]

if argv[1] == COMMANDS[0]:
    new_url = url + "all_tasks/"
    print(f"GET {new_url}")
    response = requests.get(new_url )
    print(response.text)