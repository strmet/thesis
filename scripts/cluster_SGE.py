#!/usr/bin/env python3
import os
import time
import datetime
import paramiko

# All the options for the job
datasets = ['cifar10']
epochs = [300]
nets = ['vgg16', 'alexnet', 'resnet34']
batch_sizes = [512]
epsilon = ['1e-3']
bounds = [0.7]
#bounds = [0]
server = "login.dei.unipd.it"
username = "stringherm"
lr = 0.001
optimizer = 'momentum'

# Files to be uploaded
files = ['__main__.py', 'src/utils.py', 'src/vgg.py', 'src/resnet.py', 'src/alexnet.py', 'src/BasicNet.py', 'src/ConvNet.py']

# Creating a new ssh instance
ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())

# Connect to server
ssh.connect(server, username=username, key_filename='/home/met/.ssh/id_rsa.pub')

# Open secure file transfer protocol instance
sftp = ssh.open_sftp()

# Remote project path
remote_path = "/home/" + username + "/thesis/"

# Get parent directory name
local_path = os.path.dirname(os.getcwd()) + "/"

# Create custom folder
current_time = time.time()
timestamp = datetime.datetime.fromtimestamp(current_time).strftime('%Y-%m-%d_%H:%M:%S')
current_folder = "out/" + "run__" + timestamp + "/"
sftp.mkdir(remote_path + current_folder)

# Create the commands.job file
with sftp.open(remote_path + current_folder + 'commands.job', 'w') as fp:
    fp.write("#!/bin/bash \n")
    fp.write("source /nfsd/opt/anaconda3/anaconda3.sh\n"
             "conda activate /nfsd/opt/anaconda3/tensorflow\n")

    for d in datasets:
        for net in nets:
            for batch_size in batch_sizes:
                for epoch in epochs:
                    for eps in epsilon:
                        for bound in bounds:
                            # Formatting/constructing the instruction to be given:
                            instruction = "time python3 -u " + remote_path + "__main__.py --cluster --gpu"

                            # Options to be added:
                            instruction += " --dataset " + str(d)

                            instruction += " --outfolder " + current_folder

                            instruction += " --epochs " + str(epoch)

                            instruction += " --batch-size " + str(batch_size)

                            instruction += " --net " + net

                            instruction += " --ssa --epsilon " + eps + " --accepted_bound " + str(bound) + " --cooling_factor 0.99 "

                            instruction += " --lr " + str(lr) + " --momentum 0.9"

                            #instruction += " --patience " + str(patience)

                            #instruction += " --alt " if alt else ''

                            instruction += " --optimizer " + optimizer

                            fp.write(instruction + '\n')

print("Copying files")
for file in files:
    file_remote = remote_path + file
    file_local = local_path + file

    print(file_local + ' >>> ' + file_remote)

    try:
        sftp.remove(file_remote)
    except IOError:
        print("File wasn't on the cluster")
        pass

    sftp.put(file_local, file_remote)

# Give this job to the cluster
ssh_stdin, ssh_stdout, ssh_stderr = ssh.exec_command("export SGE_ROOT=/usr/share/gridengine \n" +
                                                     "cd {0}{1} \n".format(remote_path, current_folder) +
                                                     "qsub -q gpu -cwd commands.job")

# Print output and errors
print(ssh_stdout.read().decode('utf-8'))
print(ssh_stderr.read().decode('utf-8'))

sftp.close()
ssh.close()
