import os
from os import environ
basedir = os.path.abspath(os.path.dirname(__file__))

class Config(object):
    DEBUG=True
    HOST='0.0.0.0'
    PORT=5001
    SECRET_KEY ='c)fq%he^v4^tmxnl(0=29zsydgi@^z4%6oq63n@4w^yip2-yg2'
    BASE_PATH="/st"

    PORTS=list(range(5000,9000))
