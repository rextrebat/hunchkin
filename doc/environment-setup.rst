Setup of typical Hunchkin server
================================

Software Setup
--------------

- Java::
    sudo apt-get install openjdk-7-jre-headless

- Solr
  For now, not installing solr but tar.gz of entire solr install copied over

- MySQL::
    sudo apt-get install mysql-server
  (root password, same as root for box)

- Memcache::
    sudo apt-get install memcached

- RabbitMQ::
    sudo apt-get install rabbitmq-server

- Python virtualenvwrapper::
    sudo apt-get install virtualenvwrapper

- Mongo DB (not used any more)::
    sudo apt-get install mongodb


Installation Steps
-----------------

1. Make /var/log/hunchkin::
    sudo mkdir /var/log/hunchkin
    sudo chown glasscat:glasscat /var/log/Hunchkin

#. Create /etc/hunchkin.conf::
    [environment]
    env=PROD

#. Create /opt/hunchkin

#. Copy solr binary and indexes and untar in /opt

#. DB - set root password to box root password

#. DB - create database hotel_genome, user: appuser

#. DB - dump db using mysqldump and copy over

#. DB - load dump into hotel_genome database

#. Python environment Setup::
    mkvirtualenv emeraldcity

#. Install all packages in virtualenv::
    sudo apt-get install python-dev
    sudo apt-get install libmysqlclient-dev
    easy_install -U distribute
    sudo apt-get install libxml2-dev libxslt1-dev
    sudo apt-get install libamd2.2.0 libblas3gf libc6 libgcc1 libgfortran3 liblapack3gf libumfpack5.4.0 libstdc++6 build-essential gfortran libatlas-base-dev python-all-dev
    sudo apt-get install libevent-dev
    sudo apt-get install libpng12-dev libfreetype6-dev
    sudo apt-get install libmemcached-dev
    pip install -r py-reqs.txt

#. Create app directory::
    mkdir /opt/hunchkin

#. Clone the hunchkin application::
    git clone kdasgupta@99.30.170.123:/home/kdasgupta/workspace/hotelgenome/
