#!/bin/bash
# Clone the git repository for the assignement 
git clone https://github.com/Guiimar/LOG8415_final.git
# Open folder TP2
cd LOG8415E_TP2/TP2
# Enter your AWS credentials here
new_aws_access_key="key"
new_aws_secret_key="secret"
new_aws_token_key="token"

# Fill in the credentials.ini file with entered aws_access_key
sed -i "s#aws_access_key_id=.*#aws_access_key_id=${new_aws_access_key}#" credentials.ini

# Fill in the credentials.ini file with entered new_aws_secret_key
sed -i "s#aws_secret_access_key=.*#aws_secret_access_key=${new_aws_secret_key}#" credentials.ini

# Fill in the credentials.ini file with entered new_aws_token_key
sed -i "s#aws_session_token=.*#aws_session_token=${new_aws_token_key}#" credentials.ini

# Install boto3
pip install boto3

# Install requests
pip install requests

# Install configparser
pip install configparser

# Open the folder Deployment
cd Deployment

#Execute Setup python file

python3 Setup_standalone.py

python3 Setup_clusterbenchmark.py

python3 Setup_main.py

# Execute Sending request python file
python3 Sending_requests.py

