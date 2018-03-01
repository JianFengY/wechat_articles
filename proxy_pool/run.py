from proxy_pool.api import app
from proxy_pool.schedule import Schedule

def main():

    s = Schedule()
    s.run()
    app.run()




if __name__ == '__main__':
    main()

