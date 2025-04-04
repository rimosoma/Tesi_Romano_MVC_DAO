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
        cnx.close()
        return res

    @staticmethod
    def getDAOMigliori(anno,brand,rivenditore):
        cnx = DBConnect.get_connection()
        cursor = cnx.cursor(dictionary=True)        #non serve
        query =("SELECT v.Product_number,r.Retailer_code , p.Product_brand , v.unit_sale_price, v.quantity,(v.unit_sale_price * v.quantity) AS ricavo,v.Date"
                "FROM go_daily_sales v"
                "JOIN go_products p ON v.Product_number = p.Product_number"
                "JOIN go_retailers r ON v.Retailer_code = r.Retailer_code"
                "WHERE"
                "(%s IS NULL OR EXTRACT(YEAR FROM v.data_vendita) = %s)"
                "AND (%s IS NULL OR v.codiceRivenditore = %s)"
                "AND (%s IS NULL OR p.brand = %s)"
                "ORDER BY ricavo DESC"
                "LIMIT 5;")
        cursor.execute(query, (anno, anno,rivenditore, rivenditore,brand, brand,))
        rows = cursor.fetchall()
        res = []
        for row in rows:
            res.append([f"Data: {row["Date"]}", f"Ricavo: {row["ricavo"]}", f"Prodotto: {row["Product_number"]}", f"Rivenditore: {row["Retailer_code"]}"])
        cnx.close()
        return res

    @staticmethod
    def getDAOAnalisi(anno,brand,rivenditore):
        cnx = DBConnect.get_connection()
        cursor = cnx.cursor(dictionary=True)
        query = ("SELECT SUM(v.unit_sale_price * v.quantity) AS giro_affari, "
                "COUNT(*) AS numero_vendite, "
                "COUNT(DISTINCT v.Retailer_code) AS numero_rivenditori,"
                "COUNT(DISTINCT v.Product_number) AS numero_prodotti "
                "FROM go_daily_sales v "
                "JOIN go_products p ON v.Product_number = p.Product_number "
                "WHERE (%s IS NULL OR EXTRACT(YEAR FROM v.data_vendita) = %s) "
                "AND (%s IS NULL OR v.codiceRivenditore = %s) "
                "AND (%s IS NULL OR p.brand = %s);")


        cursor.execute(query, (anno, anno, rivenditore, rivenditore,brand, brand))
        rows = cursor.fetchall()
        res = []
        for row in rows:
            res.append("Statistiche Vendite:")
            res.append(f"Giro d'affari = {row["giro_affari"]}")
            res.append(f"Nr vendite = {row["numero_vendite"]}")
            res.append(f"Nr Rivenditori coinvolti = {row["numero_rivenditori"]}")
            res.append(f"Nr Prodotti coinvolti = {row["numero_prodotti"]}")
        cnx.close()
        return res