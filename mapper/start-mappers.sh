#!/bin/bash

source conf_sh.py
mkdir -p mapper-confs

# Generate configurations and collect their publick keys and ports
for i in $(seq 1 $num_of_nodes)
do
	file=mapper-confs/node$i.conf

	$cjdns_path/cjdroute --genconf > $file

	# Get connecting info
	publicKey=$(grep -oP -m1 '(?<="publicKey": ").*(?=",)' $file)
	connectPort=$(grep -oP -m1 '(?<="0.0.0.0:).*(?=",)' $file)
	connectToInfo[i]='"127.0.0.1:'"$connectPort"'":{"password":"'"$rpc_pw"'","publicKey":"'"$publicKey"'"},'
done

# Modify configurations
for i in $(seq 1 $num_of_nodes)
do
	echo "Starting mapper node $i/$num_of_nodes"

	file=mapper-confs/node$i.conf
	rpcport=$(($rpc_firstport + $i - 1))

	# Connect to all mapper nodes except itself
	connectInfo=""
	for j in $(seq 1 $num_of_nodes)
	do
		if [[ $i != $j ]]; then
			connectInfo+="${connectToInfo[j]}"
		fi
	done

	# Set peer credentials
	sed -i 's/\/\/ Add connection credentials here to join the network/'"$connectInfo"'/g' $file
	sed -i 's/\/\/ Ask somebody who is already connected./"'"${peer_ip}"':'"${peer_port}"'":{"password":"'"${peer_pw}"'","publicKey":"'"${peer_pk}"'"}/g' $file

	# Set admin rpc credentials
	sed -i 's/127.0.0.1:11234/'"${rpc_bind}"':'"${rpcport}"'/g' $file
	sed -i 's/"password": ".*"/"password": "'"${rpc_pw}"'"/g' $file

	# Disable tun interface
	sed -i 's/"type": "TUNInterface"/\/\/"type": "TUNInterface"/g' $file

	# Start mappers
	if [[ $* == *-d* ]]; then
		# Log to stdout
		sed -i 's/\/\/ "logTo":"stdout"/"logTo":"stdout"/g' $file

		gdb $cjdns_path/cjdroute -ex 'set follow-fork-mode child' -ex 'run < '"${file}" -ex 'thread apply all bt' -ex 'quit' > gdb-$i.log 2>&1 &
	else
		$cjdns_path/cjdroute < $file
	fi
done
