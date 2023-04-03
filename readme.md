# Python Peer-to-Peer (PyP2P)
This is peer-to-peer file transfer software written in Python. It was made as part of the Computer Networks (CS348) course at the Indian Institute of Technology, Dharwad.

The software consists of two parts: a peer and a manager. A single manager must be running at all times. The manager is responsible for keeping track of all the active peers. Peers can connect to the manager and register themselves. The peers can then connect to each other directly and transfer files.

# Setup
The `MANAGER_HOST` and `MANAGER_PORT` variables in the [peer.py](peer.py) and [manager.py](manager.py) files must be set to the IP address and port number of the manager. 

# Usage
The manager can be started by running the [manager.py](manager.py) file, it must be running before any peers are started.

A peer can be started by running the [peer.py](peer.py) file. On startup the program will ask for a shared folder, any files in this folder may be transferred to other peers if they request it. The program will then ask for file which it should attempt to download from other peers. The program will then attempt to download the file parallely from other peers, if found it will be saved in the shared folder.

# Options
## Verbose Mode
Passing the `-v` or `--verbose` flag to [peer.py](peer.py) will enable verbose mode. In verbose mode the program will print out all the status updates.

# Demo
## Video
[Demo Video](https://youtu.be/hnGVwJPzXek)
<iframe width="560" height="315" src="https://www.youtube.com/embed/hnGVwJPzXek" title="YouTube video player" frameborder="0" allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture; web-share" allowfullscreen></iframe>

## Instructions
First unzip the demo files by running the following command from the root directory of the project:
```
unzip demo.zip
```
Then start the manager by running the following command from the root directory of the project:
```
python3 manager.py
```
Then start the 3 peers by running the following command from the root directory of the project:
```
python3 peer.py
```
Give [1](1) as the shared directory in 2 of the peers and [2](2) as the shared directory in 1 of the peers.

Notice that the folder [2](2) is inititally empty.
In the peer with shared directory [2](2) request [img.png](1/img.png). after the transfer is complete notice that the file has been transfered to the folder [2](2)!