class Dipendente:
    def __init__(self, id, daIncludere,in_vacation, nome, cognome,nrNotti , nrMattini, nrPomeriggi ):
        self.id = id                        #letto dal db
        self.daIncludere = daIncludere
        self.has_vacation = in_vacation  # booleano inizializzato al valore nel db
        self.nome = nome                    #letto dal bd
        self.cognome = cognome              #letto dal db
        self.notti = nrNotti
        self.mattini = nrMattini
        self.pomeriggi = nrPomeriggi
        self.necessita = []




    def setNotti(self, notti):
        self.notti = notti
        #print(self.nome, self.cognome, self.notti, self.mattini, self.pomeriggi)

    def setMattini(self, mattini):
        self.mattini = mattini

    def setPomeriggi(self, pomeriggi):
        self.pomeriggi = pomeriggi

