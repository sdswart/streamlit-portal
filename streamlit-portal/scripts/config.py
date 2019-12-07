import os
from os import environ
basedir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

class Config(object):
    DEBUG=os.environ.get('SP_DEBUG', 'true')=='true'
    HOST=os.environ.get('SP_HOST', '0.0.0.0')
    PORT=int(os.environ.get('SP_PORT', 5858))
    SECRET_KEY =os.environ.get('SP_SECRET_KEY', 'c)fq%he^v4^tmxnl(0=29zsydgi@^z4%6oq63n@4w^yip2-yg2')
    BASE_PATH=os.environ.get('SP_BASEPATH',"/st")
    INSTANCE_PATH=os.path.join(basedir,os.environ.get('SP_INSTANCE_PATH',"instance"))
    STATIC_URL=os.environ.get('SP_STATIC_URL',"/static")
    TEMPLATES_PATH=os.path.join(basedir,os.environ.get('SP_TEMPLATES_PATH',"templates"))

    PORTS=list(range(5000,9000))
