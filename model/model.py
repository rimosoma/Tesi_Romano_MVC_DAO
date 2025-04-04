from database.DAO import DAO


class Model:
    def __init__(self):
        pass

    def getAnni(self):
        return DAO().getDAOAnni()

    def getBrands(self):
        return DAO.getDAOBrands()

    def getRivenditori(self):
        return DAO.getDAODictRivenditori()


    def getMiglioriModel(self,anno,brand,rivenditore ):
        return DAO.getDAOMigliori(anno,brand,rivenditore)


    def getAnalisiModel(self,anno,brand,rivenditore ):
        return DAO.getDAOAnalisi(anno,brand,rivenditore)