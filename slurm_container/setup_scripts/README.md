# Set Up Slurm cluster on JH server

The following scripts set-up the slurm cluster on the container.

Requirements:

```
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

In order to build the image, and set-up the conatiner run:

```
python3 ./create_and_start_cluster.py --build --register
```

To just start the cluster if the container has already been built:

```
python3 ./create_and_start_cluster.py --up
```

You will need a list of users in the file user_list.txt

To just stop the cluster if the container is already running:

```
python3 ./create_and_start_cluster.py --down
```
