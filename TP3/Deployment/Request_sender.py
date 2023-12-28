import boto3
import requests
import multiprocessing
import configparser
import os
from datetime import date
import time

#Function to send a POST request to the gatekeeper
 

def send_request_to_gatekeeper(ip,port,json_data):
    try:
        url="http://{}:{}/{}".format(ip, port,'query')
        # Sending the request
        response=requests.post(url,json=json_data, headers = {'Content-Type': 'application/json'})
        ls = response.json()
        print(ls)
    except Exception as e:
        print('Exception returned is',e)

if __name__ == '__main__':
    # Get credentials from the config file :
    path = os.path.dirname(os.getcwd())
    path=path+"\TP2"
    config_object = configparser.ConfigParser()
    with open(path+"/credentials.ini","r") as file_object:
        config_object.read_file(file_object)
        key_id = config_object.get("resource","aws_access_key_id")
        access_key = config_object.get("resource","aws_secret_access_key")
        session_token = config_object.get("resource","aws_session_token")

    # Create an ec2 client 
    ec2_serviceclient = boto3.client('ec2',
                        'us-east-1',
                        aws_access_key_id= key_id,
                        aws_secret_access_key=access_key ,
                        aws_session_token= session_token) 
    
    # Get description of the gatekeeper 
    response_gatekeeper = ec2_serviceclient.describe_instances(Filters=[{'Name': 'tag:Name', 'Values': ['Gatekeeper']}])

    #Get the ip address of the gatekeeper
    ip_address_gatekeeper=response_gatekeeper["Reservations"][0]["Instances"][0]["PublicIpAddress"]
    
    #Definate orchestrator port, data to send to it, and number of requests 
    gatekeeper_port=80
    data_direct_hit={
        'type':'direct',
        'data_sql':'''SELECT * FROM actor ORDER BY last_name;'''
    }
    data_random={
        'type':'random',
        'data_sql':'''SELECT * FROM actor ORDER BY last_name;'''
    }
    data_customized={
        'type':'customized',
        'data_sql':'''SELECT * FROM actor ORDER BY last_name;'''
    }

    #Send requests to the gatekeeper
    print('Starting sending multiple requests to gatekeeper') 
    print('Sending request via direct hit')
    send_request_to_gatekeeper(ip_address_gatekeeper,gatekeeper_port,data_direct_hit)
    time.sleep(5)
    print('Sending request via random')
    send_request_to_gatekeeper(ip_address_gatekeeper,gatekeeper_port,data_random)
    time.sleep(5)
    print('Sending request via customized')
    send_request_to_gatekeeper(ip_address_gatekeeper,gatekeeper_port,data_customized)
    time.sleep(5)
    print('Finished sending requests')
    




