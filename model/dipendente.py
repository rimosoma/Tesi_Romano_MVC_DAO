class Dipendente:
    def __init__(self, id, nome, cognome, in_vacation):
        self.id = id                        #letto dal db
        self.nome = nome                    #letto dal bd
        self.cognome = cognome              #letto dal db
        self.has_vacation = in_vacation     #booleano inizializzato al valore nel db
