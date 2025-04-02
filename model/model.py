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