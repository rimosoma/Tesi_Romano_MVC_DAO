import calendar


class Dipendente:
    def __init__(self, id_dip, da_includere, has_vacation, nome, cognome, contratto, nrNotti_settimanali,
                 nrMattini_settimanali, nrPomeriggi_settimanali):
        self.id = id_dip
        self.daIncludere = da_includere  # Booleano: True/False
        self.has_vacation = has_vacation  # Booleano: True se ha ferie accumulate
        self.nome = nome
        self.cognome = cognome
        self.tipoContratto = contratto

        # Monte ore settimanale (calcolato in base al contratto)
        self.monteOreSettimanale = self._calcola_monteore_settimanale(self.tipoContratto)

        # Esigenze settimanali per tipo di turno (dal DB o UI, non inizializzate a 0)
        # Questi sono i NUMERI DI TURNI che il dipendente DEVE fare a settimana
        self.esigenzeNottiSettimanali = nrNotti_settimanali
        self.esigenzeMattiniSettimanali = nrMattini_settimanali
        self.esigenzePomeriggiSettimanali = nrPomeriggi_settimanali

        # Dizionario per le necessità giornaliere (sarà riempito esternamente)
        self.dizionarioNecessita = None

        # --- Nuovi attributi per la logica di assegnazione dei turni ---
        self.turniAssegnatiMese = {}  # {giorno_del_mese: 'tipo_turno_assegnato'} es: {1: 'mat_1', 2: 'riposo'}
        self.oreLavorateMese = 0.0  # Contatore delle ore lavorate nel mese corrente
        self.giorniLavoratiConsecutivi = 0  # Contatore per il vincolo dei riposi
        self.riposiPresiSettimana = 0  # Contatore dei riposi per la settimana corrente
        self.turniFattiSettimana = {  # Contatori per le esigenze settimanali
            "notti": 0,
            "mattini": 0,
            "pomeriggi": 0,
            "mj": 0,
            "pc": 0
        }

    def _calcola_monteore_settimanale(self, tipoContratto):
        if tipoContratto == "FTN":  # Full Time
            return 38
        elif tipoContratto == "PTN":  # Part Time (potrebbe essere generico)
            return 30
        elif tipoContratto == "PTL":  # Part Time (Light?)
            return 28
        # Aggiungi un default o solleva un errore se il contratto non è riconosciuto
        return 0  # o raise ValueError("Tipo contratto non riconosciuto")

    def setDizionario(self, dizionario):
        self.dizionarioNecessita = dizionario
        # print(f"Per {self.nome} {self.cognome} il dict necessità è stato creato")

    # Metodi per impostare le esigenze settimanali (se non vengono lette direttamente dal DB)
    def setEsigenzeNotti(self, notti):
        self.esigenzeNottiSettimanali = notti

    def setEsigenzeMattini(self, mattini):
        self.esigenzeMattiniSettimanali = mattini

    def setEsigenzePomeriggi(self, pomeriggi):
        self.esigenzePomeriggiSettimanali = pomeriggi

    def setDaIncludere(self, daIncludere):
        self.daIncludere = daIncludere
        print(self.nome, self.cognome, self.esigenzeNottiSettimanali, self.esigenzeMattiniSettimanali, self.esigenzePomeriggiSettimanali, self.daIncludere)

    # --- Metodi per la gestione interna dei conteggi durante l'assegnazione ---
    def resetContatoriSettimanali(self):
        """Azzera i contatori di turni e riposi per una nuova settimana."""
        self.riposiPresiSettimana = 0
        self.turniFattiSettimana = {
            "notti": 0,
            "mattini": 0,
            "pomeriggi": 0,
            "mj": 0,
            "pc": 0
        }

    def aggiungiTurno(self, giorno: int, tipo_turno: str, ore: float):
        """Aggiunge un turno al dipendente per un dato giorno."""
        self.turniAssegnatiMese[giorno] = tipo_turno
        self.oreLavorateMese += ore

        # Aggiorna i contatori settimanali
        if tipo_turno in self.turniFattiSettimana:
            self.turniFattiSettimana[
                tipo_turno.replace("mat_", "").replace("pom_", "")] += 1  # Conta mattini, pomeriggi, notti, mj, pc

        # Aggiorna i giorni lavorati consecutivi
        if tipo_turno in ["riposo", "ferie", "mutua", "permesso", "non_retribuita"]:
            self.giorniLavoratiConsecutivi = 0
            self.riposiPresiSettimana += 1
        else:
            self.giorniLavoratiConsecutivi += 1

    def rimuoviUltimoTurno(self, giorno: int, tipo_turno: str, ore: float):
        """Rimuove l'ultimo turno assegnato (per backtracking)."""
        if giorno in self.turniAssegnatiMese:
            del self.turniAssegnatiMese[giorno]
            self.oreLavorateMese -= ore

            if tipo_turno in self.turniFattiSettimana:
                self.turniFattiSettimana[tipo_turno.replace("mat_", "").replace("pom_", "")] -= 1

            # NOTA: La logica di giorniLavoratiConsecutivi e riposiPresiSettimana
            # è più complessa da "disfare" con il pop.
            # Sarà più semplice ricalcolarla o gestirla esternamente nel backtracking
            # quando si prova un giorno intero, piuttosto che sul singolo turno.
            # Per ora, la lasciamo così, ma potrebbe necessitare di revisione.
            # Se un turno è rimosso, dobbiamo ricalcolare lo stato precedente
            # dei giorni lavorati consecutivi/riposi della settimana.
            # Per il backtracking, è più robusto azzerare i contatori per il giorno
            # e poi ri-assegnare/ricontare per le prove alternative.

    def ripristinaTurni(self):
        """
        Ripristina le esigenze settimanali predefinite per il dipendente
        in base al suo tipo di contratto.
        """
        print(f"DEBUG: Ripristino esigenze settimanali per {self.nome} {self.cognome} (ID: {self.id})")
        if self.tipoContratto == "FTN":
            self.esigenzeMattiniSettimanali = 2  # Usa il setter della proprietà
            self.esigenzePomeriggiSettimanali = 3  # Usa il setter della proprietà
            self.esigenzeNottiSettimanali = 0  # Usa il setter della proprietà
        elif self.tipoContratto == "PTN":
            self.esigenzeMattiniSettimanali = 2
            self.esigenzePomeriggiSettimanali = 2
            self.esigenzeNottiSettimanali = 0
        elif self.tipoContratto == "PTL":
            self.esigenzeMattiniSettimanali = 2
            self.esigenzePomeriggiSettimanali = 1
            self.esigenzeNottiSettimanali = 0
        print(
            f"DEBUG: Esigenze ripristinate: Mattini={self.esigenzeMattiniSettimanali}, Pomeriggi={self.esigenzePomeriggiSettimanali}, Notti={self.esigenzeNottiSettimanali}")

    # Metodi per impostare le necessità/preferenze (corretti)
    def setPermesso(self, giorno: int, value: bool):
        self.dizionarioNecessita["permessi_ferie"][giorno] = value
        # print(f"Permesso di valore {value} nel giorno {giorno} per {self.nome} {self.cognome}")

    def setMutua(self, giorno: int, value: bool):
        self.dizionarioNecessita["mutua_infortunio"][giorno] = value  # Corretto!
        # print(f"Mutua di valore {value} nel giorno {giorno} per {self.nome} {self.cognome}")

    def setNonRetribuite(self, giorno: int, value: bool):
        self.dizionarioNecessita["non_retribuite"][giorno] = value  # Corretto!

    def setNoNotti(self, giorno: int, value: bool):
        self.dizionarioNecessita["no_notte"][giorno] = value  # Corretto!

    def setNoMatt(self, giorno: int, value: bool):
        self.dizionarioNecessita["no_mattino"][giorno] = value  # Corretto!

    def setNoPomeriggi(self, giorno: int, value: bool):
        self.dizionarioNecessita["no_pomeriggio"][giorno] = value  # Corretto!