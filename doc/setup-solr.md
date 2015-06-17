Setting up Solr
===============

Ref: http://hadooptutorial.info/apache-solr-installation-on-ubuntu/

sudo apt-get -y install openjdk-7-jdk

sudo apt-get -y install tomcat7 tomcat7-admin

sudo vi /etc/tomcat7/tomcat-users.xml

Add:
<role rolename="manager-gui" />
<user username="admin" password="rextrebat" roles="manager-gui" />

Download solr binary from http://lucene.apache.org/solr/

sudo mkdir /opt/solr
sudo mv solr-4.10.3.tgz /opt/solr/
sudo cd /opt/solr; tar zxvf solr-4.10.3.tgz
sudo cp /opt/solr/solr-4.10.3/example/webapps/solr.war /opt/solr/solr-4.10.3/example/multicore/

sudo cp -r /opt/solr/solr-4.10.3/example/lib/ext/* /usr/share/tomcat7/lib/
sudo cp -r /opt/solr/solr-4.10.3/example/resources/log3j.properties /usr/share/tomcat7/lib/

vi /etc/tomcat7/Catalina/localhost/solr.xml

Add:

<Context docBase="/usr/lib/solr/solr-4.10.2/example/multicore/solr.war" debug="0" crossContext="true">
  <Environment name="solr/home" type="java.lang.String" value="/usr/lib/solr/solr-4.10.2/example/multicore" override="true" />
</Context>

sudo chown -R tomcat7:tomcat7 /opt/solr/solr-4.3.10/example

sudo service tomcat7 restart
