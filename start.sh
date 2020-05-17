/redis-5.0.7/src/redis-server &
rm /data/twistd.pid
cd /data
alembic -c migrations/wildsearch/alembic.ini upgrade head
alembic -c migrations/ozon/alembic.ini upgrade head
scrapyd
