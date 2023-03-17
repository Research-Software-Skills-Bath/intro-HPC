
import os
import argparse
import python_on_whales
from python_on_whales import docker, exceptions, DockerClient
import time
import subprocess

'''
Script to build and start slurm-docker-cluster:
    builds image
    starts containers
    runs slurm-setup on the slurmctld container
    restarts containers for changes to take effect    

'''
def parse_command_line_arguments():
    '''
    Use argparse to get input settings
    '''
    parser = argparse.ArgumentParser()
    parser.add_argument("-b","--build",action='store_true',help="Whether to build the slurm-cluster image or not")
    parser.add_argument("-c","--cache",action='store_true',help="Whether to use the build cache")
    parser.add_argument("-r","--register",action='store_true',help="Whether to register the slurm-cluster or not")
    parser.add_argument("-n","--name",default="HPCcluster",help="If register==True the name to give the cluster")
    parser.add_argument("-u","--up",action='store_false',help="If up==True run docker compose up to bring the cluster up")
    args = parser.parse_args()
    return args

def read_users():
    with open("user_list.txt","r") as f:
        users=[line.rstrip() for line in f]

    return users

if __name__ == '__main__':

    args = parse_command_line_arguments()
    os.environ['COMPOSE_PROJECT_NAME'] = "slurm-docker-cluster"
#    qos= ["spot-fsv2-2","spot-hb-60","spot-hbv2-120","spot-hbv3-120","spot-hc-44","spot-ncv3-12","spot-ndv2-40",
#          "paygo-fsv2-2","paygo-hb-60","paygo-hbv2-120","paygo-hbv3-120","paygo-hc-44","paygo-ncv3-12","paygo-ndv2-40"]
    qos=["bigjob","shortjob"]
    users=read_users()
    project_accounts=["prj"+str(i)+"_phase1" for i in range(len(users))]
    project_accounts.insert(0,"-p")
    users.insert(0,"-u")
    qos.insert(0,"-q")    
   
    if args.build:
        try:
           #subprocess.run("git clone https://github.com/giovtorres/slurm-docker-cluster", shell=True)
            docker.buildx.build(context_path="slurm-docker-cluster/",cache=args.cache,tags=["slurm-docker-cluster"])
        except python_on_whales.exceptions.DockerException as err:
            print("Error calling build in image {}".format(err))

    if args.up:
        try:
            os.environ['COMPOSE_PROJECT_NAME'] = "slurm-docker-cluster"
            docker = DockerClient(compose_files=["slurm-docker-cluster/docker-compose.yml"])
            docker.compose.up(detach=True)
            print("compute up")
            ctld_up = False
            while not ctld_up:
                ctld_up="slurmctld" in [container.name for container in docker.container.list()]
                time.sleep(1)
        except python_on_whales.exceptions.DockerException as err:
            print("Error starting slurm cluster {}".format(err))
            exit(1)

    if args.register:
        slurmdbd_up = False
        while not slurmdbd_up:
            slurmdbd_up="slurmdbd" in [container.name for container in docker.container.list()]
            time.sleep(1)
        time.sleep(20)
        docker.execute("slurmctld",["/usr/bin/sacctmgr","--immediate","add","cluster","name="+args.name])
        try:        
            docker.restart(["slurmctld","slurmdbd"])
        except python_on_whales.exceptions.DockerException as err:
            print("Error restarting slurmctld & slurmdbd {}".format(err))
            exit(1)

    try:
        docker.copy("cluster_scripts/setup_cluster.py","slurmctld:/etc/slurm/setup_cluster.py")        
        docker.execute("slurmctld",["chmod","755","/etc/slurm/setup_cluster.py"])
        print(["/etc/slurm/setup_cluster.py"]+users+project_accounts+qos)
        docker.execute("slurmctld",["/etc/slurm/setup_cluster.py"]+users+project_accounts+qos)
        docker.execute("slurmctld",["/etc/slurm/setup_cluster.py"]+users+project_accounts+qos)
        print("Executed setup script",users+project_accounts+qos)
    except python_on_whales.exceptions.DockerException as err:
        print("Error starting app or running /etc/slurm/setup_cluster.py in slurmctld: {}".format(err))
        exit(1)

    subprocess.run("cp connect_cluster /usr/local/bin/connect_cluster ", shell=True)
    subprocess.run("chmod 755  /usr/local/bin/connect_cluster", shell=True)
    subprocess.run("ls -d /jupyter/jupyter-* | while read I; do usermod -aG docker $I; done", shell=True)

