import mysql

from database.DB_connect import DBConnect


class DAO():
    def __init__(self):
        pass

    def getDAOAnni(self):
        cnx = mysql.connector.connect()
        cursor = cnx.cursor()
        #query = ("select distinct year(date) as anno from go_dayly_sales order by anno ASC")
        cursor.execute(query)

    def getDAOBrands(self):
        cnx = mysql.connector.connect()
        cursor = cnx.cursor()
        #query = ("select distinct Product_brand p from go_products order by Product_brand ASC")
        cursor.execute(query)



    def getDAORivenditori(self):
        cnx = mysql.connector.connect()
        cursor = cnx.cursor()
        #query = ("select distinct Retailer_name p from go_retailers order by Retailer_name ASC")
        cursor.execute(query)