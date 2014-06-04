# fc00.org

Source code for http://fc00.org (http://www.fc00.org for clearnet)

## Sending your view of the network
```bash
wget https://raw.githubusercontent.com/Randati/fc00.org/master/scripts/sendGraph.py
nano sendGraph.py
chmod +x sendGraph.py

# Run this every 5-60 minutes
./sendGraph.py
```

## Web server
```bash
git clone git@github.com:Randati/fc00.org.git
sudo apt-get install python-flask python-flup python-mysqldb

cd web
cp lighttp.example.conf lighttp.conf
nano lighttp.conf
sudo sh -c "echo 'include \"/path/to/fc00.org/web/lighttp.conf\"' >> /etc/lighttpd/lighttpd.conf"
```
