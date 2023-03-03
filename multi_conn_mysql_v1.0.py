#!/usr/bin/python3
"""
connectionpool的自动重连机制，在数据库能无缝切换至其他可以写入的主节点时
有用，如果HA故障切换需要时间（mha的主从模式），哪怕是30秒，则应用程序必须加入自动重连的代码，
比如本程序的tryexcept部分。
而不是完全交给连接池，连接池会自动重连，但是故障切换前，老的主节点已经宕机，
则虽然重连也连不上，故还是会报错并退出当前连接。
如果要重新获取连接，得应用程序再次调用connection，再次申请连接。
create table t_gr1(id int(10), name varchar(10),ct_time datetime,primary key (id));
"""
import MySQLdb
import datetime
import pytz
from DBUtils.PooledDB import PooledDB
import threading
import sys
import getopt
import os
import config_file as cfg_file

HOST='auroraupgrade2111stack-mysqlaurora2090fc5f6149-kdgrvvkh4rgy.cluster-c6ckc34cbthe.ap-northeast-1.rds.amazonaws.com '

tz = pytz.timezone('Asia/Shanghai')
def now_time():
    #now = time.localtime(time.time())
    #for_now = time.strftime('%Y-%m-%d %H:%M:%S',now)
    for_now = datetime.datetime.now(tz).strftime("%Y-%m-%d %H:%M:%S")
    return for_now
#pool connects proxy
DBPARAMS = {'creator':MySQLdb,
            'host':HOST, #blue cluster endpoint
            'user':'admin',
            'passwd':'Welcome#123456',
            'db':'grdb',
            'port':3306,
            'mincached':2,
            'maxcached':20,
            'maxshared':5,
            'maxconnections':50,
            'blocking':True,
            'ping':1
}
pool = PooledDB(**DBPARAMS)

#parse the parametes input from command line
#@staticmethod
def args_parse():
    argv = sys.argv[1:]
    try:
        defined_options, unamed_args = getopt.getopt(argv, "ht:r:", ["help", "thread=", "rows="])
        #print("args:",defined_options)
        for opt, arg in defined_options:
            if opt in ['-t', '--thread']:
                threads = arg
            elif opt in ['-r', '--rows']:
                rows = arg
            elif opt in ['h', '--help']:
                print("Help: \n --thread=2: it will fork 2 threads to run;\n --rows=1000: Insert 1000 items in each thread")
                exit()
            else:
                print("Options input is not valid, please input option --help to get details")
                exit()
        return threads, rows
    except:
        print("Options input error, please input option --help to get details")
        exit()

#query max primary key from msyql
def query_table_maxID(pool):
    conn = pool.connection()
    cur = conn.cursor()
    cur.execute('select max(id) from t_gr1')
    rc = cur.fetchone()
    #print(rc)
    cur_maxValue = rc[0]
    if cur_maxValue is None:
        cur_maxValue = 0
    return int(cur_maxValue)

#insert data into mysql
def dml_mysql_table(start_key: int, range_value: int, pool):
    t_name = threading.current_thread().name
    for i in range(start_key, start_key + range_value):
        format_now = now_time()
        print ("%s handle the key %s, %s" % (t_name,i,format_now))
        try:
            conn = pool.connection()
            if i%3 == 1 or i%3 == 2:
                #time.sleep(1)
                cur = conn.cursor()
                #insert data
                cur.execute('insert into t_gr1(id,name,ct_time) values(%s,%s,%s)',(i,'maxscale',format_now))
                conn.commit()
            elif i%3 == 0:
                cur = conn.cursor()
                #update data
                j = i - 4
                cur.execute('update t_gr1 set name=%s,ct_time=%s where id=%s',('proxy',format_now,j))
                conn.commit()
            cur.close()
            conn.close()
        #if exception, close old connection; and in 'try', reconnect,then execute sql.
        except MySQLdb.MySQLError as e:
            print ("%s, MySQLError: %s" % (t_name, e))
            conn.close()
        except MySQLdb.OperationalError as e:
            print ("%s, OperationalError: %s" % (t_name, e))
            conn.close()
        except MySQLdb.NotSupportedError as ex:
            print ("%s, NotSupportedError: %s" % (t_name, ex))
            conn.close()
        i = i+1
    print ("Finish msg: %s finished. %s" % (t_name, now_time()))

def make_print_to_file(path='./'):
    '''
    path， it is a path for save your log about fuction print
    example:
    use  make_print_to_file()   and the   all the information of funtion print , will be write in to a log file
    :return:
    '''
    class Logger(object):
        def __init__(self, filename="Default.log", path="./"):
            self.terminal = sys.stdout
            self.log = open(os.path.join(path, filename), "a", encoding='utf8',)
 
        def write(self, message):
            self.terminal.write(message)
            self.log.write(message)
 
        def flush(self):
            pass
    fileName = "test_mysql_" + datetime.datetime.now(tz).strftime("%Y%m%d%H%M")
    sys.stdout = Logger(fileName + '.log', path=path)

    print(fileName.center(60,'*'))
 
if __name__ == '__main__':
    args = args_parse()
    cur_dir = os.getcwd()
    make_print_to_file(path=cur_dir)
    print ("########We start! %s" % (now_time())) 
    cur_maxID = query_table_maxID(pool)
    print("maxID:", cur_maxID)
    threads = int(args[0])
    rows = int(args[1])
    print("User started threads: %s, rows_per_thread: %s" % (args[0], args[1]))
    #start multi thread to handle db query
    for i in range(1, threads + 1):
        startKey = cur_maxID + 1
        t = threading.Thread(target=dml_mysql_table, args=(startKey, rows, pool))
        t.start()
        cur_maxID = cur_maxID + rows
