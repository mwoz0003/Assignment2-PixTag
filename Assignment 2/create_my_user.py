# create_my_user.py
import boto3
import json

iam = boto3.client('iam')

# Create an admin user for yourself
username = 'matthew-admin'
password = 'TempPassword123!'

try:
    # Create user
    iam.create_user(UserName=username)
    
    # Give admin access
    iam.attach_user_policy(
        UserName=username,
        PolicyArn='arn:aws:iam::aws:policy/AdministratorAccess'
    )
    
    # Create access keys
    keys = iam.create_access_key(UserName=username)
    
    print(f"Created user: {username}")
    print(f"Access Key ID: {keys['AccessKey']['AccessKeyId']}")
    print(f"Secret Access Key: {keys['AccessKey']['SecretAccessKey']}")
    print("\nUse these for 'aws configure' instead of root keys!")
    
except Exception as e:
    print(f"Error: {e}")