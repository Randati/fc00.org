# fc00.org

Source code for http://fc00.org (http://www.fc00.org for clearnet)


## Web server
```bash
git clone git@github.com:Randati/fc00.git
sudo apt-get install python-flask python-flup

cd web
cp lighttp.example.conf lighttp.conf
nano lighttp.conf
sudo sh -c "echo 'include \"/path/to/fc00/web/lighttp.conf\"' >> /etc/lighttpd/lighttpd.conf"
```


## Mapper
```bash
git clone git@github.com:Randati/fc00.git
sudo apt-get install python-pygraphviz python-httplib2

cd mapper
cp conf_sh.example.py conf_sh.py
nano conf_sh.py

./start-mappers.sh
./makeGraph.py && scp graph.json user@www.fc00.org:/path/to/fc00/web/static/graph.json
```
