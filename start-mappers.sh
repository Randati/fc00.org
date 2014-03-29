#!/bin/bash

source mapperconf_sh.py
mkdir -p mapper-confs

for i in $(seq 1 $num_of_nodes)
do
	echo "Starting mapper node $i/$num_of_nodes"

	file=mapper-confs/node$i.conf
	rpcport=$(($rpc_firstport + $i - 1))

	$cjdns_path/cjdroute --genconf > $file

	# Set peer credentials
	sed -i 's/\/\/ Add connection credentials here to join the network/"'"${peer_ip}"':'"${peer_port}"'":{"password":"'"${peer_pw}"'","publicKey":"'"${peer_pk}"'"}/g' $file

	# Set admin rpc credentials
	sed -i 's/127.0.0.1:11234/'"${rpc_bind}"':'"${rpcport}"'/g' $file
	sed -i 's/"password": ".*"/"password": "'"${rpc_pw}"'"/g' $file

	# Disable tun interface
	sed -i 's/"type": "TUNInterface"/\/\/"type": "TUNInterface"/g' $file

	$cjdns_path/cjdroute < $file
done
