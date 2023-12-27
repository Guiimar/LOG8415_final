from flask import Flask, request
import requests
import random
import paramiko
import sshtunnel
from sshtunnel import SSHTunnelForwarder
import pymysql
import pythonping
from pythonping import ping

app= Flask(__name__)

#Will be updated in main with corresponding Ip
private_ip_address_nodes={}

public_ip_address_nodes={}

master_ip=private_ip_address_nodes['Master_cluster']

private_nodes_ip=[value for key, value in private_ip_address_nodes.items() if key != "Master_cluster"]
public_nodes_ip=[value for key, value in public_ip_address_nodes.items() if key != "Master_cluster"]


#Function to determine the nature of the query ( read or write)
def test_write(request):
    write_words=['insert','delete','update','create','alter']
    request_data = request.get_json()
    request_sql = request_data.get('data_sql')
    words_request=request_sql.strip().lower().split()

    for keyword in write_words:
        if keyword in words_request:
             return True
        
    return False

#request to send an request
def send_query(request,ip_address,master_ip):
     request_data = request.get_json()
     request_sql = request_data.get('data_sql')
     ssh_key = paramiko.RSAKey.from_private_key_file('labuser.pem')
     try:
        #create a tunnel SSH connection
        tunnel=SSHTunnelForwarder(
            host=ip_address,
            ssh_username='ubuntu',
            ssh_pkey=ssh_key,
            remote_bind_address=('127.0.0.1', 3306))
        tunnel.start()
        # pymysql connection 
        con=pymysql.connect(host=master_ip,
                                user='myapp',
                                password='password',
                                database='sakila',
                                port='3306',
                                charset='utf8mb4')
        cursor=con.cursor()
        cursor.execute(request_sql)
        result=cursor.fetchall()
        con.commit()
        cursor.close()
        con.close()
        return str(result),200
     except Exception as e:
        return str(e),500

#Ping each of the nodes and get the fastest one
def get_fastest_slave(nodes):
    #https://www.ictshore.com/python/python-ping-tutorial/
    fastest_response = 100000
    fastest_node=None
    for node in nodes:
         time_ping=ping(target=node,count=2,timeout=2).rtt_avg_ms
         if time_ping<fastest_response:
              fastest_response=time_ping
              fastest_node=node
    return node

@app.route('/direct',methods=['POST'])
#the request is directly forwarded to the master node
def direct_master():
    try:
        return send_query(request,master_ip,master_ip)
    except Exception as e:
        return str(e),500

@app.route('/random',methods=['POST'])
#the request is directly forwarded to a randomized node
def randomized():
    try:
        if test_write(request):
                return send_query(request,master_ip,master_ip)
        
        random_node=random.choice(private_nodes_ip)
        return send_query(request,random_node,master_ip)
    except Exception as e:
        return str(e),500


@app.route('/customized',methods=['POST'])
#the request is directly forwarded to the fastest responding node 
def customized():
    try:
        if test_write(request):
            return send_query(request,master_ip,master_ip)
        node_fastest=get_fastest_slave(private_nodes_ip)
        send_query(request,node_fastest,master_ip)
    except Exception as e:
        return str(e),500

if __name__=='__main__':
    app.run(host='127.0.0.1',port=5000)