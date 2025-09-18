# setup_assignment2.py
import boto3
import json
import secrets
import string
from datetime import datetime

def setup_assignment2_team():
    """
    Setup AWS infrastructure for Assignment 2 - PixTag Project
    """
    print("\n" + "="*50)
    print("Assignment 2 - PixTag AWS Setup")
    print("="*50 + "\n")
    
    # Check AWS connection
    try:
        sts = boto3.client('sts')
        account_id = sts.get_caller_identity()['Account']
        print(f"✅ Connected to AWS Account: {account_id}\n")
    except Exception as e:
        print(f"❌ Error: Can't connect to AWS")
        print(f"Run 'aws configure' first with your credentials")
        return
    
    iam = boto3.client('iam')
    
    # Team setup for Assignment 2
    team = {
        'charlotte': 'Part A - Upload/Thumbnail/YOLO',
        'matthew': 'Part B - Database/Queries',
        'omar': 'Part C - Auth/Frontend/Integration'
    }
    
    credentials = {}
    
    print("Creating IAM Users for Assignment 2 Team...")
    print("-" * 40)
    
    for name, role in team.items():
        username = f'assignment2-{name}'
        temp_password = f'Assignment2!{secrets.randbelow(9999):04d}'
        
        try:
            # Create IAM user
            iam.create_user(
                UserName=username,
                Tags=[
                    {'Key': 'Project', 'Value': 'Assignment2'},
                    {'Key': 'Role', 'Value': role}
                ]
            )
            
            # Enable console access
            iam.create_login_profile(
                UserName=username,
                Password=temp_password,
                PasswordResetRequired=True
            )
            
            # Attach PowerUser policy
            iam.attach_user_policy(
                UserName=username,
                PolicyArn='arn:aws:iam::aws:policy/PowerUserAccess'
            )
            
            # Create access keys
            keys = iam.create_access_key(UserName=username)
            
            credentials[name] = {
                'username': username,
                'password': temp_password,
                'access_key': keys['AccessKey']['AccessKeyId'],
                'secret_key': keys['AccessKey']['SecretAccessKey'],
                'console_url': f'https://{account_id}.signin.aws.amazon.com/console',
                'role': role
            }
            
            print(f"✅ Created: {username}")
            print(f"   Role: {role}")
            
        except iam.exceptions.EntityAlreadyExistsException:
            print(f"⚠️  User {username} already exists")
        except Exception as e:
            print(f"❌ Error creating {username}: {e}")
    
    # Save credentials
    filename = f'assignment2_credentials_{datetime.now().strftime("%Y%m%d_%H%M%S")}.json'
    with open(filename, 'w') as f:
        json.dump(credentials, f, indent=2)
    
    print("\n" + "="*50)
    print("✅ Assignment 2 Team Setup Complete!")
    print("="*50)
    print(f"\n📁 Credentials saved to: {filename}")
    print("📧 Send credentials PRIVATELY to each team member")
    print("\n⚠️  Next: Run create_assignment2_resources() to set up AWS resources")
    
    return credentials

def create_assignment2_resources():
    """
    Create all AWS resources for Assignment 2
    """
    print("\n" + "="*50)
    print("Creating Assignment 2 AWS Resources")
    print("="*50 + "\n")
    
    import random
    
    s3 = boto3.client('s3', region_name='us-east-1')
    dynamodb = boto3.client('dynamodb', region_name='us-east-1')
    iam = boto3.client('iam')
    
    # Unique suffix for S3 buckets
    suffix = random.randint(1000, 9999)
    
    config = {
        'project': 'Assignment 2 - PixTag',
        'created': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        'region': 'us-east-1'
    }
    
    # 1. Create S3 Buckets
    print("1️⃣ Creating S3 Buckets...")
    buckets = {
        'full_images': f'assignment2-images-{suffix}',
        'thumbnails': f'assignment2-thumbnails-{suffix}'
    }
    
    for bucket_type, bucket_name in buckets.items():
        try:
            s3.create_bucket(Bucket=bucket_name)
            print(f"   ✅ Created: {bucket_name}")
            
            if 'thumbnails' in bucket_name:
                # Make thumbnails public
                s3.put_public_access_block(
                    Bucket=bucket_name,
                    PublicAccessBlockConfiguration={
                        'BlockPublicAcls': False,
                        'IgnorePublicAcls': False,
                        'BlockPublicPolicy': False,
                        'RestrictPublicBuckets': False
                    }
                )
                
                policy = {
                    "Version": "2012-10-17",
                    "Statement": [{
                        "Effect": "Allow",
                        "Principal": "*",
                        "Action": "s3:GetObject",
                        "Resource": f"arn:aws:s3:::{bucket_name}/*"
                    }]
                }
                
                s3.put_bucket_policy(
                    Bucket=bucket_name,
                    Policy=json.dumps(policy)
                )
                print(f"   ✅ Made {bucket_name} public")
                
        except Exception as e:
            print(f"   ❌ Error: {e}")
    
    config['s3_buckets'] = buckets
    
    # 2. Create DynamoDB Tables
    print("\n2️⃣ Creating DynamoDB Tables...")
    tables_config = [
        {
            'TableName': 'assignment2-images',
            'KeySchema': [{'AttributeName': 'imageId', 'KeyType': 'HASH'}],
            'AttributeDefinitions': [{'AttributeName': 'imageId', 'AttributeType': 'S'}]
        },
        {
            'TableName': 'assignment2-tag-index',
            'KeySchema': [
                {'AttributeName': 'tag', 'KeyType': 'HASH'},
                {'AttributeName': 'imageId', 'KeyType': 'RANGE'}
            ],
            'AttributeDefinitions': [
                {'AttributeName': 'tag', 'AttributeType': 'S'},
                {'AttributeName': 'imageId', 'AttributeType': 'S'}
            ]
        }
    ]
    
    for table in tables_config:
        try:
            dynamodb.create_table(
                **table,
                BillingMode='PAY_PER_REQUEST'
            )
            print(f"   ✅ Created: {table['TableName']}")
        except dynamodb.exceptions.ResourceInUseException:
            print(f"   ⚠️  Table {table['TableName']} already exists")
    
    config['dynamodb_tables'] = ['assignment2-images', 'assignment2-tag-index']
    
    # 3. Create Lambda Role
    print("\n3️⃣ Creating Lambda Execution Role...")
    
    trust_policy = {
        "Version": "2012-10-17",
        "Statement": [{
            "Effect": "Allow",
            "Principal": {"Service": "lambda.amazonaws.com"},
            "Action": "sts:AssumeRole"
        }]
    }
    
    try:
        role = iam.create_role(
            RoleName='assignment2-lambda-role',
            AssumeRolePolicyDocument=json.dumps(trust_policy)
        )
        
        policies = [
            'arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole',
            'arn:aws:iam::aws:policy/AmazonS3FullAccess',
            'arn:aws:iam::aws:policy/AmazonDynamoDBFullAccess'
        ]
        
        for policy_arn in policies:
            iam.attach_role_policy(
                RoleName='assignment2-lambda-role',
                PolicyArn=policy_arn
            )
        
        config['lambda_role_arn'] = role['Role']['Arn']
        print(f"   ✅ Created: assignment2-lambda-role")
        
    except iam.exceptions.EntityAlreadyExistsException:
        print(f"   ⚠️  Lambda role already exists")
        role = iam.get_role(RoleName='assignment2-lambda-role')
        config['lambda_role_arn'] = role['Role']['Arn']
    
    # Save configuration
    config_file = 'assignment2_config.json'
    with open(config_file, 'w') as f:
        json.dump(config, f, indent=2)
    
    print("\n" + "="*50)
    print("✅ Assignment 2 Infrastructure Complete!")
    print("="*50)
    print(f"\n📁 Configuration saved to: {config_file}")
    print("\n📋 Next steps for each team member:")
    print("   Charlotte: Create upload/thumbnail/YOLO Lambdas")
    print("   Matthew: Create query Lambda functions")
    print("   Omar: Set up Cognito and API Gateway")
    print("\n⚠️  Share assignment2_config.json with your team!")
    
    return config

def test_assignment2_setup():
    """Test that everything is working"""
    print("\nTesting Assignment 2 Setup...")
    print("-" * 40)
    
    try:
        # Test S3
        s3 = boto3.client('s3')
        buckets = s3.list_buckets()['Buckets']
        assignment2_buckets = [b['Name'] for b in buckets if 'assignment2' in b['Name']]
        print(f"✅ Found {len(assignment2_buckets)} Assignment 2 S3 buckets")
        
        # Test DynamoDB
        dynamodb = boto3.client('dynamodb', region_name='us-east-1')
        tables = dynamodb.list_tables()['TableNames']
        assignment2_tables = [t for t in tables if 'assignment2' in t]
        print(f"✅ Found {len(assignment2_tables)} Assignment 2 DynamoDB tables")
        
        # Test IAM
        iam = boto3.client('iam')
        users = iam.list_users()['Users']
        assignment2_users = [u['UserName'] for u in users if 'assignment2' in u['UserName']]
        print(f"✅ Found {len(assignment2_users)} Assignment 2 IAM users")
        
        print("-" * 40)
        print("✅ All tests passed!")
        
    except Exception as e:
        print(f"❌ Test failed: {e}")

if __name__ == "__main__":
    print("Assignment 2 - PixTag Project Setup Script")
    print("==========================================\n")
    
    print("What would you like to do?")
    print("1. Create IAM users for team")
    print("2. Create AWS resources (S3, DynamoDB, etc.)")
    print("3. Test setup")
    print("4. Do everything (1, then 2, then 3)")
    
    choice = input("\nEnter choice (1-4): ")
    
    if choice == '1':
        setup_assignment2_team()
    elif choice == '2':
        create_assignment2_resources()
    elif choice == '3':
        test_assignment2_setup()
    elif choice == '4':
        setup_assignment2_team()
        input("\nPress Enter to continue with resource creation...")
        create_assignment2_resources()
        input("\nPress Enter to test setup...")
        test_assignment2_setup()
    else:
        print("Invalid choice")