# Versions
## OS Version
Windows 11

## Python Version
Python 3.10.11

# How to run
1. First open up settings and find the public 'ip' address dedicated to the computer you want to run on.
2. When inside the main directory 'Blockchain-Node-Implementation', open the file BlockchainNode.py and edit the line:  
159: HOST = 'ip'
3. Then create a text file of all nodes to be connected to in 'node_list.txt'
4. Finally, using your wanted 'port' enter the following in the command line:  
python3 BlockchainNode.py port node_list.txt
