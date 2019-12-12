from sp.app import app
from sp.config import Config

if __name__ == "__main__":
    app.run(host=Config.HOST,port=Config.PORT,debug=Config.DEBUG)
