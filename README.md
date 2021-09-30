# Instructions

## Setting up virtual environment

- `virtualenv venv -p python3`
- `source venv/bin/activate`
- `pip install -r requirements.txt`

## check installation
- `scrapy list`

## spider execution
- `scrapy crawl [spider_name] --logfile=[spider_name] -o [spider_name].json`