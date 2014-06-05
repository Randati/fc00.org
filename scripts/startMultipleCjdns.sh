#!/bin/bash

###############################################################################
# CONFIG

cjdns_path="/home/user/cjdns"
num_of_nodes=5

# Where nodes connect to
peer_ip="127.0.0.1"
peer_port="55555"
peer_pw="mapper-hunter2"
peer_pk="foobarbaz9876543211337asdf.k"

# RPC settings for nodes
rpc_bind="127.0.0.1"
rpc_pw="hunter2"
rpc_firstport=11234

###############################################################################



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

	if [[ $* == *-d* ]]; then
		# Log to stdout
		sed -i 's/\/\/ "logTo":"stdout"/"logTo":"stdout"/g' $file

		gdb $cjdns_path/cjdroute -ex 'set follow-fork-mode child' -ex 'run < '"${file}" -ex 'thread apply all bt' -ex 'quit' > gdb-$i.log 2>&1 &
	else
		$cjdns_path/cjdroute < $file
	fi
done