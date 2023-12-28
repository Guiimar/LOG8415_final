#------------------------------------Functions for EC2s instances termination ----------------------------------------------------

#Function to terminate EC2 instances when not needed
def terminate_instances(ec2_serviceresource,instances_ids):
    for id in instances_ids:
        ec2_serviceresource.Instance(id).terminate()
    return("Instances terminated")