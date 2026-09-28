#!/bin/bash

set -e

cd ~ || exit

sudo apt update && sudo apt install redis-server libcups2-dev mariadb-client

pip install frappe-bench

git clone https://github.com/frappe/frappe --branch version-16 --depth 1
bench init --skip-assets --frappe-path ~/frappe --python "$(which python)" frappe-bench

mariadb --host 127.0.0.1 --port 3306 -u root -proot -e "SET GLOBAL character_set_server = 'utf8mb4'"
mariadb --host 127.0.0.1 --port 3306 -u root -proot -e "SET GLOBAL collation_server = 'utf8mb4_unicode_ci'"

mariadb --host 127.0.0.1 --port 3306 -u root -proot -e "FLUSH PRIVILEGES"

cd ~/frappe-bench || exit

sed -i 's/watch:/# watch:/g' Procfile
sed -i 's/schedule:/# schedule:/g' Procfile
sed -i 's/socketio:/# socketio:/g' Procfile
sed -i 's/redis_socketio:/# redis_socketio:/g' Procfile

bench get-app erpnext --branch version-16
bench get-app hrms --branch version-16
bench get-app working_time "${GITHUB_WORKSPACE}"

bench setup requirements --dev

bench new-site --db-root-password root --admin-password admin test_site --install-app erpnext
bench --site test_site install-app hrms
bench --site test_site install-app working_time

CI=Yes bench build --production

bench start &> bench_start.log &
