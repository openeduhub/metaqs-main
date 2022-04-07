vim .ssh/authorized_keys 
exit
sudo apt update
sudo apt upgrade
reboot
sudo reboot
sudo apt install apt-transport-https ca-certificates curl software-properties-common
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo apt-key add -
sudo add-apt-repository "deb [arch=amd64] https://download.docker.com/linux/ubuntu focal stable"
apt-cache policy docker-ce
sudo apt install docker-ce
sudo systemctl status docker
docker ps
sudo usermod -aG docker ${USER}
su - ${USER}
exit
groups
docker ps
sudo curl -L "https://github.com/docker/compose/releases/download/1.29.2/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose
sudo ln -s /usr/local/bin/docker-compose /usr/bin/docker-compose
docker-compose --version
exit
docker pull postgres
docker image ls
pwd
ls
cd /
ls
touch test
ls -l
sudo touch test
sudo rm test 
sudo mkdir .dbt
groups
sudo chown -r cloud:cloud .dbt
sudo chown -R cloud:cloud .dbt
sudo mv .dbt dbt.git
ls -l
ls
ls -l
ls dbt.git/hooks/
sudo mkdir /api.git
sudo chown -R cloud:cloud /api.git
which git
ls
sudo mkdir metaqs
sudo chown -R cloud:cloud metaqs
mv api.git dbt.git metaqs/
ls -l
sudo mv api.git dbt.git metaqs/
cd metaqs/
ls
mv api.git demo.git
mv demo.git api.git
ls
cd api.git/
git --worktree ${PWD}%.git checkout -f
git --work-tree ${PWD}%.git checkout -f
git --work-tree "${PWD%.git}" checkout -f
cd ..
mkdir api
cd api
git --work-tree "${PWD%.git}" checkout -f
ls
cd ..
ls
git --git-dir=api.git --work-tree=api checkout master .
git --git-dir=api.git --work-tree=api checkout -f
ls api
git --git-dir=dbt.git --work-tree=dbt checkout -f
ls
mkdir dbt
git --git-dir=dbt.git --work-tree=dbt checkout -f
ls
touch docker-compose.yml
ls
fg
which vim
cd dbt.git/hooks/
ls
vim post-receive
ls -l
chmod +x post-receive 
ls -l
cp post-receive ../../api.git/hooks/
cd ../../
ls
vim api.git/hooks/post-receive 
ls
vim docker-compose.yml 
ls
docker image ls
docker pull erikvl87/languagetool
docker-compose build dbt
exit
sudo ufw status verbos
sudo ufw status verbose
which curl
curl www.google.com
ls
which pip
docker ps
docker image ls
docker-compose build dbt
/metaqs/
cd /metaqs/
docker-compose build dbt
curl pypi.org
curl https://pypi.org/
sudo apt install python3
which pip
pip install alembic databases dbt
sudo apt install python3-pip
pip install alembic databases dbt
docker-compose build dbt
docker run -it 95da431c8206 bash
ls
docker-compose build fastapi
docker run -it python bash
sudo apt update
pip install alembic
docker run -it python bash
docker run -it -net=host python bash
docker run -it --net=host python bash
docker network ls
docker run -it --net=bridge python bash
ls
ls /etc/systemd/network
sudo iptables -L
reboot
sudo reboot
sudo systemctl status docker
sudo systemctl stop docker
sudo systemctl start docker
docker ps
cd /metaqs/
docker-compose build dbt
cat /etc/resolv.conf 
sudo cat /run/systemd/resolve/resolv.conf 
ls -l /etc/resolv.conf 
sudo rm /etc/resolv.conf 
cd /etc/
sudo ln -s ../run/systemd/resolve/resolv.conf resolv.conf
sudo reboot
cd /metaqs/
docker-compose build dbt
cat /etc/resolv.conf 
sudo systemctl restart docker
docker-compose build dbt
docker run -it python bash
cat /etc/docker/
ls /etc/docker/
cat /etc/resolv.conf 
sudo dockerd --dns 134.76.10.46
sudo systemctl stop docker
sudo dockerd --dns 134.76.10.46
docker pull busybox
sudo systemctl start docker
docker pull busybox
sudo reboot
docker pull busybox
docker run busybox nslookup www.google.com
cat /etc/resolv.conf 
cat /run/systemd/resolve/resolv.conf 
docker run busybox cat /etc/resolv.conf
docker run -it busybox bash
docker run -it busybox sh
ls /etc/netplan/
cat /etc/netplan/50-cloud-init.yaml 
docker network inspect bridge
sudo vim /etc/docker/daemon.json
cat /etc/resolv.conf 
sudo vim /etc/docker/daemon.json
fg
sudo systemctl restart docker
cd /metaqs/
docker-compose build dbt
docker network prune
docker network ls
docker network rm 9a72e57610a1
sudo sysctl net.ipv4.ip_forward
ls /proc/sys/net/ipv4/conf/
cat /proc/sys/net/ipv4/conf/docker0/
cat /proc/sys/net/ipv4/conf/docker0/forwarding 
cat /proc/sys/net/ipv4/conf/ens3/forwarding 
docker run --rm -it alpine ping -c4 google.com
docker run --rm -it alpine ping -c4 pypi.org
docker run --rm -it busybox ping -c4 pypi.org
docker run --rm -it alpine apk update
sudo ifconfig
ip
ip link
sudo ip link set docker0 up
ip link
ls /etc/systemd/system
sudo mkdir /etc/systemd/system/docker.service.d
sudo vim /etc/systemd/system/docker.service.d/docker.conf
sudo   
systemctl daemon-reload
sudo reboot
systemctl stop docker
sudo systemctl stop docker
sudo apt-get install bridge-utils
sudo ip link set docker0 down
sudo brctl delbr docker0
sudo systemctl start docker
sudo systemctl status docker
sudo systemctl stop docker
sudo systemctl status docker
sudo rm -rf /etc/systemd/system/docker.service.d
sudo reboot
sudo systemctl status docker
sudo systemctl stop docker
sudo ip link set docker0 down
sudo brctl delbr docker0
sudo systemctl start docker
sudo systemctl status docker
cd /metaqs/
docker-compose build dbt
sudo mkdir /etc/systemd/system/docker.service.d
sudo vim /etc/systemd/system/docker.service.d/docker.conf
which docker
sudo systemctl daemon-reload
sudo systemctl status docker
sudo systemctl stop docker
sudo ip link set docker0 down
sudo brctl delbr docker0
sudo systemctl start docker
sudo systemctl status docker
sudo systemctl stop docker
sudo vim /etc/systemd/system/docker.service.d/docker.conf
sudo systemctl daemon-reload
sudo systemctl start docker
sudo systemctl status docker
sudo systemctl stop docker
sudo ip link set docker0 down
sudo brctl delbr docker0
sudo systemctl start docker
sudo rm -rf /etc/systemd/system/docker.service.d
sudo reboot
sudo systemctl start docker
route
sudo route
sudo apt install net-toolt
sudo apt install net-tools
sudo route
cat /etc/resolv.conf 
cat /lib/systemd/system/docker.service 
docker run --rm -it alpine apk update
sudo docker run --rm -it alpine apk update
sudo docker run --dns 134.76.10.46 --rm -it alpine apk update
sudo reboot
ll
vim start.sh
./start.sh
chmod +x start.sh 
./start.sh
snap install autossh
sudo snap install autossh
./start.sh
curl -XGET 127.0.0.1:9200/
ps -avz | grep "autossh"
ps | grep "autossh"
ps -aux
ps -aux | grep "autossh"
vim start.sh 
curl -XGET 172.17.0.1:9200 -d '{
  459    "query": {
  460      "bool": {
  461        "filter": [
  462          { "term": { "type": "ccm:map" }},
  463          { "term": { "permissions.read.keyword": "GROUP_EVERYONE" }},
  464          { "term": { "properties.cm:edu_metadataset.keyword": "mds_oeh" }},
  465          { "term": { "nodeRef.storeRef.protocol.keyword": "workspace" }},
  466          { "term": { "path.keyword": "94f22c9b-0d3a-4c1c-8987-4c8e83f3a92e" }}
  467        ]
  468      }
  469    },
  470    "_source": ["nodeRef.id", "properties.cm:title"],
  471    "size": 10000
  472  }' -H 'Accept: application/json'
curl -XGET 172.17.0.1:9200
curl -XGET 127.0.0.1:9201
autossh -M 20000 -f -N oeh@wirlernenonline.de -L 172.17.0.1:9200:127.0.0.1:9210
curl -XGET 127.0.0.1:9210
./start.sh
curl -X GET 172.17.0.1:9200
ssh-keygen -t rsa -b 4096 -C "metaqs-theo"
./start.sh
curl -X GET 172.17.0.1:9200
ssh-copy-id oeh@wirlernenonline.de
cat .ssh/id_rsa.pub 
./start.sh
curl -X GET 172.17.0.1:9200
autossh -M 20000 -f -N oeh@wirlernenonline.de -L 172.17.0.1:9200:127.0.0.1:9210
curl -X GET 172.17.0.1:9200
ls
cd /metaqs/
ls
vim docker-compose.yml 
docker-compose build dbt
docker image ls
docker image prune
docker image ls
docker image rm 4246fb19839f
docker container prune
docker image rm 4246fb19839f
docker image ls
docker image rm 0a97eee8041e
docker image rm 7138284460ff
docker image ls
docker image rm postgres
docker image prune
docker pull postgres:14
docker image ls
vim docker-compose.yml 
ls
mv api.git fastapi.git
mv api fastapi
ls
vim docker-compose.yml 
docker-compose build fastapi
docker image ls
ssh oeh@wirlernenonline.de
curl -X GET 172.17.0.1:9200
autossh -M 20000 -f -N oeh@wirlernenonline.de -L 172.17.0.1:9200:127.0.0.1:9210
curl -X GET 172.17.0.1:9200
ps -a | grep autossh
ps -aux | grep "autossh"
kill 7918
sudo kill 7918
ps aux
ps aux | grep autossh
autossh -M 20000 -f -N oeh@wirlernenonline.de -L 172.17.0.1:9200:127.0.0.1:9201 -L 172.17.0.1:9222:127.0.0.1:9200
ps aux | grep autossh
autossh -M 20000 -f -N oeh@wirlernenonline.de -L 172.17.0.1:9200:127.0.0.1:9201
ps aux | grep autossh
autossh -v
ssh oeh@wirlernenonline.de -L 172.17.0.1:9200:127.0.0.1:9201
ssh-keygen -p
autossh -M 20000 -f -N oeh@wirlernenonline.de -L 172.17.0.1:9200:127.0.0.1:9201
curl -X GET 172.17.0.1:9200
htop
sudo snap install htop
htop
ssh -N oeh@wirlernenonline.de -L 172.17.0.1:9200:127.0.0.1:9201
autossh -M 20000 -f -N oeh@wirlernenonline.de -L 172.17.0.1:9200:127.0.0.1:9201
sudo snap remove --purge autossh
sudo apt install autoss
autossh -M 20000 -f -N oeh@wirlernenonline.de -L 172.17.0.1:9200:127.0.0.1:9201
autossh
sudo snap remove autossh
sudo apt remove autossh
sudo snap install autossh
autossh --version
man autossh
autossh -M 20000 -f -N oeh@wirlernenonline.de -L 172.17.0.1:9200:127.0.0.1:9201
ps aux | grep autossh
ssh oeh@wirlernenonline.de
autossh -L 172.17.0.1:9200:127.0.0.1:9201 oeh@wirlernenonline.de
autossh oeh@wirlernenonline.de -L 172.17.0.1:9200:127.0.0.1:9201
autossh -f -N oeh@wirlernenonline.de -L 172.17.0.1:9200:127.0.0.1:9201
sudo autossh -f -N oeh@wirlernenonline.de -L 172.17.0.1:9200:127.0.0.1:920
autossh -M 20000 -f -N oeh@wirlernenonline.de -L 172.17.0.1:9200:127.0.0.1:9201
ps aux | grep autossh
autossh -V
ssh -N oeh@wirlernenonline.de -L 172.17.0.1:9200:127.0.0.1:9201
ps -ef | grep autossh
ssh -N oeh@wirlernenonline.de -L 172.17.0.1:9200:127.0.0.1:9210
autossh -M 20000 -f -N oeh@wirlernenonline.de -L 172.17.0.1:9200:127.0.0.1:9210
ps -ef | grep autossh
htop
sudo reboot 
autossh -M 20000 -f -N oeh@wirlernenonline.de -L 172.17.0.1:9200:127.0.0.1:9200
ps -ef | grep autossh
ssh -N oeh@wirlernenonline.de -L 172.17.0.1:9200:127.0.0.1:9200
ll
ssh -N oeh@wirlernenonline.de -L 172.17.0.1:9200:127.0.0.1:9200
autossh -V
autossh -M 20000 -N oeh@wirlernenonline.de -L 172.17.0.1:9200:127.0.0.1:9200
export AUTOSSH_DEBUG=1
autossh -M 20000 -N oeh@wirlernenonline.de -L 172.17.0.1:9200:127.0.0.1:9200
netstat -tulpn
docker -v
sudo autossh -M 20000 -N oeh@wirlernenonline.de -L 172.17.0.1:9200:127.0.0.1:9200
netstat -tulpn
export AUTOSSH_DEBUG=1
sudo autossh -M 20000 -N oeh@wirlernenonline.de -L 172.17.0.1:9200:127.0.0.1:9200
netstat -tulpn
ps -ef | grep autossh
ssh -N oeh@wirlernenonline.de -L 172.17.0.1:9200:127.0.0.1:9200
autossh -M 20000 -N oeh@wirlernenonline.de -L 172.17.0.1:9200:127.0.0.1:9200
export AUTOSSH_LOGLEVEL=7
autossh -M 20000 -N oeh@wirlernenonline.de -L 172.17.0.1:9200:127.0.0.1:9200
sudo autossh -M 20000 -N oeh@wirlernenonline.de -L 172.17.0.1:9200:127.0.0.1:9200
systemctl restart autossh
sudo systemctl restart autossh
ll
sudo snap remove autossh
autossh -V
sudo apt install autossh
autossh -V
sudo dpkg --configure -a
sudo apt-get update
autossh -V
export AUTOSSH_LOGLEVEL=7
export AUTOSSH_DEBUG=1
sudo autossh -M 20000 -N oeh@wirlernenonline.de -L 172.17.0.1:9200:127.0.0.1:9200
autossh -M 20000 -f -N oeh@wirlernenonline.de -L 172.17.0.1:9200:127.0.0.1:9200
ps -ef | grep autossh
curl -X GET 172.17.0.1:9200
ps -ef | grep autossh
sudo kill 2308
./start.sh 
sudo kill 2308
ps -ef | grep autossh
curl -XGET 172.17.0.1:9200
ll
ifconfig
netstat -tulpn
ps -ef | grep autossh
docker ps
cd /metaqs/
ls
vim docker-compose.yml 
fg
docker-compose config
vim docker-compose.yml 
docker-compose config
vim docker-compose.yml 
docker-compose run -it fastapi bash
docker-compose run -it --rm fastapi bash
docker-compose config
docker-compose up -d
docker ps
docker-compose exec fastapi bash
docker-compose down
vim docker-compose.yml 
docker-compose config
fg
docker-compose config
docker-compose up -d
fg
docker-compose up -d
docker-compose exec fastapi bash
ls
touch .env
vim .env
vim docker-compose.yml 
fg
docker ps
docker-compose down
docker container prune
docker image prune
docker image ls
ls
cat docker-compose.yml 
curl http://localhost/
docker ps
docker-compose up -d
docker ps
curl http://localhost/
docker-compose down
vim docker-compose.yml 
docker-compose up -d
docker ps
fg
docker ps
docker ps > ps.1
cat ps.1
vim dbt.git/hooks/post-receive 
docker ps
docker network ls
docker-compose exec dbt alembic upgrade head
docker-compose exec fastapi alembic downgrade
docker-compose exec fastapi alembic downgrade base
docker-compose exec dbt alembic upgrade head
fg
docker ps
docker-compose run -d --name dbt_docs --ports 8581:80 dbt "dbt docs generate && dbt docs serve"
docker-compose run -d --name dbt_docs -p 8581:80 dbt "dbt docs generate && dbt docs serve"
docker-compose run -d --name dbt_docs -p 8581:80 dbt dbt docs generate && dbt docs serve
docker ps
docker-compose logs -f fastapi
docker-compose down
docker container prune
docker image prune
docker-compose up -d
docker ps
docker-compose down
docker ps
docker-compose up -d postgres
docker-compose up -d dbt
docker ps
docker-compose exec dbt alembic downgrade base
docker-compose exec -u postgres postgres psql -d analytics
docker ps
docker-compose up -d languagetool
docker ps
docker-compose up -d nginx
docker ps
docker-compose exec dbt alembic upgrade head
docker-compose exec dbt alembic downgrade base
docker-compose exec dbt alembic upgrade head
docker-compose up -d --no-deps --force-recreate fastapi
docker-compose logs -f fastapi
docker-compose exec dbt alembic downgrade base
docker-compose exec dbt alembic upgrade head
docker ps
docker-compose logs -f fastapi
ls
ls -l fastapi
fg
vim fastapi.git/hooks/post-receive 
ls -l fastapi/app
ls -l fastapi
docker-compose build fastapi
docker-compose up -d --no-deps --force-recreate fastapi
docker container prune
docker-compose logs -f fastapi
touch fastapi/prestart.sh
docker-compose build fastapi
docker-compose up -d --no-deps --force-recreate fastapi
docker-compose logs -f fastapi
vim docker-compose.yml 
docker-compose up -d --no-deps --force-recreate fastapi
docker ps
fg
docker-compose up -d --no-deps --force-recreate fastapi
docker ps
docker-compose exec dbt alembic downgrade base
docker-compose exec dbt alembic upgrade head
docker-compose logs -f fastapi
docker ps
top
docker-compose exec -u postgres postgres psql -d analytics
docker-compose exec dbt dbt run
docker ps
docker-compose exec dbt alembic downgrade base
docker-compose exec dbt alembic upgrade head
docker-compose logs -f fastapi
docker-compose up -d --no-deps --force-recreate fastapi
docker-compose logs -f fastapi
docker ps
cp fastapi/nginx/nginx.c
cp fastapi/nginx/nginx.conf.template .
ls
rm ps.1 
vim nginx.conf.template 
ls
vim docker-compose.yml 
docker image ls
docker image prune
docker image ls
docker-compose exec -u postgres postgres psql -d analytics
docker-compose exec dbt dbt run 
docker-compose exec dbt alembic downgrade base
docker-compose exec dbt alembic upgrade head
docker-compose up -d --no-deps --force-recreate fastapi
docker-compose logs -f fastapi
docker-compose exec dbt dbt run 
docker-compose up -d --no-deps --force-recreate fastapi
docker-compose exec dbt alembic downgrade base
docker-compose exec dbt alembic upgrade head
docker-compose logs -f fastapi
docker-compose exec -u postgres postgres psql -d analytics
docker-compose logs -f fastapi
docker-compose exec -u postgres postgres psql -d analytics
docker-compose logs -f fastapi
docker-compose exec -u postgres postgres psql -d analytics
docker-compose exec dbt alembic downgrade base
docker-compose exec dbt alembic upgrade head
docker-compose up -d --no-deps --force-recreate fastapi
docker-compose logs -f fastapi
docker-compose exec -u postgres postgres psql -d analytics
exit
docker pull apache/superset
docker image ls
docker-compose exec -u postgres postgres psql -d analytics
docker ps
ls
cd /metaqs/
docker-compose exec -u postgres postgres psql -d analytics
docker-compose exec dbt dbt run 
docker-compose exec -u postgres postgres psql -d analytics
docker ps
vim docker-compose.yml 
docker-compose up -d --no-deps --force-recreate postgres
docker ps
docker-compose exec -u postgres postgres psql -d analytics
docker ps
docker-compose logs -f fastapi
docker ps
cd fastapi
ls
ls -l
cd ..
rm -rf fastapi/*
vim fastapi.git/hooks/post-receive 
git --git-dir /metaqs/fastapi.git --work-tree /metaqs/fastapi checkout -f
ls -l fastapi
docker-compose build fastapi
docker-compose up -d --no-deps --force-recreate fastapi
docker ps
fg
vim fastapi/app/pg/queries.py 
git --git-dir /metaqs/fastapi.git --work-tree /metaqs/fastapi checkout -f -b master
git --git-dir /metaqs/fastapi.git --work-tree /metaqs/fastapi checkout -f --orphan master
rm -rf fastapi/*
git --git-dir /metaqs/fastapi.git --work-tree /metaqs/fastapi checkout -f --orphan master

git checkout --work-tree /metaqs/fastapi --orphan master
git --work-tree /metaqs/fastapi checkout --orphan master
git --work-tree /metaqs/fastapi --orphan master checkout
git --work-tree /metaqs/fastapi checkout master
cd ..
ls
vim fastapi.git/hooks/post-receive 
vim dbt.git/hooks/post-receive 
docker-compose up -d --no-deps --force-recreate fastapi
docker-compose logs -f fastapi
ls -l fastapi
docker-compose exec fastapi bash
docker-compose down
docker-compose up -d
docker ps
docker-compose logs -f fastapi
vim docker-compose.yml 
docker ps
docker-compose logs -f fastapi
docker-compose run -it fastapi bash
docker-compose run fastapi bash
docker ps
docker-compose logs -f fastapi
docker-compose run fastapi bash
docker-compose logs -f fastapi
docker-compose run fastapi bash
docker-compose logs -f fastapi
ls
docker-compose up -d dbt_docs
docker ps
docker-compose logs -f dbt_docs
docker-compose stop dbt_docs
docker-compose remove dbt_docs
docker-compose rm dbt_docs
docker container prune
docker image prune
docker image ls
docker-compose up -d dbt_docs
docker ps
docker-compose logs -f dbt_docs
docker-compose stop dbt_docs
docker-compose rm dbt_docs
docker-compose up -d dbt_docs
docker ps
curl http://localhost:8081
docker ps
ls
mkdir superset
ls superset/
docker-compose build superset
docker image ls
vim superset/.env 
mv superset/.env superset.env
ls
docker-compose up -d --no-deps --force-recreate superset
docker ps
docker-compose logs -f superset
docker ps
docker exec -it superset superset fab create-admin                --username admin                --firstname Superset                --lastname Admin                --email admin@superset.com docker-compose exec superset superset fab create-admin                --username admin                --firstname Superset                --lastname Admin                --email admin@superset.com --password admin
docker exec -it superset superset fab create-admin --username admin --firstname Superset --lastname Admin --email admin@superset.com --password admin
docker-compose logs -f superset
docker-compose stop superset
docker-compose rm superset
docker container prune
docker image prune
docker volume ls
docker volume rm metaqs_superset-home 
docker-compose exec -u postgres postgres psql -d superset
docker-compose up -d --no-deps --force-recreate superset
docker-compose exec -u postgres postgres psql -d analytics
docker-compose exec superset superset db upgrade
docker-compose exec -u postgres postgres psql -d superset
docker exec -it superset superset fab create-admin --username admin --firstname Superset --lastname Admin --email admin@superset.com --password admin
docker exec -it superset superset init
docker-compose logs -f superset
docker-compose up -d --no-deps --force-recreate superset
docker-compose logs -f fastapi
docker-compose up -d --no-deps --force-recreate superset
docker-compose logs -f fastapi
docker-compose exec superset bash
docker ps
vim dbt.git/hooks/post-receive 
docker-compose up -d --no-deps --force-recreate dbt_docs
docker-compose exec dbt dbt run
docker-compose logs -f fastapi
docker ps
docker-compose up -d --no-deps --force-recreate superset
docker ps
docker-compose logs -f superset
docker ps
docker-compose down
docker-compose up -d
docker ps
docker-compose down
cd /metaqs/
docker-compose down
docker-compose up -d
docker ps
docker-compose build dbt
docker-compose up -d --no-deps --force-recreate dbt dbt_docs
docker ps
docker-compose logs -f dbt
docker ps
docker-compose logs -f fastapi

docker-compose logs -f fastapi
docker ps
docker-compose logs -f fastapi
docker ps
docker-compose logs -f fastapi
docker ps
docker-compose exec dbt dbt run-operation clear_state
docker-compose exec dbt dbt run-operation clear_state_store
docker-compose exec -u postgres postgres psql -d analytics
cd /metaqs
docker-compose up -d --no-deps --force-recreate fastapi
docker ps
docker-compose logs -f fastapi
docker-compose up -d --no-deps --force-recreate fastapi
docker-compose exec dbt dbt run-operation clear_state
docker-compose exec dbt dbt run-operation clear_state_store
docker-compose logs -f fastapi
docker-compose up -d --no-deps --force-recreate fastapi
docker-compose logs -f fastapi
docker ps
docker-compose logs -f fastapi
cd /metaqs/
docker-compose exec dbt dbt run-operation clear_state_store
docker-compose exec dbt dbt run-operation clear_state
docker-compose up -d --no-deps --force-recreate fastapi
docker-compose logs -f fastapi
docker-compose down
lll
ll
docker --version
docker-compose -v
docker image ls
ll
cd /metaqs/
ll
vim docker-compose.yml 
docker ps
docker-compose down
cd fastapi.git/
ll
cd ..
docker system prune -f
docker image ls
docker volume ls
ll
cd superset
ll
cd ..
cd superset_home/
ll
cd ..
docker volume rm metaqs_pg-data 
docker volume rm metaqs_superset-home 
docker volume ls
docker-compose rm
docker-compose up -d postgres
docker-compose logs -f
docker ps
docker image ls
docker-compose run
docker-compose run --rm
docker-compose run --rm dbt alembic upgrade head
docker-compose run --rm dbt "alembic upgrade head"
docker-compose up -d 
docker-compose logs -f#
docker-compose logs -f
vim docker-compose.yml 
ifconfig
ll
cd fastapi
ll
cd ..
vim docker-compose.yml 
vim .env 
docker ps
docker-compose up -d postgres
cd /metaqs
docker-compose up -d postgres
docker-compose run --rm dbt dbt run-operation clear_state
docker-compose run dbt dbt run-operation clear_state
docker-compose run dbt bash
docker-compose up -d --force-recreate
docker ps
docker-compose logs -f fastapi
docker ps
ls
ls dbt.git/
docker-compose exec dbt dbt run --select path:models/spellcheck
docker volume ls
docker volume inspect metaqs_superset-home 
cp /var/lib/docker/volumes/metaqs_superset-home/_data ./superset_home
sudo cp /var/lib/docker/volumes/metaqs_superset-home/_data ./superset_home
sudo cp -R /var/lib/docker/volumes/metaqs_superset-home/_data ./superset_home
ls -l
sudo chown -R cloud:cloud superset_home
ls -l
ls superset_home/
ls
docker ps
vim docker-compose.yml 
ls
docker-compose up -d --no-deps --force-recreate superset
docker ps
docker-compose exec dbt dbt run
docker ps
ls -l superset_home/
chmod -r a+w superset_home
chmod -R a+w superset_home
sudo chmod -R +w superset_home
ls -l .
sudo chmod +r superset_home
ls -l .
chmod 755 superset_home
ls -l
chmod 775 superset_home
ls -l
ls -l superset_home/
ls -la superset_home/
chmod 666 superset_home/*
ls -la superset_home/
chmod 666 superset_home/.*
sudo chmod 666 superset_home/.*
ls -la superset_home/
ls -l
ls
pwd
ls
cd ..
ls
ls -l
ls -l metaqs/
docker ps
cd /metaqs/
sudo cd /metaqs/
which cd
sudo chown -R cloud:cloud /metaqs
ls -l
ls metaqs/
cd /metaqs/
exit
docker ps
ls /metaqs/
docker stop superset
docker ps
ls
cd /metaqs/
sudo docker-compose -f /metaqs/docker-compose.yml down
docker ps
ls /metaqs/

ls /metaqs/
ls /metaqs/dbt
sudo chmod 777 /metaqs/dbt
sudo chmod 777 /metaqs/dbt/*
ls /metaqs/dbt
sudo reboot
cd /metaqs
ls -l metaqs
ls -l /metaqs
cd /metaqs
ls -l
ls -l /
chmod 755 /metaqs
cd /metaqs/
ls
ls superset_home/
chmod +x superset_home
chmod +x dbt
ls
chmod 755 dbt
chmod 755 superset_home
ls
ls dbt
ls -l dbt
ls
ls superset_home/
ls -la superset_home/
cp superset.db ../
cp superset_home/superset.db ./
ls
vim docker-compose.yml
docker-compose up -d
vim docker-compose.yml
docker-compose up -d --no-deps --force-recreate superset
docker stop superset
docker container prune
docker image prune
docker volume ls
docker-compose down
vim docker-compose.yml 
docker-compose down
vim docker-compose.yml 
apt install jq
sudo apt update
apt list --upgradable 
sudo apt install jq
docker volume inspect metaqs_superset-home | jq '.'
docker volume inspect metaqs_superset-home | jq '.Mountpoint'
docker volume inspect metaqs_superset-home | jq '.[].Mountpoint'
echo $$
echo $?
echo $P
env
docker volume inspect metaqs_superset-home | jq '.[].Mountpoint'
ls -l `docker volume inspect metaqs_superset-home | jq '.[].Mountpoint'`
ls /var/lib/docker/
sudo ls -l `docker volume inspect metaqs_superset-home | jq '.[].Mountpoint'`
sudo ls -l /var/lib/docker/volumes
sudo ls -l /var/lib/docker/volumes/metaqs_superset-home/
sudo ls -l /var/lib/docker/volumes/metaqs_superset-home/_data
docker volume rm metaqs_superset-home 
docker-compose up -d
vim docker-compose.yml 
docker-compose up -d
sudo ls -l /var/lib/docker/volumes/metaqs_superset-home/_data
sudo ls -l /var/lib/docker/volumes/metaqs_superset-home
docker stop superset
ls
ls superset_home/
ls superset_home/superset.db 
ls superset_db/
ls -l .
sudo rm -rf superset_db
chmod 644 superset.db 
ls /var/lib/docker/
sudo ls /var/lib/docker/
sudo ls /var/lib/docker/volumes
sudo ls /var/lib/docker/volumes/metaqs_superset-home/_data
sudo ls -la /var/lib/docker/volumes/metaqs_superset-home/_data
sudo cp superset.db /var/lib/docker/volumes/metaqs_superset-home/_data/
sudo ls -la /var/lib/docker/volumes/metaqs_superset-home/_data
docker-compose up -d
docker ps
docker-compose exec dbt dbt run
docker-compose down
exit
fg
exit
history | grep autossh
autossh -M 20000 -f -N oeh@wirlernenonline.de -L 172.17.0.1:9200:127.0.0.1:9200
ps -ef | grep autossh
sudo kill 25192
autossh -M 20000 -f -N oeh@wirlernenonline.de -L 172.17.0.1:9200:127.0.0.1:9210
ps -ef | grep autossh
cd /metaqs
docker-compose up -d
docker ps
docker-compose logs -f fastapi
docker-compose up -d --no-deps --force-recreate fastapi
docker-compose logs -f fastapi
docker-compose up -d --no-deps --force-recreate fastapi
docker-compose exec dbt dbt run-operation clear_state
docker-compose exec dbt dbt run-operation clear_state_store
docker-compose up -d --no-deps --force-recreate fastapi
docker-compose logs -f fastapi
docker ps
docker-compose down
docker ps
ls
cat superset.env 
ls
exit
cd /metaqs/
docker ps
docker-compose up -d
docker-compose logs -f fastapi
docker-compose down
exit
cd /metaqs/
ls
ls superset
cat docker-compose.yml 
cat superset.env
ls
exit
ll
cd /metaqs/
docker-compose up -d postgres
docker-compose up -d
docker-compose logs -f fastapi
cd /metaqs
docker ps
ls
exit
cd /metaqs
ls
cat docker-compose.yml 
exit
cd /metaqs
ls
git clone https://github.com/openeduhub/metaqs-dbt.git dbt
ls
exit
cd /metaqs/
ls
docker ps
docker-compose down
ls
cd ..
mv metaqs metaqs.bak
sudo mv metaqs metaqs.bak
ls 
ls -l
sudo mkdir metaqs
sudo chown cloud:cloud metaqs
ls -l
cd metaqs
git clone git@github.com:openeduhub/metaqs-main.git main
git clone https://github.com/openeduhub/metaqs-main.git
mv metaqs-main main
ls
cd /metaqs
ls
git clone https://github.com/openeduhub/metaqs-fastapi.git fastapi
ls
cd main
ls
git remote add staging metaqs:/metaqs/main/.git
git fetch staging
git remote remove staging
git fetch origin
git reset --hard origin/main
git status
cat docker-compose.yml 
ls
ls -a
cp .env.example .env
cat .env
docker image ls
docker image prune
docker container prune
docker-compose build fastapi
cd ../../metaqs.bak/
ls
cat docker-compose.yml 
cd ../metaqs/main
git fetch origin
git reset --hard origin/main
docker-compose build fastapi
git fetch origin
git reset --hard origin/main
docker-compose build fastapi
docker-compose build dbt
docker image ls
docker volume ls
docker volume rm metaqs_pg-data 
cat ../../metaqs.bak/docker-compose.yml 
cat ../../metaqs.bak/.env 
git fetch origin
git reset --hard origin/main
cat docker-compose.yml 
git fetch origin
git reset --hard origin/main
cp .env.example .env
cat .env
docker-compose up -d postgres
git fetch origin
git reset --hard origin/main
cp .env.example .env
vim .env
git fetch origin
git reset --hard origin/main
cp .env.example .env
vim .env
docker-compose up -d --no-deps --force-recreate nginx
docker ps
docker-compose logs
docker-compose up -d --force-recreate nginx
docker-compose logs
docker-compose down
docker volume rm metaqs_pg-data 
docker-compose up -d postgres
docker-compose run dbt alembic upgrade head
docker container prune
docker image prune
docker-compose up -d
docker-compose logs -f fastapi
cd ../fastapi/
git fetch origin
git reset --hard origin/main
cd ../main
docker-compose build fastapi
docker-compose up -d --no-deps --force-recreate fastapi
docker-compose logs -f fastapi
vim .env
docker-compose up -d --no-deps --force-recreate fastapi
docker-compose logs -f fastapi
vim .env
docker-compose up -d --no-deps --force-recreate fastapi
docker-compose exec dbt dbt run --select models/tables
ls
mkdir ../mkdocs
ls ../
ls ../mkdocs/
ls
vim docker-compose.yml 
docker ps
docker-compose up -d --no-deps --force-recreate nginx
docker-compose logs nginx
fg
docker-compose exec nginx ls /usr/share/nginx/html
docker-compose exec nginx ls /usr/share/nginx/html/docs
fg
docker-compose up -d --no-deps --force-recreate nginx
docker-compose logs nginx
git fetch origin
git reset --hard origin/main
ls -a
docker-compose up -d --no-deps --force-recreate nginx
docker-compose logs nginx
fg
ls
git status
git fetch origin
git reset --hard origin/main
docker-compose up -d --no-deps --force-recreate nginx
docker-compose logs nginx
cd ../fastapi/
ls
fg
vim app/analytics/analytics.py 
cd ../main/
docker-compose build fastapi
#docker-compose up -d --no-deps --force-recreate fastapi
vim .env
docker-compose up -d --no-deps --force-recreate fastapi
docker-compose logs -f fastapi
fg
docker-compose up -d --no-deps --force-recreate fastapi
fg
vim docker-compose.yml 
vim .env
docker-compose up -d --no-deps --force-recreate fastapi
docker-compose logs -f fastapi
vim .env
ls
git fetch origin
git reset --hard origin/main
ls
fg
docker-compose up -d
docker ps
docker-compose logs dbt-docs
docker-compose exec nginx ls /usr/share/nginx/html/dbt-docs
ls
cd ..
ls
ls ../metaqs.bak/
cd ../metaqs.bak/
ls
ls superset
fg
cat superset/Dockerfile 
ls
ls superset_home/
cat superset.env 
cat docker-compose.yml 
ls
cd ../metaqs/main
git fetch origin
git reset --hard origin/main
ls
docker-compose build superset
ls
docker-compose up -d --no-deps --force-recreate superset nginx
docker ps
docker inspect metaqs-superset
sudo ls /var/lib/docker/volumes/metaqs_superset-data/_data
sudo cp superset/superset.db /var/lib/docker/volumes/metaqs_superset-data/_data/
sudo ls -l /var/lib/docker/volumes/metaqs_superset-data/_data
docker stop metaqs-superset
docker container prune
docker volume rm metaqs_superset-data 
docker-compose up -d --no-deps --force-recreate superset
sudo ls -l /var/lib/docker/volumes/metaqs_superset-data/_data
docker-compose exec superset superset db upgrade
docker-compose exec superset superset fab create-admin --username admin --firstname Superset --lastname Admin --email admin@superset.com --password admin
docker-compose exec superset superset init
cd ../fastapi/
git fetch origin
git reset --hard origin/main
cd ../main
docker-compose build fastapi
docker-compose up -d --no-deps --force-recreate fastapi
git fetch origin
git reset --hard origin/main
docker-compose up -d --no-deps --force-recreate nginx
docker stop superset
docker stop metaqs-superset
sudo cp superset/superset.db /var/lib/docker/volumes/metaqs_superset-data/_data/
docker-compose up -d --no-deps --force-recreate superset
docker ps
exit
cd /metaqs
docker image ls
docker image prune
docker image ls
docker image rm metaqs-fastapi:latest 
docker image rm metaqs-superset:latest 
docker image rm metaqs-dbt:latest 
docker container prune
docker network prune
docker volume ls
docker volume rm metaqs_superset-home 
docker image ls
docker ps
docker-compose exec -u postgres postgres psql -d analytics
docker-compose exec postgres psql -d analytics
docker-compose exec postgres sh
docker-compose exec fastapi bash
cd main
docker-compose exec postgres psql -d analytics
docker-compose exec -u postgres postgres psql -d analytics
docker-compose exec dbt dbt run-operation clear_state
docker-compose logs -f fastapi
docker-compose exec dbt dbt run --select models/tables
docker-compose logs -f fastapi
docker-compose exec dbt dbt run --select models/spellcheck
exit
cd /metaqs/main/
docker-compose exec nginx bash
docker-compose exec nginx sh
git fetch origin
git reset --hard origin/main
vim .env
docker-compose up -d --no-deps --force-recreate nginx
docker ps
docker-compose logs nginx
git fetch origin
git reset --hard origin/main
docker-compose up -d --no-deps --force-recreate nginx
docker-compose logs -f nginx
docker-compose exec nginx sh
git fetch origin
git reset --hard origin/main
docker-compose up -d --no-deps --force-recreate nginx
docker-compose logs -f nginx
git fetch origin
git reset --hard origin/main
docker-compose up -d --no-deps --force-recreate nginx
docker-compose logs -f nginx
git fetch origin
git reset --hard origin/main
docker-compose up -d --no-deps --force-recreate nginx
docker-compose logs -f nginx
docker-compose exec nginx sh
docker-compose logs -f nginx
git fetch origin
git reset --hard origin/main
docker-compose up -d --no-deps --force-recreate nginx
cd /metaqs/main
cd ../fastapi/
git fetch origin
git reset --hard origin/main
cd ../main
ls
docker-compose build fastapi
ls
vim .env
ls
docker ps
exit
ls
cd /metaqs/main
git fetch origin
git reset --hard origin/main
cat .env
docker-compose up -d --no-deps --force-recreate nginx
docker ps
docker-compose up -d --no-deps --force-recreate nginx fastapi
docker ps
docker-compose logs -f fastapi
vim .env
git fetch origin
git reset --hard origin/main
docker-compose up -d --no-deps --force-recreate nginx fastapi
docker-compose logs -f fastapi
docker-compose exec nginx cat /etc/nginx/conf.d/default.conf
ls
cat .env
cat docker-compose.yml 
docker-compose up -d --no-deps --force-recreate nginx fastapi
docker-compose exec nginx cat /etc/nginx/conf.d/default.conf
vim nginx/nginx.conf.template 
docker-compose up -d --no-deps --force-recreate nginx fastapi
docker-compose exec nginx cat /etc/nginx/conf.d/default.conf
vim nginx/nginx.conf.template 
vim docker-compose.yml 
docker-compose up -d --no-deps --force-recreate nginx fastapi
docker-compose exec nginx cat /etc/nginx/conf.d/default.conf
git fetch origin
git reset --hard origin/main
docker-compose up -d --no-deps --force-recreate nginx fastapi
vim .env
docker-compose build fastapi
docker ps
docker-compose up -d --no-deps --force-recreate fastapi
docker-compose logs -f fastapi
docker ps
docker-compose build fastapi
vim .env
docker-compose up -d --no-deps --force-recreate fastapi
docker-compose logs -f fastapi
docker-compose build fastapi
docker-compose up -d --no-deps --force-recreate fastapi
docker-compose logs -f fastapi
cat .env
git fetch origin
git reset --hard origin/main
docker-compose build fastapi
docker-compose up -d --no-deps --force-recreate fastapi
docker-compose logs -f fastapi
docker ps
cd /metaqs/fastapi/
git fetch origin
git reset --hard origin/main
git status
git fetch origin
git reset --hard origin/main
git fetch origin
git reset --hard origin/main
exit
vim .ssh/authorized_keys 
exit
cd /metaqs
ll
vim .ssh/authorized_keys 
docker ps
cat .ssh/authorized_keys 
ls -l
cat start.sh 
sudo -s
history | grep docker
ls -l
ls -l snap/
docker ps
history | grep yml
sudo -s
exit
cat .ssh/authorized_keys 
exit
sudo -i
exit
sudo -i
exit
docker ps
sudo -i
crontab -l
ls -l /home/
sudo -s
history | grep up
docker ps
sudo -s
history | grep ssl
history | grep docker-compose
sudo -i
exit
sudo -i
exit
sudo -i
exit
sudo -i
history | grep docker-compose
history | grep docker-compose.yml
ls-la /metaqs.bak/
ls -la /metaqs.bak/
ls -la /metaqs/
ls -la /metaqs/main
less /metaqs/main/docker-compose.ssl.yml
exit
sudo -s
sudo -i
exit
docker ps
sudo -i
sudo -i
exit
less /metaqs/main/docker-compose.yml
less /metaqs/main/nginx/nginx.conf.template
cd /metaqs/main/
cd nginx/
ls -la
diff -s nginx.conf.template nginx.conf.template.bak 
vim nginx.conf.template
diff -s nginx.conf.template nginx.conf.template.bak 
vim nginx.conf.template
diff -s nginx.conf.template nginx.conf.template.bak 
exit
sudo -i
exit
less /metaqs/main/nginx/nginx.conf.template
exit
cd /metaqs/main/
ls-la
ls -la
less docker-compose.yml
docker ps
docker stop f227ad757ed9
docker ps
less docker-compose.yml
vim docker-compose.y
vim docker-compose.yml
docker-compose -f docker-compose.yml up -d
docker ps
vim docker-compose.yml
docker-compose -f docker-compose.yml up -d
docker ps
docker logs -f c50e9276424c
docker ps
less docker-compose.yml
cd nginx/
ls -la
less nginx.conf.template
less nginx-ssl.conf.template
vim nginx-ssl.conf.template
history 
cd ..
less init_letsencrypt.sh
docker-compose exec nginx nginx -s reload
docker ps
docker-compose exec -it b28086792c5d sh
sudo -s
cd
ls -la
cat start.sh 
sh start.sh 
sudo -i
cat .ssh/authorized_keys 
vim .ssh/authorized_keys
cat .ssh/authorized_keys 
exit
cat .ssh/authorized_keys 
sudo -i
exit
sudo -i
exit
docker ps
exit
docker ps
apt list --upgradable
docker ps
systemctl list-units --type=service --state=running
man uptime
uptime
exit
sudo -i
exit
sudo -i
exit
sudo -s
reboot
sudo reboot
sudo -s
docker
docker ps
exit
df -h
sudo reboot
df -h
du -sh /var/
sudo -
sudo -i
exit
sudo -i
exit
df -h
ps aux | grep pipe-to
sudo su
cd /metaqs/fastapi/
git status
git diff
ls .git/config 
cat .git/config 
docker inspect --format='{{.LogPath}}' $(docker ps -qa)
du -h $(docker inspect --format='{{.LogPath}}' $(docker ps -qa))
sudo du -h $(docker inspect --format='{{.LogPath}}' $(docker ps -qa))
git log
vim docker-compose.yml 
git diff
ls -la
cat .env.example 
docker-compose ps
docker ps
ls ..
ls ../main/
cat ../main/docker-compose.yml 
cd ../main/
docker-compose ps
git status
git diff
git status
ls -l nginx/certbot/
l .git/config 
cat .git/config 
git log
ls -l
ls -la
cat .env
git status
cat docker-compose.yml 
git status
cat init_letsencrypt.sh
git status
cat nginx/nginx-ssl.conf.template
cat .env
sudo du -h $(docker inspect --format='{{.LogPath}}' $(docker ps -qa))
docker-compose ps
cd /metaqs/main/
git pull
git checkout christopher/update
git stash
git checkout christopher/update
git stash pop
vim init_letsencrypt.sh 
git status
git restore --staged docker-compose.yml
git status
git restore docker-compose.yml
git status
git restore --staged nginx/nginx-ssl.conf.template
vim nginx/nginx-ssl.conf.template 
git restore nginx/nginx-ssl.conf.template
git status
git diff
git restore --staged  init_letsencrypt.sh
git sttaus
git statuts
git status
git diff
docker-compose ps
docker-compose up -d --no-deps metaqs-fastapi
docker-compose up -d --no-deps fastapi
docker-compose ps
docker-compose -v
vim docker-compose.yml 
docker-compose up -d --no-deps fastapi
docker inspect e28dc3c4bc19_metaqs-fastapi
docker inspect metaqs-fastapi
docker inspect metaqs-fastapi | less
du -h
du -h /
df -h 
sudo su
sudo du -h $(docker inspect --format='{{.LogPath}}' $(docker ps -qa))
docker system df
docker-compose ps
sudo su
cat docker-compose.yml 
git stash
git fetch 
git reset --hard origin/christopher/update 
git stash pop
git diff
git fetch 
git stash
git reset --hard origin/christopher/update 
git stash pop
git idff
git diff
df -h
sudo su
git status
git fetch
git stash
git checkout main
git pull
git stash pop
git status
df -h
sudo -s
du -sh
df -h
cd /var/lib/docker/
ls
sudo -s
df -h
exit
sudo -i
exit
sudo -i
exit
sudo -i
exit
sudo -i
exit
lsblk
sudo -i
exit
history 
sudo -i
exit
sudo -i
exit
sudo -i
exit
ls -l
df -h
ls -l
dd if=/dev/zero of=/home/cloud/output bs=128k count=16k
ls -l
ls -lh
rm output 
ls -lh
lsblk
hdparm -tT /dev/vda
sudo hdparm -tT /dev/vda
ls -l
exit
dd if=/dev/zero of=/home/cloud/output bs=1G count=1
ls -lh
rm output 
dd if=/dev/zero of=/home/cloud/output bs=2G count=1
ls -lh
cp output output2
ls -l
ls -lh
rm output*
ls -l
exit
host wirlernenonline.de
cat /etc/resolv.conf 
exit
ls
cd /opt/
ls
sudo -s
exit
sudo reboot
sudo -i
docker ps
exit
sudo -i
exit
sudo -i
exit
sudo -s
htop
exit
sudo -i
exit
sudo -s
ssh cloud@10.254.1.26
exit
ssh borg@10.254.1.41
exit
ls -l
exit
ls -l
sudo mv 8.1.13.3-TIV-TSMBAC-LinuxX86_DEB.tar /root/
ls -l
sudo -i
ls -l
cd /metaqs
ls -l
cd
sudo -i
exit
sudo -i
exit
du -sh /opt/
du -sh /root/
du -sh /etc/
sudo -i
exit
sudo -i
docker ps
exit
sudo -i
exit
sudo -i
exit
sudo -i
exit
sudo reboot
sudo -i
exit
cd /opt/
sudo -s
sudo -i
sudo apt update
sudo -i
exit
sudo -i
ls
ll
cd ..
ll
curl 10.254.1.31:9200/workspace/_search?pretty -o output.txt
curl 10.254.1.31:9200/workspace/_search?pretty -o output.json
curl -XGET "10.254.1.31:9200/workspace/_search?pretty" -o output.txt
curl -XGET "10.254.1.31:9200/workspace/_search?pretty" -o output.json
curl -XGET "10.254.1.31:9200/workspace/_search?pretty" -o output.json -d'
  {
     "query": {
       "match_all": {}
     }
  }'
curl -XGET "10.254.1.31:9200/workspace/_search?pretty&filter_path=hits.hits._source.properties" "q=+properties:ccm:replicationsource" -o output.json
curl -XGET "10.254.1.31:9200/workspace/_search?pretty&filter_path=hits.hits._source -o output.json
curl -XGET "10.254.1.31:9200/workspace/_search?pretty&filter_path=hits.hits._source" -o output.json
curl -XGET "10.254.1.31:9200/workspace/_search?pretty&filter_path=hits.hits._source.properties.ccm:replicationsource.keyword" -o output.json
curl -XGET "10.254.1.31:9200/workspace/_search?pretty&filter_path=hits.hits._source.properties.ccm:replicationsource" -o output.json
docker ps
docker logs ea57
curl -XGET "10.254.1.31:9200/workspace/_search?pretty&filter_path=hits.hits._source.properties" -o output.json
cat start.sh 
sudo -I
sudo apt update
sudo -i
sudo -s
python --version
python3 --version
curl -XGET "10.254.1.31:9200/workspace/_search?pretty&filter_path=hits.hits._source.i18n" -o output_i18n.json
curl -XGET "10.254.1.31:9200/workspace/_search?pretty" -o output.json
curl -XGET "10.254.1.31:9200/workspace/_search?pretty&filter_path=hits.hits._source.properties" -o output_properties.json
curl -XGET "10.254.1.31:9200/workspace/_search?pretty&filter_path=hits.hits._source.properties.ccm:replicationsource" -o output_sources.json
ls
cat start.sh 
curl -XGET "10.254.1.31:9200/workspace/_search"
docker logs ea57
docker logs --help
docker logs ea57 -f
df -h
ls -lah
docker-compose logs
docker logs ea57 --tail
docker logs ea57 -f
docker logs ea57 > docker_log
