import mysql
import mysql.connector
from database.DB_connect import DBConnect


class DAO():
    def __init__(self):
        pass
    @staticmethod
    def getDAOAnni():
        cnx = DBConnect.get_connection()
        cursor = cnx.cursor()
        query = ("select distinct year(date) as anno from go_daily_sales order by anno ASC")
        cursor.execute(query)
        res = []
        result = cursor.fetchall()
        for row in result:
            res.append(row[0])
        return res



    @staticmethod
    def getDAOBrands():
        cnx = DBConnect.get_connection()
        cursor = cnx.cursor()
        query = ("select distinct Product_brand p from go_products order by Product_brand ASC")
        cursor.execute(query)
        res = []
        result = cursor.fetchall()
        for row in result:
            res.append(row[0])
        return res


    @staticmethod
    def getDAODictRivenditori():
        cnx = DBConnect.get_connection()
        cursor = cnx.cursor(dictionary=True)
        query = ("select distinct Retailer_code c, Retailer_name n from go_retailers order by Retailer_name ASC")
        cursor.execute(query)

        rows = cursor.fetchall()
        res = {}
        for row in rows:
            res[row["c"]] = row["n"]
        print(res)
        return res
        cnx.close()
        return res
