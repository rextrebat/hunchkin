Setup of typical Hunchkin server
================================

Software Setup
--------------

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

- Python virtualenv::


Installation Steps
-----------------

1. Make /var/log/hunchkin::
    sudo mkdir /var/log/hunchkin
    sudo chown glasscat:glasscat /var/log/Hunchkin

#. Create /etc/hunchkin.conf::
    [environment]
    env=PROD

#. Copy solr binary and indexes::

#. 


