#!  /usr/bin/python3
import os
from re import I
import subprocess
import argparse

def parse_command_line_arguments():
    '''
    Use argparse to get user and project list
    '''
    parser = argparse.ArgumentParser()
    parser.add_argument("-u","--users",nargs="+",default=None,help="User list.")
    parser.add_argument("-p","--projects",nargs="+",default=None,help="List of projects accounts.")
    parser.add_argument("-q","--qos",nargs="+",default=None,help="List of qos to add." )
    args = parser.parse_args()
    return args

def add_user(username):
    '''
    Call useradd to add user to system
    
    Args:
        username (str): username to add
    '''
    try:
        subprocess.run("useradd --create-home --home /data/" + username+" --user-group --shell /bin/bash " + username, shell=True, check=True)
    except:
        print("Error calling user add in add-user")

def create_qos(qos_name):
    '''
    Call to sacctmgr to create qos.

    Args:

    qos_name (str): name of quality of service
    '''
    try:
        subprocess.run("sacctmgr --immediate add qos " + qos_name, shell=True, check=True)
    except:
        print("Error calling add qos in create_qos")

def sacctmgr_modify(entity,spec1,value1,spec2,value2,operation):
    '''
    Call sacctmgr to modify an entity:
        `sacctmgr modify <entity> where <spec1>=<value1> set <spec2><operation><value2>`

    Args:
        entity(str): Slurm entity to modify
        spec1(str): defines slurm specification to make change to
        value1(str): Value for slurm spec1
        spec2(str): Slurm specification to set
        value2(str): value that spec2 will be set
        operation(str): either "=","+=","-="
    '''
    try:
        print("sacctmgr --immediate modify " + entity + " " + spec1 +"="+value1+" set "+spec2+operation+value2)
        subprocess.run("sacctmgr --immediate modify " + entity +" "+ spec1 +"="+value1+" set "+spec2+operation+value2, shell=True, check=True)
    except:
        print("Error calling sacctmgr modify in sacctmgr_modify")

def sacctmgr_add(entity,spec1,value1,spec2,value2,operation):
    '''
    Call sacctmgr to add to an entity:
        `sacctmgr add where <spec1>=<value1> set <spec2><operation><value2>`
        e.g. `sacctmgr add user=cor22 account=prj1_phase1`
    Args:
        spec1(str): defines slurm specification to make change to
        value1(str): Value for slurm spec1
        spec2(str): Slurm specification to set
        value2(str): value that spec2 will be set
        operation(str): either "=","+=","-="
    '''
    try:
        print("sacctmgr --immediate add " + entity + " " +spec1 +"="+value1+" set "+spec2+operation+value2)
        subprocess.run("sacctmgr --immediate add "+ entity+" "+spec1 +"="+value1+" set "+spec2+operation+value2, shell=True, check=True)
    except:
        print("Error calling sacctmgr add in sacctmgr_add")

def create_account(project_name, qos_list):
    '''
    Call to create project account:

    Args:
        project_name (str): project_name to add
        qos_list ([str]): list of qoss to add to account
    '''
    qos_string = "".join([ qos + "," for qos in qos_list])[0:-1]
    print("QOS STRING:",qos_string)
    try:
        print("sacctmgr --immediate create account name=" + project_name + " qos=" + qos_string)
        subprocess.run("sacctmgr --immediate create account name=" + project_name + " qos=" + qos_string, shell=True, check=True)
    except:
        print("Error calling sacctmgr in create_account")

if __name__ == '__main__':

    args = parse_command_line_arguments()

    for user in args.users: 
        add_user(user)

    for qos in args.qos:
        create_qos(qos)

    for user in args.users:
        for qos in args.qos:
            sacctmgr_modify("user","name",user,"qos",qos,"+=")

    for project in args.projects:
        create_account(project,args.qos)

    for id,user in enumerate(args.users):
        sacctmgr_add("user","name",user,"account",args.projects[id],"+=") 

    subprocess.run("scontrol reconfig",shell=True,check=True)
