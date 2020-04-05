/redis-5.0.7/src/redis-server &
rm /data/twistd.pid
cd /data
alembic upgrade head
scrapyd
