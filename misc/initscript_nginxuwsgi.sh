#!/bin/sh

# Initialize users and priuileges
echo $1

if [ $1 = "install" ]
  then
    apt-get update
    apt-get -y install nginx php5 sqlite3 php5-sqlite
    a2enmod rewrite
    apt-get -y install python-dev python3 python-setuptools
    apt-get -y install swig libfuse-dev libusb-dev php5-dev
    apt-get -y install i2c-tools python-smbus
    apt-get -y install hostapd
    apt-get -y install isc-dhcp-server
    update-rc.d -f isc-dhcp-server remove
    update-rc.d -f apache2 remove

    easy_install pip

    pip install rpi.gpio
    apt-get -y install python-serial
    apt-get -y install python-gtk2
    apt-get -y install automake
    apt-get install nginx
    apt-get install uwsgi
    apt-get install python-pip
    apt-get install php5-fpm
fi

if [ $1 = "update" ]
    then
      echo "updated only, as requested"
else
    echo "Configuring users and directories"
    mkdir /usr/lib/iicontrollibs
    chown -R root:pi /usr/lib/iicontrollibs
    chmod -R 775 /usr/lib/iicontrollibs

    mkdir /var/wwwsafe
    chown -R root:pi /var/wwwsafe
    chmod -R 775 /var/wwwsafe

    mkdir /var/www
    chown -R root:www-data /var/www
    chmod -R 775 /var/www

    mkdir /usr/lib/cgi-bin
    chown -R root:www-data /usr/lib/cgi-bin

    mkdir /var/log/cupid
    chgrp -R pi /var/log/cupid
    chmod ug+s /var/log/cupid
    chmod -R 775 /var/log/cupid

    mkdir /var/1wire

    addgroup sshers
    usermod -aG sshers pi
    usermod -aG www-data pi

    useradd websync
    usermod -aG sshers websync
    usermod -aG www-data websync
    echo "complete"

    echo "Configuring sshd"
    #       Add to sshd_config: AllowGroups sshers
    testresult=$(grep -c 'AllowGroups' /etc/ssh/sshd_config)
    if [ ${testresult} -ne 0 ]
      then
        echo "Groups ssh already configured"
    else
      echo "AllowGroups sshers" >> /etc/ssh/sshd_config
    fi
    echo "complete"


    echo "Initializing web library repo"
    cd /var/www
    rm -R *
    git init .
    git config --global user.email "info@interfaceinnovations.org"
    git config --global user.name "iinnovations"
    git remote add origin https://github.com/iinnovations/cupidweblib
    chown -R pi:www-data .git
    chmod -R 775 .git
    git reset --hard master
    git pull origin master
    chown -R pi:www-data *
    chmod -R 775 *
    echo "complete"


    echo "Initializing control libraries repo"
    cd /usr/lib/iicontrollibs
    rm -R *
    git init .
    git config --global user.email "info@interfaceinnovations.org"
    git config --global user.name "iinnovations"
    git remote add origin https://github.com/iinnovations/iicontrollibs
    chown -R pi:www-data .git
    chmod -R 775 .git
    git reset --hard master
    git pull origin master
    chown -R pi:www-data *
    chmod -R 775 *
    echo "complete"

    echo "Creating default databases"
    /usr/lib/iicontrollibs/cupid/rebuilddatabases.py DEFAULTS
    echo "Complete"

    echo "Copying boot script"
    cp /usr/lib/iicontrollibs/misc/rc.local /etc/
    echo "complete"

    echo "Updating crontab"
    crontab /usr/lib/iicontrollibs/misc/crontab
    echo "complete"

    echo "Copying inittab"
    cp /usr/lib/iicontrollibs/misc/inittab /etc/
    echo "Complete"

    echo "Copying cmdline.txt"
    cp /usr/lib/iicontrollibs/misc/cmdline.txt /boot/
    echo "Complete"

    echo "Copying nginx site"
    cp /usr/lib/iicontrollibs/misc/nginx/nginxsite /etc/apache2/sites-available/default
    echo "Complete"

    echo "Creating self-signed ssl cert"
    opensslreq -new -x509 -days 365 -nodes -out /etc/ssl/localcerts/mycert.pem -keyout /etc/ssl/localcerts/mycert.key
    echo "Complete"

    echo "Copying dhcpd.conf"
    cp /usr/lib/iicontrollibs/misc/dhcpd.conf /etc/dhcp/
    echo "Complete"


    testresult=$(/opt/owfs/bin/owfs -V | grep -c '2.9p5')
    if [ ${testresult} -ne 0 ]
      then
        echo "owfs 2.9p5 already installed"
    else
        echo "installing owfs 2.9p5"
        cd /usr/lib/iicontrollibs/resource
        tar -xvf owfs-2.9p5.tar.gz
        cd /usr/lib/iicontrollibs/resource/owfs-2.9p5
        ./configure
        make install
        cd ..
        rm -R owfs-2.9p5
    fi
    echo "complete"

    if [ $(ls /usr/sbin/ | grep -c 'hostapd.edimax') -ne 0 ]
        then
            echo "hostapd already configured"
    else
        echo "copying hostapd"
        mv /usr/sbin/hostapd /usr/sbin/hostapd.bak
        cp /usr/lib/iicontrollibs/resource/hostapd.edimax /usr/sbin/hostapd.edimax
        ln -sf /usr/sbin/hostapd.edimax /usr/sbin/hostapd
        chown root:root /usr/sbin/hostapd
        chmod 755 /usr/sbin/hostapd
        echo "hostapd configuration complete"
    fi

    echo "copying hostapd.conf"
    cp /usr/lib/iicontrollibs/misc/hostapd.conf /etc/hostapd/

    echo "copying blacklist file"
    cp /usr/lib/iicontrollibs/misc/raspi-blacklist.conf /etc/modprobe.d/

    echo "setting modprobe"
    modprobe i2c-bcm2708

    echo "coping boot config to enable serial interfaces"
    cp /usr/lib/iicontrollibs/misc/config.txt /boot/

    echo "installing gpio-admin"
    cd /usr/lib/iicontrollibs/resource/quick2wire-gpio-admin-master/
    make
    make install

    echo "installing python-api-master"
    cd /usr/lib/iicontrollibs/resource/quick2wire-python-api-master/
    ./setup.py install

    echo "installing spi-dev"
    cd /usr/lib/iicontrollibs/resource/py-spidev/
    ./setup.py install

    echo "installing bitstring"
    cd /usr/lib/iicontrollibs/resource/bitstring/
    ./setup.py install

    echo "Copying icons to desktop"

    echo "Changing desktop wallpaper"
    sudo -u pi pcmanfm -w /var/www/images/splash/cupid_splash_big.png

    echo "Copying icons"
    cp /usr/lib/iicontrollibs/misc/updatecupidweblibs.desktop /

fi