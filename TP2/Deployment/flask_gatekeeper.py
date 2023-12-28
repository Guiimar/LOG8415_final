from flask import Flask, request
import requests


#stock adress of the proxy to send the request
public_ip_address_proxy=''
private_ip_address_proxy=''
proxy_port=80

#creation of the flask app that receives the request
app= Flask(__name__)

#creation of the route
@app.route('/query',methods=['POST'])

def query():
    try:
        #Get the request data
        request_data = request.get_json()

        #get the type of the request
        request_type = request_data.get('type')

        #verify if request is in the righ type
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

#launch the instance listening on port 80
if __name__=='__main__':
        app.run(host='0.0.0.0',port=80)
