#!/bin/bash
sudo apt-get -y update
sudo DEBIAN_FRONTEND=noninteractive apt-get install -y python3-venv 

# Create a flaskapp directory
mkdir /home/ubuntu/flaskapp && cd /home/ubuntu/flaskapp 

#Create the virtual environment
python3 -m venv venv

#Activate the virtual environment
source venv/bin/activate

#Install Flask
pip install Flask
pip install jsons
pip install flask-restful
pip install requests

cat <<EOL > /home/ubuntu/flaskapp/flask_gatekeeper.py
from flask import Flask, request
import requests

public_ip_address_proxy=" "
private_ip_address_proxy=" "
proxy_port=80

app= Flask(__name__)

@app.route('/query',methods=['POST'])

def query():
    try:
        #creation of the url
        #Get the request data
        request_data = request.get_json()

        request_type = request_data.get('type')

        if request_type not in ['direct','random','customized']:
             return "Type is not valid",400
        
        #creation of the url
        url_proxy="http://{}:{}/{}".format(private_ip_address_proxy, proxy_port,request_type)
        #post to send the request to the container 
        response=requests.post(url_proxy,json=request_data,headers = {'Content-Type': 'application/json'})
        if response.status_code == 200:
             return response.text,200
        else :
             return "Error during process",500
             
    except Exception as e:
        print('Exception returned is',e)
    return str(e),500

if __name__=='__main__':
        app.run(host='0.0.0.0',port=80)
EOL

#lauching the flask app on the server 
python /home/ubuntu/flaskapp/flask_gatekeeper.py