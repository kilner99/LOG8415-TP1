import boto3
import sys, os
from botocore.exceptions import ClientError

def delete_key_pair(ec2_client, key_name):
    try:
        response = ec2_client.delete_key_pair(KeyName=key_name)
        print(f"Key pair '{key_name}' deleted successfully.")
    except ClientError as e:
        print(f"Error deleting key pair: {e}")

def get_latest_key_pair(ec2_client):
    try:
        key_name = "tp1"

        # Delete old key pair and create a new one
        delete_key_pair(ec2_client, key_name)
        response = ec2_client.create_key_pair(KeyName=key_name)

        # Extract private key
        private_key = response['KeyMaterial']

        # Path to save the key
        save_directory = os.path.expanduser('~/.aws')
        key_file_path = os.path.join(save_directory, f"{key_name}.pem")

        # Save the key to directory
        with open(key_file_path, 'w') as file:
            file.write(private_key)

        os.chmod(key_file_path, 0o400)
        return key_name

    except ClientError as e:
        print(f"Error retrieving key pairs: {e}")
        sys.exit(1)

def get_default_security_group(ec2_client, vpc_id):
    try:
        response = ec2_client.describe_security_groups(
            Filters=[
                {
                    'Name': 'group-name',
                    'Values': ['default']
                },
                {
                    'Name': 'vpc-id',
                    'Values': [vpc_id]
                }
            ]
        )
        security_groups = response.get('SecurityGroups', [])
        if not security_groups:
            print("Error: Default security group not found.")
            sys.exit(1)
        return security_groups[0]['GroupId']
    except ClientError as e:
        print(f"Error retrieving security groups: {e}")
        sys.exit(1)

def get_first_subnet(ec2_client, vpc_id):
    try:
        response = ec2_client.describe_subnets(
            Filters=[
                {
                    'Name': 'vpc-id',
                    'Values': [vpc_id]
                }
            ]
        )
        subnets = response.get('Subnets', [])
        if not subnets:
            print("Error: No subnets found in the VPC.")
            sys.exit(1)

        return subnets[0]['SubnetId']
    except ClientError as e:
        print(f"Error retrieving subnets: {e}")
        sys.exit(1)

def get_vpc_id(ec2_client):
    try:
        response = ec2_client.describe_vpcs()
        vpcs = response.get('Vpcs', [])
        if not vpcs:
            print("Error: No VPCs found.")
            sys.exit(1)
        return vpcs[0]['VpcId']
    except ClientError as e:
        print(f"Error retrieving VPCs: {e}")
        sys.exit(1)

def launch_instances(ec2_resource, image_id, count, instance_type, key_name, security_group_id, subnet_id):
    try:
        instances = ec2_resource.create_instances(
            ImageId=image_id,
            MinCount=1,
            MaxCount=count,
            InstanceType=instance_type,
            KeyName=key_name,
            SecurityGroupIds=[security_group_id],
            SubnetId=subnet_id,
            TagSpecifications=[
                {
                    'ResourceType': 'instance',
                    'Tags': [
                        {
                            'Key': 'Name',
                            'Value': 'LabInstance'
                        }
                    ]
                }
            ]
        )
        print(f"Launched {len(instances)} instance(s) successfully.")
    except ClientError as e:
        print(f"Error launching instances: {e}")
        sys.exit(1)

def main():
    # Initialize AWS clients
    ec2_client = boto3.client('ec2')
    ec2_resource = boto3.resource('ec2')

    # Parameters
    IMAGE_ID = 'ami-0e86e20dae9224db8'   # Replace with your AMI ID
    INSTANCE_TYPE = 't2.micro'
    INSTANCE_COUNT = 1

    vpc_id = get_vpc_id(ec2_client)
    print(f"Using VPC ID: {vpc_id}")

    key_name = get_latest_key_pair(ec2_client)
    print(f"Using Key Pair: {key_name}")

    security_group_id = get_default_security_group(ec2_client, vpc_id)
    print(f"Using Security Group ID: {security_group_id}")

    subnet_id = get_first_subnet(ec2_client, vpc_id)
    print(f"Using Subnet ID: {subnet_id}")

    launch_instances( ec2_resource, IMAGE_ID, INSTANCE_COUNT, INSTANCE_TYPE, key_name, security_group_id, subnet_id )

if __name__ == "__main__":
    main()
