import configparser
import boto3
import time
import requests
import re 
import json

#Function to create a service resource for ec2: 
def resource_ec2(aws_access_key_id, aws_secret_access_key, aws_session_token):
    ec2_serviceresource =  boto3.resource('ec2',
                       'us-east-1',
                       aws_access_key_id= aws_access_key_id,
                       aws_secret_access_key=aws_secret_access_key ,
                      aws_session_token= aws_session_token) 
    
    return(ec2_serviceresource)

#Function to create a service client for ec2
def client_ec2(aws_access_key_id, aws_secret_access_key, aws_session_token):
    ec2_serviceclient =  boto3.client('ec2',
                       'us-east-1',
                       aws_access_key_id= aws_access_key_id,
                       aws_secret_access_key=aws_secret_access_key ,
                      aws_session_token= aws_session_token) 
   
    
    return(ec2_serviceclient)

#Function to create and check a KeyPair : 
def create_keypair(key_pair_name, client):
    try:
        keypair = client.create_key_pair(KeyName=key_pair_name)
        print(keypair['KeyMaterial'])
        with open('labuser.pem', 'w') as f:
            f.write(keypair['KeyMaterial'])

        return(key_pair_name)

    except:
        print("\n\n============> Warning :  Keypair already created !!!!!!!<==================\n\n")
        return(key_pair_name)


#---------------------------------------------To re check----------------------------------------------
#Function to create a new vpc (Maybe no need for this, just use default vpc)'
def create_vpc(CidrBlock,resource):
   VPC_Id=resource.create_vpc(CidrBlock=CidrBlock).id
   return VPC_Id

#Function to create security group 
def create_security_group(Description,Groupe_name,vpc_id,resource):
    Security_group_ID=resource.create_security_group(
        Description=Description,
        GroupName=Groupe_name,
        VpcId=vpc_id).id
    
    Security_group=resource.SecurityGroup(Security_group_ID)
    
    #Add an inbounded allowing inbounded traffics of tcp protocol, and ports 22,80 and all Ipranges.
    Security_group.authorize_ingress(
         IpPermissions=[
            {'FromPort':22,
             'ToPort':22,
             'IpProtocol':'tcp',
             'IpRanges':[{'CidrIp':'0.0.0.0/0'}]
            },
            {'FromPort':80,
             'ToPort':80,
             'IpProtocol':'tcp',
             'IpRanges':[{'CidrIp':'0.0.0.0/0'}]
            },
            ]
    )
    return Security_group_ID

#Function to create security for proxy
def create_security_group_proxy(Description,Groupe_name,vpc_id,resource):
    Security_group_ID=resource.create_security_group(
        Description=Description,
        GroupName=Groupe_name,
        VpcId=vpc_id).id
    
    Security_group=resource.SecurityGroup(Security_group_ID)
    
    #Add an inbounded allowing inbounded traffics of tcp protocol, and ports 22,80 only from the gatekeeper
    Security_group.authorize_ingress(
         IpPermissions=[
            {'FromPort':22,
                'ToPort':22,
                'IpProtocol':'tcp',
                'IpRanges':[{'CidrIp':'0.0.0.0/0'}]
                },
                {
                'FromPort': -1,
                'ToPort': -1,
                'IpProtocol': 'ICMP',
                'IpRanges': [
                {
                'CidrIp': '0.0.0.0/0'},
                        ]
                    }
            ]
    )
    return Security_group_ID

#Function to create security for nodes
def create_security_group_nodes(Description,Groupe_name,vpc_id,resource):
    Security_group_ID=resource.create_security_group(
        Description=Description,
        GroupName=Groupe_name,
        VpcId=vpc_id).id
    
    Security_group=resource.SecurityGroup(Security_group_ID)
    
    #Add an inbounded allowing inbounded traffics of tcp protocol, and ports 22,80 only from the gatekeeper
    Security_group.authorize_ingress(
         IpPermissions=[
                {'FromPort':3306,
                'ToPort':3306,
                'IpProtocol':'tcp',
                'IpRanges':[{'CidrIp':'0.0.0.0/0'}]
                },
                {
                'FromPort': -1,
                'ToPort': -1,
                'IpProtocol': 'ICMP',
                'IpRanges': [
                {
                'CidrIp': '0.0.0.0/0'},
                        ]
                    },
                    {'FromPort':22,
             'ToPort':22,
             'IpProtocol':'tcp',
             'IpRanges':[{'CidrIp':'0.0.0.0/0'}]
            },
            {'FromPort':1186,
             'ToPort':1186,
             'IpProtocol':'tcp',
             'IpRanges':[{'CidrIp':'0.0.0.0/0'}]
            },
            ]
    )
    return Security_group_ID
#------------------------------------------------End----------------------------------------------------


#Function to create ec2 instances :  The function returns a list containing the [id of instance,public_ip_address]

def create_instance_ec2(num_instances,ami_id,
    instance_type,key_pair_name,ec2_serviceresource,security_group_id,Availabilityzons,instance_function,user_data):
    instances=[]
    for i in range(num_instances):
        instance=ec2_serviceresource.create_instances(
            ImageId=ami_id,
            InstanceType=instance_type,
            KeyName=key_pair_name,
            MinCount=1,
            MaxCount=1,
            Placement={'AvailabilityZone':Availabilityzons[i]},
            SecurityGroupIds=[security_group_id] if security_group_id else [],
            UserData=user_data,
            TagSpecifications=[
                    {
                        'ResourceType': 'instance',
                        'Tags': [
                            {
                                'Key': 'Name',
                                'Value': 'lab3-'+str(instance_function)+"-"+str(i)
                            },
                        ]
                    },
                ]
        )

        #Wait until the instance is running to get its public_ip adress
        instance[0].wait_until_running()
        instance[0].reload()
        #Get the public ip address of the instance and add it in the return
        public_ip = instance[0].public_ip_address
        private_ip=instance[0].private_ip_address
        public_dns_name=instance[0].public_dns_name
        private_dns_name=instance[0].private_dns_name

        instances.append([instance[0].id,public_ip,private_ip,public_dns_name,private_dns_name])
        print ('Instance: '+str(instance_function)+str(i+1),' having the Id: ',instance[0].id,'and having the ip',public_ip,' in Availability Zone: ', Availabilityzons[i], 'is created')
    return instances

#function that include the command to send to the machine to implement the command standalone
def commands_standalone():
    list_of_commands_standalone = [
        "sudo apt-get -y update",
        'sudo apt-get install mysql-server -y',
        'sudo apt install sysbench -y',
        'sudo apt install wget',
        'sudo apt-get install unzip',
        'sudo mkdir sakila',
        'cd sakila',
        'sudo wget https://downloads.mysql.com/docs/sakila-db.zip',
        'sudo unzip sakila-db.zip',
        """sudo mysql -e "ALTER USER 'root'@'localhost' IDENTIFIED WITH mysql_native_password BY 'password'" """,
        'sudo mysql -u root --password=password -e "SOURCE /home/ubuntu/sakila-db/sakila-schema.sql"',
        'sudo mysql -u root --password=password -e "SOURCE /home/ubuntu/sakila-db/sakila-data.sql"',

        'sudo mysql -u root --password=password -e "USE sakila"', 

        'sudo sysbench oltp_read_write --table-size=100000 --mysql-db=sakila --mysql-user=root --mysql-password=password prepare',
        'sudo sysbench oltp_read_write --table-size=100000 --threads=6 --max-time=60 --max-requests=0 --mysql-db=sakila --mysql-user=root --mysql-password=password  run > /home/ubuntu/results.txt',
        'sudo sysbench oltp_read_write --mysql-db=sakila --mysql-user=root --mysql-password=password cleanup'
        ]
    
    return list_of_commands_standalone

def commands_cluster_common_steps():
    commands=[
        'sudo apt-get -y update',
        'sudo apt-get -y install libncurses5',
        'sudo apt install sysbench -y',
        'sudo mkdir -p /opt/mysqlcluster/home',
        'sudo chmod -R 777 /opt/mysqlcluster',
        'sudo wget http://dev.mysql.com/get/Downloads/MySQL-Cluster-7.2/mysql-cluster-gpl-7.2.1-linux2.6-x86_64.tar.gz -P /opt/mysqlcluster/home',
        'sudo tar xvf mysql-cluster-gpl-7.2.1-linux2.6-x86_64.tar.gz -C /opt/mysqlcluster/home/',
        'sudo ln -s mysql-cluster-gpl-7.2.1-linux2.6-x86_64 /opt/mysqlcluster/home/mysqlc',
        'sudo rm /opt/mysqlcluster/home/mysql-cluster-gpl-7.2.1-linux2.6-x86_64.tar.gz',
        'sudo chmod -R 777 /etc/profile.d',
        'sudo echo "export MYSQLC_HOME=/opt/mysqlcluster/home/mysqlc" > /etc/profile.d/mysqlc.sh',
        'sudo echo "export PATH=$MYSQLC_HOME/bin:$PATH" >> /etc/profile.d/mysqlc.sh',
        'source /etc/profile.d/mysqlc.sh',
    ]
    return commands
def commands_cluster_master(dns_private_adress):
    commands=[
        'sudo mkdir -p /opt/mysqlcluster/deploy',
        'sudo mkdir /opt/mysqlcluster/deploy/conf',
        'sudo  mkdir /opt/mysqlcluster/deploy/mysqld_data',
        'sudo mkdir /opt/mysqlcluster/deploy/ndb_data',
        'sudo chmod -R 777 /opt/mysqlcluster/deploy/conf',
        ''' sudo echo "[mysqld]
ndbcluster
datadir=/opt/mysqlcluster/deploy/mysqld_data
basedir=/opt/mysqlcluster/home/mysqlc
port=3306" > /opt/mysqlcluster/deploy/conf/my.cnf''',
    f'''echo "[ndb_mgmd]
    hostname={dns_private_adress["Master_cluster"]}
    datadir=/opt/mysqlcluster/deploy/ndb_data
    nodeid=1

    [ndbd default]
    noofreplicas=3
    datadir=/opt/mysqlcluster/deploy/ndb_data

    [ndbd]
    hostname={dns_private_adress["Slave_cluster_1"]}
    nodeid=3

    [ndbd]
    hostname={dns_private_adress["Slave_cluster_2"]}
    nodeid=4

    [ndbd]
    hostname={dns_private_adress["Slave_cluster_3"]}
    nodeid=5

    [mysqld]
    nodeid=50" | sudo tee /opt/mysqlcluster/deploy/conf/config.ini''',

    'sudo /opt/mysqlcluster/home/mysqlc/scripts/mysql_install_db --basedir=/opt/mysqlcluster/home/mysqlc --no-defaults --datadir=/opt/mysqlcluster/deploy/mysqld_data',
    'sudo /opt/mysqlcluster/home/mysqlc/bin/ndb_mgmd -f /opt/mysqlcluster/deploy/conf/config.ini --initial --configdir=/opt/mysqlcluster/deploy/conf/'
    ]
    return commands

def cluster_slave_start(dns_private_adress):
    commands=[
    'sudo mkdir -p /opt/mysqlcluster/deploy/ndb_data',
    f'sudo /opt/mysqlcluster/home/mysqlc/bin/ndbd -c {dns_private_adress["Master_cluster"]}:1186'
    ]
    return commands

def commands_cluster_master_start():
    commands=[
    'sudo /opt/mysqlcluster/home/mysqlc/bin/mysqld --defaults-file=/opt/mysqlcluster/deploy/conf/my.cnf --user=root &'
    ]
    return commands

def commands_cluster_master_start_sakila():
    #https://stansantiago.wordpress.com/2012/01/04/installing-mysql-cluster-on-ec2/
    commands=[
    '''sudo /opt/mysqlcluster/home/mysqlc/bin/mysql -e "CREATE USER 'myapp'@'%' IDENTIFIED BY 'testpwd';GRANT ALL PRIVILEGES ON * . * TO 'myapp'@'%' IDENTIFIED BY 'password';"''',
    '''sudo /opt/mysqlcluster/home/mysqlc/bin/mysql -e "USE mysql; UPDATE user SET plugin='mysql_native_password' WHERE User='root'; FLUSH PRIVILEGES;SET PASSWORD FOR 'root'@'localhost' = PASSWORD('password');"''',
    'wget https://downloads.mysql.com/docs/sakila-db.tar.gz',
    'tar -xvf sakila-db.tar.gz',
    '''sudo /opt/mysqlcluster/home/mysqlc/bin/mysql -h 127.0.0.1 -e "SOURCE sakila-db/sakila-schema.sql;'-u root -p password''',
    '''sudo /opt/mysqlcluster/home/mysqlc/bin/mysql -h 127.0.0.1 -e "SOURCE sakila-db/sakila-data.sql;'-u root -p password''',
    '''sudo /opt/mysqlcluster/home/mysqlc/bin/mysql -h 127.0.0.1 -e "USE sakila;'-u root -p password''',
    ]
    return commands

def command_benchmark():
    #https://www.jamescoyle.net/how-to/1131-benchmark-mysql-server-performance-with-sysbench
    commands=[
    'sudo sysbench oltp_read_write --table-size=1000000 --threads=6 --mysql-db=sakila --mysql-user=root --db-driver=mysql --mysql-host=127.0.0.1 --mysql-password=password prepare'
    'sudo sysbench oltp_read_write --table-size=1000000 --threads=6  --mysql-db=sakila --mysql-user=root --db-driver=mysql --mysql-host=127.0.0.1 --mysql-password=password run > /home/ubuntu/results_cluster.txt'
    'sudo sysbench oltp_read_write --table-size=1000000 --threads=6  --mysql-db=sakila --mysql-user=root --db-driver=mysql --mysql-host=127.0.0.1 --mysql-password=password cleanup '
    ]
    return commands

def ssh_connexion_command(para_client,dns_public_adress,para_key,commands,print_std=True,ssh_key=""):
    print('Try to connect to',dns_public_adress)
    para_client.connect(hostname=dns_public_adress,username='ubuntu',pkey=para_key)
    print('Connected to the instance')
    for command in commands:
        print("Executing {}".format( command ))
        stdin , stdout, stderr = para_client.exec_command(command)

        while print_std:
            print(stdout.readline())
            if stdout.channel.exit_status_ready():
                break

    time.sleep(10)
    return None


def update_flask_proxy_script(ud_script,ip_private_address,ip_public_address):
    
    #Replace the private_ip_address in the proxy file 
    pattern_private = re.compile(r'private_ip_address_nodes=\{.*?\}', re.DOTALL)
    result_private= re.search(pattern_private, ud_script)
    old_ip_private = result_private.group(1)
    updated_script_private = ud_script.replace(old_ip_private, ip_private_address)

    #Replace the public_ip_address in the proxy file 
    pattern_public = re.compile(r'public_ip_address_nodes=\{.*?\}', re.DOTALL)
    result_public= re.search(pattern_public, ud_script)
    old_ip_public = result_public.group(1)
    updated_script_public = updated_script_private.replace(old_ip_public, ip_public_address)

    # Rewrite the flask proxy_app with 
    with open('flask_proxy.sh', 'w') as file:
        file.write(updated_script_public)
    print("\nScript Flask proxy updated with proxy ips.")
    return updated_script_public


def update_flask_gatekeeper_script(ud_script,proxy_public_address,proxy_private_address):

    #Replace the old public ip
    pattern_public= re.compile(r'public_ip_address_proxy=(\'.*?\'|\".*?\")', re.DOTALL)
    result_public= re.search(pattern_public, ud_script)
    old_ip_public = result_public.group(1)
    updated_script_public = ud_script.replace(old_ip_public, proxy_public_address)

    # replace old ip_address
    pattern_private= re.compile(r'private_ip_address_proxy=(\'.*?\'|\".*?\")', re.DOTALL)
    result_private= re.search(pattern_private, updated_script_public)
    old_ip_private = result_private.group(1)
    updated_script_private = updated_script_public.replace(old_ip_private, proxy_private_address)

    # Rewrite the flask gatekeeper_app
    with open('flask_gatekeeper.sh', 'w') as file:
        file.write(updated_script_private)
    print("\nScript Flask Gatekeeper updated with proxy ips.")
    return updated_script_private

#Function to replace the key.pem by the right one in the script
def add_key(key,ud_script):
    pattern = re.compile(r'("key_to_modify")')
    resultat = re.search(pattern, ud_script)
    contenu = resultat.group(1)
    new_key= key
    ud_script_modified= re.sub(pattern, f'"{new_key}"',ud_script)
    with open('flask_proxy.sh', 'w') as file:
        file.write(ud_script_modified)
    return ud_script_modified
