import configparser
import boto3
from utils import *
import base64
import os
import json
from threading import Thread
import re
import sshtunnel
from sshtunnel import SSHTunnelForwarder
import paramiko

if __name__ == '__main__':
    # Get credentials from the config file :
    path = os.path.dirname(os.getcwd())
    config_object = configparser.ConfigParser()
    with open(path+"/credentials.ini","r") as file_object:
        #Loading of the aws tokens
        config_object.read_file(file_object)
        key_id = config_object.get("resource","aws_access_key_id")
        print(key_id)
        access_key = config_object.get("resource","aws_secret_access_key")
        session_token = config_object.get("resource","aws_session_token")
        ami_id = config_object.get("ami","ami_id")


    print('============================>SETUP Begins')

    #--------------------------------------Creating ec2 resource and client ----------------------------------------
    
    #Create ec2 resource with our credentials:
    ec2_serviceresource = resource_ec2(key_id, access_key, session_token)
    print("============> ec2 resource creation has been made succesfuly!!!!<=================")
    #Create ec2 client with our credentials:
    ec2_serviceclient = client_ec2(key_id, access_key, session_token)
    print("============> ec2 client creation has been made succesfuly!!!!<=================")

    #--------------------------------------Creating a keypair, or check if it already exists-----------------------------------
    
    key_pair_name = create_keypair('labuser', ec2_serviceclient)

    #---------------------------------------------------Get default VPC ID-----------------------------------------------------
    #Get default vpc description : 
    default_vpc = ec2_serviceclient.describe_vpcs(
        Filters=[
            {'Name':'isDefault',
             'Values':['true']},
        ]
    )
    default_vpc_desc = default_vpc.get("Vpcs")
   
    # Get default vpc id : 
    vpc_id = default_vpc_desc[0].get('VpcId')


    #--------------------------------------Try create a security group--------------------------------
    try:
        security_group_id_gatekeeper= create_security_group("All traffic sec_group","lab_gatekeeper",vpc_id,ec2_serviceresource)  
    except :
        print("Exception")
        #Get the standard security group from the default VPC :
        sg_dict = ec2_serviceclient.describe_security_groups(Filters=[
            { 'Name': 'vpc-id',
                'Values': [
                    vpc_id,
                ]
            },
        {'Name': 'group-name',
                'Values': [
                    "lab_gatekeeper",
                ]
            },
        ])
        security_group_id_gatekeeper = (sg_dict.get("SecurityGroups")[0]).get("GroupId")

    try:
        security_group_id_proxy= create_security_group("All traffic sec_group","lab_proxy",vpc_id,ec2_serviceresource)  
    except :
        print("Exception")
        #Get the standard security group from the default VPC :
        sg_dict = ec2_serviceclient.describe_security_groups(Filters=[
            { 'Name': 'vpc-id',
                'Values': [
                    vpc_id,
                ]
            },
        {'Name': 'group-name',
                'Values': [
                    "lab_proxy",
                ]
            },
        ])
        security_group_id_proxy = (sg_dict.get("SecurityGroups")[0]).get("GroupId")
    try:
        security_group_id_nodes= create_security_group("All traffic sec_group","lab_nodes",vpc_id,ec2_serviceresource)  
    except :
        print("Exception")
        #Get the standard security group from the default VPC :
        sg_dict = ec2_serviceclient.describe_security_groups(Filters=[
            { 'Name': 'vpc-id',
                'Values': [
                    vpc_id,
                ]
            },
        {'Name': 'group-name',
                'Values': [
                    "lab_nodes",
                ]
            },
        ])
        security_group_id_nodes = (sg_dict.get("SecurityGroups")[0]).get("GroupId")

    #--------------------------------------Pass flask deployment script into the user_data parameter ------------------------------

    user_data_manager=""
    print(user_data_manager)

    #user_data_workers = str(flask_script_cluster)
    user_data_workers=""

    time.sleep(20)
    #--------------------------------------Create Instances of orchestrator and workers ------------------------------------------------------------

    # Create 4 intances with m4.large as workers:
    Availabilityzones_Cluster1=['us-east-1a','us-east-1b','us-east-1a','us-east-1b','us-east-1a']
    instance_type = "t2.micro"

    print("\n Creating cluster :  ")

    #Creation of 4 instances : to install the MySQL Cluster 
    manager=create_instance_ec2(1,ami_id, instance_type,key_pair_name,ec2_serviceresource,security_group_id_nodes,Availabilityzones_Cluster1,"Manager",user_data_manager)
    print(manager)
    workers_cluster=create_instance_ec2(3,ami_id, instance_type,key_pair_name,ec2_serviceresource,security_group_id_nodes,Availabilityzones_Cluster1,"my-sql-cluster-workers",user_data_manager)
    print(workers_cluster)
    print('\n ........instances launched......\n')
    time.sleep(10)

    #Get DNS private adress
    DNS_private_address={}
    DNS_private_address['Master_cluster']=manager[0][4]
    for i in range (len(workers_cluster)):
        slave_name='Slave_cluster_'+str(i+1)
        DNS_private_address[slave_name]=workers_cluster[i][4]
    print("DNS_private",DNS_private_address)

    #Get DNS public adress
    DNS_public_address={}
    DNS_public_address['Master_cluster']=manager[0][3]
    for i in range (len(workers_cluster)):
        slave_name='Slave_cluster_'+str(i+1)
        DNS_public_address[slave_name]=workers_cluster[i][3]
    print("DNS_public",DNS_public_address)

    #Get ip public adress
    ip_public_address={}
    ip_public_address['Master_cluster']=manager[0][1]
    for i in range (len(workers_cluster)):
        slave_name='Slave_cluster_'+str(i+1)
        ip_public_address[slave_name]=workers_cluster[i][1]
    print("ip_public",ip_public_address)

    #Get private public adress
    ip_private_address={}
    ip_private_address['Master_cluster']=manager[0][2]
    for i in range (len(workers_cluster)):
        slave_name='Slave_cluster_'+str(i+1)
        ip_private_address[slave_name]=workers_cluster[i][2]
    print("ip_private",ip_private_address)


    k = paramiko.RSAKey.from_private_key_file("labuser.pem")
    c=paramiko.SSHClient()
    c.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    print('key defined')
    commands_common=commands_cluster_common_steps()
    print('commands',commands_common)
    time.sleep(10)

    commands_common=commands_cluster_common_steps()
    ssh_connexion_command(c,DNS_public_address['Master_cluster'],k,commands_common)
    #Implement common setup for values on Master and slaves
    for address in DNS_public_address.values():
        commands_common=commands_cluster_common_steps()
        ssh_connexion_command(c,address,k,commands_common)

    #Continuer setup for manager
    command_cluster_deployment=commands_cluster_master(DNS_private_address)
    ssh_connexion_command(c,DNS_public_address['Master_cluster'],k,command_cluster_deployment)

    #Implement commands only on slave
    for i in range(1,4):
        commands_slave=cluster_slave_start(DNS_private_address)
        ssh_connexion_command(c,DNS_public_address[f"Slave_cluster_{i}"],k,commands_slave)

    #Command the cluster manager, start the managament node
    cluster_manager_start=commands_cluster_master_start()   
    ssh_connexion_command(c,DNS_public_address['Master_cluster'],k,cluster_manager_start,False)

    #Update ^proxy script with key before passing it into user data
    with open('flask_proxy.sh', 'r') as f :
        flask_proxy = f.read()
    ud_proxy= str(flask_proxy)

    with open('labuser.pem', 'r') as f :
        key = f.read()

    key_str= str(key)
    new_script=add_key(key_str,ud_proxy)

    #Creation of the proxy
    proxy=create_instance_ec2(1,ami_id, "t2.large",key_pair_name,ec2_serviceresource,security_group_id_proxy,Availabilityzones_Cluster1,"Proxy",new_script)
    proxy_public_ip=proxy[0][1]
    proxy_private_ip=proxy[0][2]

    #Update gatekeeper script with proxy ip_adress before passing it into user data
    with open('flask_gatekeeper.sh', 'r') as f :
        flask_gatekeeper = f.read()

    ud_gatekeeper= str(flask_gatekeeper)
    print("Starting to update gatekeeper_script")
    script_gatekeeper_updated=update_flask_gatekeeper_script(ud_gatekeeper,proxy_public_ip,proxy_private_ip)
    #Creation of the gatekeeper
    gatekeeper=create_instance_ec2(1,ami_id, "t2.large",key_pair_name,ec2_serviceresource,security_group_id_gatekeeper,Availabilityzones_Cluster1,"Gatekeeper",script_gatekeeper_updated)
    gatekeeper_public_ip=gatekeeper[0][1]

    #modify to secure the proxy
    ec2_serviceresource.authorize_security_group_ingress(
        GroupId=security_group_id_proxy,
        IpPermissions=[
        {'FromPort': 80,
            'ToPort': 80,
            'IpProtocol': 'tcp',
            'IpRanges':[{'CidrIp':gatekeeper_public_ip}],
            },
        {'FromPort':3306,
        'ToPort':3306,
        'IpProtocol':'tcp',
        'IpRanges':[{'CidrIp':ip_private_address['Master_cluster']}]
                },]
    )






        
    

    

    




