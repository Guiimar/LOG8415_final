from flask import Flask, request
import requests

public_ip_address_proxy=''
private_ip_address_proxy=''
proxy_port=''

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
