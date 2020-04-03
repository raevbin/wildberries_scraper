# wildberries scraper

Сканер для сбора сведений о товарах с https://www.wildberries.ru


## Установка

1. Должен быть установлен docker
2. Загрузить репозиторий в папку wondersell_scraper
3. Отредактировать файл wondersell_scraper/proxy_list.csv , добавив туда несколько прокси серверов. Например:
```
protocol;ip;port;login;passoword
socks;83.217.11.126;2324;sdfgdsfg;asdfhjkasl
socks;185.58.204.145;4555;sdfert;dfghwr
socks;185.211.246.79;4664;sdfgs;andfgdhsrew
```

4. Установка:

```sh
$ cd wondersell_scraper
$ docker-compose build
```
5. Запуск:
```sh
$ docker-compose up
```
после удачного запуска можно подключиться в контейнеру
для этого в новом терминале!:
```sh
$ docker exec -it wondersellscraper_scrab_1 bash
```
должно появиться приглашение на подобии
```sh
root@f96349b4e0d9:/data#
```
## Работа
(все команды выполняются в контейнере)
1. Для начала нужно проверить прокси сервера
```sh
# scrapy crawl proxy_test
```
! при первом запуске после создания контейнера могут появиться ошибки:
(Error occurred during fetching http://useragentstring.com/pages/useragentstring.php?name=Chrome
...
socket.timeout: timed out)
но при этом все должно работать штатно и при повторе такого быть не должно.
в результат увидим количество рабочих прокси
(по умолчанию программа выбирает только протокол socks!)
Более подробно о параметрах сканеров - в разделе "Параметры"

```sh
....
[2020-04-03 10:37:33,218][INFO] count proxy : 3
```
если count proxy > 0 , можно работать дальше

2. Сканирование каталога
```sh
# scrapy crawl catalog
```
после завершения сканер печатает статистику. например:
```sh
stat:
{
    "downloader/request_bytes": 1012,
    "downloader/request_count": 3,
    "downloader/request_method_count/GET": 3,
    "downloader/response_bytes": 5282,
    "downloader/response_count": 3,
    "downloader/response_status_count/200": 3,
    "elapsed_time_seconds": 6.515392,
    "finish_reason": "finished",
    "finish_time": "2020-04-03T10:37:33.216861",
    "log_count/DEBUG": 1,
    "log_count/INFO": 15,
    "memusage/max": 69128192,
    "memusage/startup": 69128192,
    "response_received_count": 3,
    "scheduler/dequeued": 3,
    "scheduler/dequeued/memory": 3,
    "scheduler/enqueued": 3,
    "scheduler/enqueued/memory": 3,
    "start_time": "2020-04-03T10:37:26.701469"
}
```
3. Теперь можно сканировать товары

```sh
# scrapy crawl wb -a catalog_ids=endpoints -a limit=1
```
эта команда возьмет одну категорию и соберет все товары из нее.
Прервать процесс сканирования: Cntl+c (Внимание! после одного нажатия процесс еще будет продолжаться некоторое время. Нужно дождаться отчета!)

4. Сбор цен и остатков
```sh
# scrapy crawl wb_cost -a item_ids=all
```
этот сканер тоже можно остановит Cntl+c

5. Доступ к базе.

По умолчанию подключена база sqlite
введите
```sh
# sqlite3 ./sql_db/wildsearch.db
```
приглашение:
```sh
SQLite version 3.27.2 2019-02-25 16:06:06
Enter ".help" for usage hints.
sqlite>
```
используйте стандартные команды sql, например:
```sh
sqlite> SELECT id, url FROM catalog limit 10;
```

## Параметры
### Сканеры
все сканеры основаны на фреймворке Scrapy. Большинство параметров можно почитать в официальной документации. Здесь приводятся только специфические для проекта.

#### # scrapy crawl catalog
сканирует и собирает url-ы всех категорий
- запускается без специальных параметров
- остановка на паузу не возможна

особенности работы:
.... <текст готовится к публикации>

#### # scrapy crawl wb
сканирует и собирает общую информацию о товарах
- без параметров не сканирует
- *-a item_ids* (=[1,2,3],[4-10]|all)
принимает id товара через запятую и диапазоном или *all* например:
```sh
# scrapy crawl wb -а item_ids=1,2,3,4,25-50,100-500
# scrapy crawl wb -а item_ids=all
```
- *-a catalog_ids* (=[1,2,3],[4-10]|all|endpoints)
по аналогии с item_ids, но вместо *all* рекомендую использовать *endpoints*
- *-a limit* (=1)
используется для тестирования
- возможны комбинации
- поддерживает установку на паузу

особенности работы:
.... <текст готовится к публикации>

#### # scrapy crawl wb_cost
принимает параметры по аналогии с *scrapy crawl wb*
только без *endpoints* для *catalog_ids* и без *limit*


особенности работы:
.... <текст готовится к публикации>

#### # scrapy crawl proxy_test
Загружает прокси сервера, тестирует их и ставит в очередь "ротатора". Если прокси не отвечает, то автоматически удаляется из очереди.
- можно запускать без параметров
    .... <текст готовится к публикации>
        - source
        - mode
        - protocol
        - group

### Использование паузы
сканеры *wd* и *wd_cost* поддерживают установку на паузу.
если планируется прерывание скрипта с возможностью продолжения нужно добавить параметр
- *-s JOBDIR (=<path>)*
<path> - путь к каталогу с архивом экземпляра сканера
например:
```sh
# scrapy crawl wb -a catalog_ids=endpoints -s JOBDIR=crawls/wb_1
```
эта команда создаст папку архива в корне директории.
если остановить такой сканер, то можно потом продолжить введя команду с тем же архивом.
Внимание! Остановка сканера (с помощь Cntl+c) не завершат процесс сразу. Сканер еще некоторое время работает сохраняя результаты. Если нажать Cntl+c повторно, это прервет работу сканера и повредит архив, что сделает невозможным продолжить с того же места.

### Настройки

#### Подключение MySql
.... <текст готовится к публикации>
#### Настройки задержки и скорости сканирования
.... <текст готовится к публикации>

#### Сервис Scylla
автоматически поиск публичных прокси серверов
.... <текст готовится к публикации>
 
