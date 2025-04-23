import pymysql

db = pymysql.connect(
	host='localhost',
    port=3306,
    user='root',
    passwd='your password',
    db='your database name',
    charset='utf8'
 )