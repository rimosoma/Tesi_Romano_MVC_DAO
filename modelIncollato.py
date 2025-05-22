import calendar
import os
import datetime
from collections import defaultdict

import pandas as pd
from dateutil.utils import today
from ortools.sat.python import cp_model

from database.DAO import Dao
from database import DB_connect


class SchedulingModel:
    """
    Logica di business per la generazione e gestione dei turni.
    """

    def __init__(self):
        # Configurazione DB, da parametrizzare esternamente

        self.current_year = None
        self.current_month = None
        self.dao = Dao()
        self.turni = []  # lista di turni generati
        self.dictDipendenti = self.dao.get_employees()
        self.is_first_month_historically = False  # Inizializza qui!
        # Mappa i nomi dei turni ai loro tipi principali (M, P, N)

    def controllo_mese(self, mese_str: str) -> bool:
        print(f"DEBUG: controllo_mese chiamato con: {mese_str}")
        try:
            month_val, year_val = map(int, mese_str.split("-"))
            print(f"DEBUG: Parsed month: {month_val}, year: {year_val}")
        except ValueError:
            print("ERRORE: Formato mese non valido. Usa 'MM-YYYY'.")
            self.is_first_month_historically = False  # <--- AGGIUNGI ANCHE QUI per sicurezza
            return False

        self.current_month = month_val
        self.current_year = year_val

        # Definisci il primo mese storico (Maggio 2025 secondo il tuo output)
        FIRST_MONTH_YEAR = 2025  # Secondo il tuo output
        FIRST_MONTH_NUM = 5  # Secondo il tuo output

        print(f"DEBUG: Mese corrente impostato a: {self.current_month}-{self.current_year}")
        print(f"DEBUG: Primo mese storico configurato: {FIRST_MONTH_NUM}-{FIRST_MONTH_YEAR}")

        if (self.current_year < FIRST_MONTH_YEAR) or \
                (self.current_year == FIRST_MONTH_YEAR and self.current_month < FIRST_MONTH_NUM):
            print("DEBUG: Condizione TRUE: Mese troppo vecchio")
            print("Mese troppo vecchio per essere il primo del database (anteriormente a Maggio 2025).")
            self.is_first_month_historically = False  # <--- IMPOSTA QUI
            return False
        elif self.current_year == FIRST_MONTH_YEAR and self.current_month == FIRST_MONTH_NUM:
            print("DEBUG: Condizione TRUE: Primo mese storico identificato (Maggio 2025)")
            print("Primo mese del database.")
            self.is_first_month_historically = True  # <--- IMPOSTA QUI
            self.loadNecessitaDipendenti(mese_str)
            return True
        else:
            print("DEBUG: Condizione: Mese successivo al primo storico.")
            # Controlla l'esistenza del mese precedente usando il DAO
            if self.dao.controlla_mese_precedente(self.current_year, self.current_month):
                print("DEBUG: Mese precedente trovato nel database.")
                self.is_first_month_historically = False  # <--- IMPOSTA QUI
                self.loadNecessitaDipendenti(mese_str)
                return True
            else:
                print("DEBUG: Mese precedente NON trovato nel database.")
                print(
                    f"IMPOSSIBILE PROCEDERE: Il mese precedente ({self.current_month - 1 if self.current_month > 1 else 12}-{self.current_year if self.current_month > 1 else self.current_year - 1}) non è stato trovato nel database. Genera prima i mesi precedenti.")
                self.is_first_month_historically = False  # <--- IMPOSTA QUI
                return False

    def loadNecessitaDipendenti(self, mese):
        print("necessita in creazione")
        month_str, year_str = mese.split("-")
        self.current_month = int(month_str)
        self.current_year = int(year_str)
        for dip in self.dictDipendenti.values():
            # Ogni dipendente riceve il suo dict fresco
            nuovo_dict = self.costruttoreDictNecessita()
            dip.setDizionario(nuovo_dict)

    def costruttoreDictNecessita(self) -> dict[str, dict[int, bool]]:
        """
        Costruisce, per un dipendente, il dict con 6 sotto‐dizionari
        giorno→False, usando l'anno e il mese correnti di questa istanza.
        """
        # numero di giorni del mese corrente
        days_in_month = calendar.monthrange(self.current_year, self.current_month)[1]
        days = range(1, days_in_month + 1)

        necessity_types = [
            "permessi_ferie",
            "mutua_infortunio",
            "non_retribuite",
            "no_mattino",
            "no_pomeriggio",
            "no_notte",
        ]

        # dict comprehension
        return {
            ntype: {day: False for day in days}
            for ntype in necessity_types
        }

    def get_employeesM(self):
        return self.dictDipendenti

    def get_employeeM(self, emp_id):
        return self.dictDipendenti[emp_id]

    def updateNrNotti(self, emp_id, nr):
        self.dictDipendenti[emp_id].setEsigenzeNotti(nr)  # CAMBIO NOME METODO
        return True

    def updateNrMattini(self, emp_id, nr):
        self.dictDipendenti[emp_id].setEsigenzeMattini(nr)  # CAMBIO NOME METODO
        return True

    def updateNrPomeriggi(self, emp_id, nr):
        self.dictDipendenti[emp_id].setEsigenzePomeriggi(nr)  # CAMBIO NOME METODO
        return True

    def updateDaIncludere(self, emp_id, tipo):
        # Questi metodi azzeraTurni/ripristinaTurni agiscono sulle esigenze settimanali predefinite
        # e non sui conteggi attuali (che sono gestiti nel Model/generazione turni)
        if tipo == "maternità" or tipo == "aspettativa":
            self.dictDipendenti[emp_id].azzeraTurni()  # Metodo esistente in Dipendente

        else:
            self.dictDipendenti[emp_id].ripristinaTurni()  # Metodo esistente in Dipendente
        self.dictDipendenti[emp_id].setDaIncludere(tipo)

    def set_permesso_dipendente(self, emp_id: int, giorno: int, valore: bool):
        # Assicurati che emp_id sia valido e che il dizionario esista
        if emp_id in self.dictDipendenti:
            if 'permessi_ferie' not in self.dictDipendenti[emp_id].dizionarioNecessita:
                self.dictDipendenti[emp_id].dizionarioNecessita['permessi_ferie'] = {}
            self.dictDipendenti[emp_id].dizionarioNecessita['permessi_ferie'][giorno] = valore
            print(
                f"DEBUG: set_permesso_dipendente per {emp_id}, giorno {giorno}, valore {valore}. Stato attuale: {self.dictDipendenti[emp_id].dizionarioNecessita['permessi_ferie'][giorno]}")

    def set_mutua_dipendente(self, emp_id: int, giorno: int, valore: bool):
        if emp_id in self.dictDipendenti:
            if 'mutua_infortunio' not in self.dictDipendenti[emp_id].dizionarioNecessita:
                self.dictDipendenti[emp_id].dizionarioNecessita['mutua_infortunio'] = {}
            self.dictDipendenti[emp_id].dizionarioNecessita['mutua_infortunio'][giorno] = valore
            print(
                f"DEBUG: set_mutua_dipendente per {emp_id}, giorno {giorno}, valore {valore}. Stato attuale: {self.dictDipendenti[emp_id].dizionarioNecessita['mutua_infortunio'][giorno]}")

    def set_esigenza_dipendente(self, emp_id: int, giorno: int, valore: bool):
        # Questo è "non_retribuite"
        if emp_id in self.dictDipendenti:
            if 'non_retribuite' not in self.dictDipendenti[emp_id].dizionarioNecessita:
                self.dictDipendenti[emp_id].dizionarioNecessita['non_retribuite'] = {}
            self.dictDipendenti[emp_id].dizionarioNecessita['non_retribuite'][giorno] = valore
            print(
                f"DEBUG: set_esigenza_dipendente per {emp_id}, giorno {giorno}, valore {valore}. Stato attuale: {self.dictDipendenti[emp_id].dizionarioNecessita['non_retribuite'][giorno]}")

    def set_pref_noNott_dipendente(self, emp_id: int, giorno: int, valore: bool):
        if emp_id in self.dictDipendenti:
            if 'no_notte' not in self.dictDipendenti[emp_id].dizionarioNecessita:
                self.dictDipendenti[emp_id].dizionarioNecessita['no_notte'] = {}
            self.dictDipendenti[emp_id].dizionarioNecessita['no_notte'][giorno] = valore
            print(
                f"DEBUG: set_pref_noNott_dipendente per {emp_id}, giorno {giorno}, valore {valore}. Stato attuale: {self.dictDipendenti[emp_id].dizionarioNecessita['no_notte'][giorno]}")

    def set_pref_noMatt_dipendente(self, emp_id: int, giorno: int, valore: bool):
        if emp_id in self.dictDipendenti:
            if 'no_mattino' not in self.dictDipendenti[emp_id].dizionarioNecessita:
                self.dictDipendenti[emp_id].dizionarioNecessita['no_mattino'] = {}
            self.dictDipendenti[emp_id].dizionarioNecessita['no_mattino'][giorno] = valore
            print(
                f"DEBUG: set_pref_noMatt_dipendente per {emp_id}, giorno {giorno}, valore {valore}. Stato attuale: {self.dictDipendenti[emp_id].dizionarioNecessita['no_mattino'][giorno]}")

    def set_pref_noPom_dipendente(self, emp_id: int, giorno: int, valore: bool):
        if emp_id in self.dictDipendenti:
            if 'no_pomeriggio' not in self.dictDipendenti[emp_id].dizionarioNecessita:
                self.dictDipendenti[emp_id].dizionarioNecessita['no_pomeriggio'] = {}
            self.dictDipendenti[emp_id].dizionarioNecessita['no_pomeriggio'][giorno] = valore
            print(
                f"DEBUG: set_pref_noPom_dipendente per {emp_id}, giorno {giorno}, valore {valore}. Stato attuale: {self.dictDipendenti[emp_id].dizionarioNecessita['no_pomeriggio'][giorno]}")

    def controlloTuttiCinque(self):
        for dipendente in self.dictDipendenti:
            if dipendente.daIncludere != ("maternità", "aspettativa") and (
                    int(dipendente.notti) + int(dipendente.mattini) + int(dipendente.pomeriggi) < 5):
                # il dipendente con "da Includere" oppure "non selezionato" non ha 5 turni settimanali
                return False
            else:
                return True

    def genera_turni_mese(self):
        print("DEBUG MODEL: Inizio metodo genera_turni_mese.")

        print(f"DEBUG MODEL: self.current_year tipo: {type(self.current_year)}, valore: {self.current_year}")
        print(f"DEBUG MODEL: self.current_month tipo: {type(self.current_month)}, valore: {self.current_month}")

        dim = calendar.monthrange(self.current_year, self.current_month)[1]
        print(f"DEBUG MODEL: Numero di giorni nel mese: {dim}")

        days = []
        for d in range(1, dim + 1):
            try:
                current_date_obj = datetime.date(self.current_year, self.current_month, d)
                days.append(current_date_obj)
            except Exception as e:
                print(f"ERRORE CRITICO MODEL: Impossibile creare data per giorno {d}: {e}")
                raise

        print(f"DEBUG MODEL: Lista 'days' creata con {len(days)} elementi.")

        days_iso = [d.isoformat() for d in days]

        shift_types_8h = ['mat_1', 'mat_2', 'mat_3', 'mat_4', 'pom_1', 'pom_2', 'pom_3', 'notte']
        shift_types_3h = ['mj', 'pc']
        all_shift_types = shift_types_8h + shift_types_3h

        shift_hours = {s: 8 for s in shift_types_8h}
        shift_hours.update({s: 3 for s in shift_types_3h})

        employees = self.dictDipendenti
        active_employees = {emp_id: dip for emp_id, dip in employees.items() if
                            dip.daIncludere not in ["maternità", "aspettativa"]}
        print(f"DEBUG: Generazione turni per {len(active_employees)} dipendenti attivi.")

        ## DEBUG STEP 0: Inizializzazione dati settimana precedente (MANTENERE ATTIVO) ##
        if self.is_first_month_historically:
            print("DEBUG MODEL: È il primo mese storico, prev_week_data sarà inizializzato come vuoto.")
            prev_week_data = {}
        else:
            print("DEBUG MODEL: Chiamo DAO per get_last_week_turni per recuperare i dati della settimana precedente.")
            try:
                prev_week_data = self.dao.get_last_week_turni(self.current_year, self.current_month)
                print(f"DEBUG MODEL: get_last_week_turni ha restituito dati per {len(prev_week_data)} dipendenti.")
            except Exception as e:
                print(f"ERRORE DAO CALL: Errore durante la chiamata a get_last_week_turni: {e}")
                raise

        print(f"DEBUG MODEL: Prev_week_data finale: {prev_week_data}")

        initial_consecutive_work_days = {}
        for emp_id, history in prev_week_data.items():
            if emp_id in active_employees:
                count = 0
                for activity in reversed(history):
                    if activity == 'lavoro':
                        count += 1
                    else:
                        break
                initial_consecutive_work_days[emp_id] = count
            else:
                initial_consecutive_work_days[emp_id] = 0
        ## FINE DEBUG STEP 0 ##

        # 5) Costruisci il modello CP-SAT
        model = cp_model.CpModel()
        x = {}
        is_assigned = {}
        has_rest = {}
        is_any_mandatory_absence_vars = {}
        print("DEBUG MODEL: is_any_mandatory_absence_vars inizializzato.")

        # 5.1) Variabili di assegnazione e vincoli base giorno per giorno
        print(
            f"DEBUG MODEL: Inizio creazione variabili di assegnazione. Numero dipendenti attivi: {len(active_employees)}")

        for emp_id, dip in active_employees.items():
            print(f"DEBUG MODEL: Processing employee ID: {emp_id}, Nome: {dip.nome} {dip.cognome}")

            if not hasattr(dip, 'dizionarioNecessita') or not isinstance(dip.dizionarioNecessita, dict):
                print(
                    f"ERRORE CRITICO MODEL: Il dipendente {emp_id} non ha 'dizionarioNecessita' o non è un dizionario!")
                raise AttributeError(f"Dipendente {emp_id} ha 'dizionarioNecessita' mancante o non valido.")

            prefs = dip.dizionarioNecessita

            for d_obj in days:
                d_iso = d_obj.isoformat()
                day_idx = d_obj.day

                ## DEBUG STEP 1: Creazione Variabili di Base (is_assigned, has_rest, x) e loro vincoli minimali ##
                # (Questa sezione deve rimanere ATTIVA per il modello base)
                print(f"DEBUG MODEL: *** DEBUG STEP 1: Creazione Variabili di Base per {emp_id}, Giorno {d_iso}. ***")

                is_assigned[(emp_id, d_obj)] = model.NewBoolVar(f"is_assigned_{emp_id}_{d_iso}")
                has_rest[(emp_id, d_obj)] = model.NewBoolVar(f"has_rest_{emp_id}_{d_iso}")
                model.Add(is_assigned[(emp_id, d_obj)] + has_rest[(emp_id, d_obj)] == 1)

                for s in all_shift_types:
                    x[(emp_id, d_obj, s)] = model.NewBoolVar(f"x_{emp_id}_{d_iso}_{s}")

                # Vincolo: se assegnato, deve avere UN turno
                model.AddBoolOr([x[(emp_id, d_obj, s)] for s in all_shift_types]).OnlyEnforceIf(
                    is_assigned[(emp_id, d_obj)])
                # Vincolo: se NON assegnato, NON deve avere turni
                model.AddBoolAnd([x[(emp_id, d_obj, s)].Not() for s in all_shift_types]).OnlyEnforceIf(
                    is_assigned[(emp_id, d_obj)].Not())
                ## FINE DEBUG STEP 1 ##

                ## DEBUG STEP 2: Vincoli su Assenze Obbligatorie (Ferie, Mutua, Non Retribuite) ##
                # Questo blocco rimane ATTIVO

                try:
                    permessi_ferie_val = bool(prefs.get('permessi_ferie', {}).get(day_idx, False))
                    mutua_infortunio_val = bool(prefs.get('mutua_infortunio', {}).get(day_idx, False))
                    non_retribuite_val = bool(prefs.get('non_retribuite', {}).get(day_idx, False))

                    print(f"DEBUG MODEL: Accessing prefs for day_idx: {day_idx} (d_obj: {d_obj.isoformat()}). Values: "
                          f"permessi_ferie={permessi_ferie_val}, mutua_infortunio={mutua_infortunio_val}, "
                          f"non_retribuite={non_retribuite_val}")

                except Exception as e:
                    print(
                        f"ERRORE CRITICO MODEL: Errore durante accesso a prefs per dipendente {emp_id}, giorno {d_obj.isoformat()}: {e}")
                    raise

                print(f"DEBUG MODEL: *** DEBUG STEP 2: Gestione Assenze Obbligatorie per {emp_id}, Giorno {d_iso}. ***")

                is_ferie_pref = model.NewBoolVar(f"is_ferie_pref_{emp_id}_{d_iso}")
                is_mutua_pref = model.NewBoolVar(f"is_mutua_pref_{emp_id}_{d_iso}")
                is_non_ret_pref = model.NewBoolVar(f"is_non_ret_pref_{emp_id}_{d_iso}")

                if permessi_ferie_val:
                    model.Add(is_ferie_pref == True)
                else:
                    model.Add(is_ferie_pref == False)

                if mutua_infortunio_val:
                    model.Add(is_mutua_pref == True)
                else:
                    model.Add(is_mutua_pref == False)

                if non_retribuite_val:
                    model.Add(is_non_ret_pref == True)
                else:
                    model.Add(is_non_ret_pref == False)

                is_any_mandatory_absence_pref_var = model.NewBoolVar(f"is_any_mand_abs_pref_{emp_id}_{d_iso}")

                model.AddBoolOr([is_ferie_pref, is_mutua_pref, is_non_ret_pref]).OnlyEnforceIf(
                    is_any_mandatory_absence_pref_var)
                model.AddBoolAnd([is_ferie_pref.Not(), is_mutua_pref.Not(), is_non_ret_pref.Not()]).OnlyEnforceIf(
                    is_any_mandatory_absence_pref_var.Not())

                is_any_mandatory_absence_vars[(emp_id, d_obj)] = is_any_mandatory_absence_pref_var

                model.Add(is_assigned[(emp_id, d_obj)] == False).OnlyEnforceIf(
                    is_any_mandatory_absence_vars[(emp_id, d_obj)])
                model.Add(has_rest[(emp_id, d_obj)] == True).OnlyEnforceIf(
                    is_any_mandatory_absence_vars[(emp_id, d_obj)])

                for s in all_shift_types:
                    if (emp_id, d_obj, s) in x:
                        model.Add(x[(emp_id, d_obj, s)] == False).OnlyEnforceIf(
                            is_any_mandatory_absence_vars[(emp_id, d_obj)])

                ## FINE DEBUG STEP 2 ##

            print(f"DEBUG MODEL: *** FINE GIORNI PER DIPENDENTE {emp_id}. ***")

        print(
            f"DEBUG MODEL: *** TUTTI I DIPENDENTI E I GIORNI PROCESSATI SENZA ERRORE NEL LOOP PRINCIPALE (Sezione 5.1). ***")

        ## DEBUG STEP 3: Vincolo: ogni turno coperto ESATTAMENTE da 1 dipendente (SECTION 5.2) ##
        # Questo blocco rimane ATTIVO
        print(f"DEBUG MODEL: *** DEBUG STEP 3: Inizio vincolo 5.2 (copertura turni). ***")
        for d_obj in days:
            for s in all_shift_types:
                vars_for_shift = [x[(emp_id, d_obj, s)] for emp_id in active_employees if (emp_id, d_obj, s) in x]
                if vars_for_shift:
                    model.AddExactlyOne(vars_for_shift)
        print(f"DEBUG MODEL: Vincolo 5.2 aggiunto. ")
        ## FINE DEBUG STEP 3 ##

        ## DEBUG STEP 4: Vincolo: max 1 turno per dipendente al giorno (SECTION 5.3) ##
        # Questo blocco rimane ATTIVO
        print(f"DEBUG MODEL: *** DEBUG STEP 4: Inizio vincolo 5.3 (max 1 turno per dipendente al giorno). ***")
        for emp_id in active_employees:
            for d_obj in days:
                vars_for_day_employee = [x[(emp_id, d_obj, s)] for s in all_shift_types if (emp_id, d_obj, s) in x]
                if vars_for_day_employee:  # Aggiunto controllo per lista vuota
                    model.AddAtMostOne(vars_for_day_employee)
        print(f"DEBUG MODEL: Vincolo 5.3 aggiunto.")
        ## FINE DEBUG STEP 4 ##

        ## DEBUG STEP 5: Raggruppamento giorni per settimana ISO (MANTENERE ATTIVO SE USATO DOPO) ##
        weeks = defaultdict(list)
        for d_obj in days:
            wnum = d_obj.isocalendar()[1]
            weeks[wnum].append(d_obj)
        print(
            f"DEBUG MODEL: Raggruppamento completato. Numero settimane: {len(weeks)}. Inizio vincoli settimanali per dipendenti.")
        ## FINE DEBUG STEP 5 ##

        ## DEBUG STEP 6: Vincoli settimanali per dipendenti (SECTION 5.5) ##
        # Questo blocco è ora COMPLETAMENTE DECOMMENTATO
        print(
            f"DEBUG MODEL: *** DEBUG STEP 6: Inizio vincoli settimanali per dipendenti (Section 5.5). (Tutti i vincoli attivi). ***")
        for emp_id, dip in active_employees.items():
            print(f"DEBUG MODEL: {emp_id} - Inizio vincoli settimanali per il dipendente.")
            """
            # Vincolo: No più di 5 giorni lavorativi consecutivi.
            for i in range(len(days) - 4):  # Finestre di 5 giorni
                current_window_work_vars = [is_assigned[(emp_id, days[i + j])] for j in range(5)]

                # Se tutti e 5 i giorni nella finestra sono assegnati come lavoro, allora il sesto giorno deve essere riposo
                # Creiamo una variabile booleana per rappresentare "tutti e 5 sono lavoro"
                all_5_working_in_window = model.NewBoolVar(f"all_5_working_{emp_id}_{days[i].isoformat()}")
                model.AddBoolAnd(current_window_work_vars).OnlyEnforceIf(all_5_working_in_window)
                model.AddBoolOr([v.Not() for v in current_window_work_vars]).OnlyEnforceIf(
                    all_5_working_in_window.Not())  # Necessario per la reificazione inversa

                if i + 5 < len(days):  # Assicurati che esista un "sesto giorno" nel mese
                    next_day_after_5_working = days[i + 5]
                    model.Add(has_rest[(emp_id, next_day_after_5_working)] == True).OnlyEnforceIf(
                        all_5_working_in_window)
                    model.Add(is_assigned[(emp_id, next_day_after_5_working)] == False).OnlyEnforceIf(
                        all_5_working_in_window)
            print(f"DEBUG MODEL: {emp_id} - Vincolo 5 giorni lavorativi consecutivi e riposo seguente aggiunti.")
            """

            # Vincolo: Se dal mese precedente ci sono >= 5 giorni di lavoro consecutivi, il primo giorno del mese corrente deve essere riposo.
            if initial_consecutive_work_days.get(emp_id, 0) >= 5 and len(days) > 0:
                print(
                    f"DEBUG MODEL: {emp_id} - initial_consecutive_work_days è {initial_consecutive_work_days.get(emp_id, 0)}. Applico vincolo riposo per il primo giorno del mese.")
                model.Add(has_rest[(emp_id, days[0])] == True)
                model.Add(is_assigned[(emp_id, days[0])] == False)
            else:
                print(
                    f"DEBUG MODEL: {emp_id} - Nessun vincolo di riposo per il primo giorno del mese (initial_consecutive_work_days: {initial_consecutive_work_days.get(emp_id, 0)}).")
            print(f"DEBUG MODEL: {emp_id} - Vincolo riposo inizio mese gestito (se applicabile).")

            # Vincolo: Almeno 2 giorni di riposo in una finestra di 7 giorni (scorrevole)
            """
            for i in range(len(days) - 6):  # Finestre di 7 giorni
                window_days = [days[i + j] for j in range(7)]
                rest_vars_in_window = [has_rest[(emp_id, d_w)] for d_w in window_days if (emp_id, d_w) in has_rest]
                if rest_vars_in_window:  # Aggiunto controllo per evitare liste vuote
                    model.Add(sum(rest_vars_in_window) >= 2)
            print(f"DEBUG MODEL: {emp_id} - Vincolo almeno 2 riposi in 7 giorni scorrevoli aggiunto.")
            """
            # Vincoli per settimana ISO:

            for wnum, wdays in weeks.items():
                print(f"DEBUG MODEL: {emp_id}, Settimana ISO {wnum} - Inizio vincoli specifici settimana.")
                """
                # a) Esattamente 5 giorni lavorativi (quindi 2 giorni di riposo)
                # NOTA: questo vincolo assume settimane complete di 7 giorni lavorativi per il calcolo.
                # Se la settimana ISO non ha 7 giorni nel mese, questo vincolo potrebbe essere problematico.
                # Potrebbe essere necessario un controllo if len(wdays) == 7

                if len(wdays) == 7:  # Applica questo vincolo solo a settimane complete
                    work_vars_in_iso_week = [is_assigned[(emp_id, d_obj)] for d_obj in wdays if
                                             (emp_id, d_obj) in is_assigned]
                    if work_vars_in_iso_week:
                        model.Add(sum(work_vars_in_iso_week) == 5)  # Esattamente 5 giorni lavorativi
                        print(
                            f"DEBUG MODEL: {emp_id}, Settimana {wnum} (completa) - Vincolo 5 giorni lavorativi aggiunti. (Lavorativi: {len(work_vars_in_iso_week) - 2})")
                else:
                    print(
                        f"DEBUG MODEL: {emp_id}, Settimana {wnum} (non completa) - Vincolo 5 giorni lavorativi/2 riposi NON applicato.")
                    """
                # Valori convertiti a INT
                esigenze_mattini = int(dip.esigenzeMattiniSettimanali)
                esigenze_pomeriggi = int(dip.esigenzePomeriggiSettimanali)
                esigenze_notti = int(dip.esigenzeNottiSettimanali)
                monte_ore_settimanale_num = int(dip.monteOreSettimanale)  # Assumiamo int

                print(f"DEBUG MODEL: {emp_id}, Settimana {wnum} - Valori esigenze settimanali (dopo conversione): "
                      f"Mattini={esigenze_mattini}, Pomeriggi={esigenze_pomeriggi}, Notti={esigenze_notti}")

                # b) Esatto numero di mattini/pomeriggi/notti a settimana
                # Assicurati che queste somme siano fatte solo per i giorni che appartengono alla settimana corrente (wdays)
                m_vars = [x[(emp_id, d_obj, s)]
                          for d_obj in wdays for s in ['mat_1', 'mat_2', 'mat_3', 'mat_4']
                          if (emp_id, d_obj, s) in x]
                if m_vars:
                    print(
                        f"DEBUG MODEL: {emp_id}, Settimana {wnum} - Aggiungo vincolo mattini. Somma m_vars: {len(m_vars)}.")
                    model.Add(sum(m_vars) <= esigenze_mattini)
                else:
                    # Questo print è importante per debug, se ti aspetti mattini ma non vengono trovati
                    print(
                        f"DEBUG MODEL: {emp_id}, Settimana {wnum} - Nessun turno mattina disponibile in m_vars. Vincolo mattini NON aggiunto (o 0 attesi).")

                p_vars = [x[(emp_id, d_obj, s)]
                          for d_obj in wdays for s in ['pom_1', 'pom_2', 'pom_3']
                          if (emp_id, d_obj, s) in x]
                if p_vars:
                    print(
                        f"DEBUG MODEL: {emp_id}, Settimana {wnum} - Aggiungo vincolo pomeriggi. Somma p_vars: {len(p_vars)}.")
                    model.Add(sum(p_vars) <= esigenze_pomeriggi)
                else:
                    print(
                        f"DEBUG MODEL: {emp_id}, Settimana {wnum} - Nessun turno pomeriggio disponibile in p_vars. Vincolo pomeriggi NON aggiunto (o 0 attesi).")

                n_vars = [x[(emp_id, d_obj, 'notte')]
                          for d_obj in wdays if (emp_id, d_obj, 'notte') in x]
                if n_vars:
                    print(
                        f"DEBUG MODEL: {emp_id}, Settimana {wnum} - Aggiungo vincolo notti. Somma n_vars: {len(n_vars)}.")
                    model.Add(sum(n_vars) <= esigenze_notti)
                else:
                    print(
                        f"DEBUG MODEL: {emp_id}, Settimana {wnum} - Nessun turno notte disponibile in n_vars. Vincolo notti NON aggiunto (o 0 attesi).")

                # c) Monte ore settimanale esatto
                ore_terms = []
                print(f"DEBUG MODEL: {emp_id}, Settimana {wnum} - Inizio calcolo monte ore settimanale per giorno.")
                for d_obj in wdays:
                    d_iso = d_obj.isoformat()

                    # Variabile per le ore lavorate effettivamente in un giorno specifico
                    daily_actual_hours = model.NewIntVar(0, 24, f"daily_actual_hours_{emp_id}_{d_obj.isoformat()}")

                    # Calcola le ore effettive assegnate (somma delle ore dei turni)
                    assigned_shift_hours = cp_model.LinearExpr.Sum(
                        [x[(emp_id, d_obj, s)] * shift_hours[s] for s in all_shift_types if (emp_id, d_obj, s) in x])

                    # Se il dipendente è assegnato, le ore effettive sono la somma dei turni
                    model.Add(daily_actual_hours == assigned_shift_hours).OnlyEnforceIf(is_assigned[(emp_id, d_obj)])

                    # Se il dipendente è a riposo (e non in assenza obbligatoria), le ore effettive sono 0
                    model.Add(daily_actual_hours == 0).OnlyEnforceIf(has_rest[(emp_id, d_obj)])

                    # Gestione delle assenze obbligatorie nel calcolo delle ore
                    is_any_mandatory_absence_day_var = is_any_mandatory_absence_vars.get((emp_id, d_obj))

                    # Se la variabile di assenza obbligatoria non è definita, è un problema. Fallback per evitare crash.
                    if is_any_mandatory_absence_day_var is None:
                        print(
                            f"ERRORE DEBUG MODEL: is_any_mandatory_absence_day_var NON definita per {emp_id}, {d_obj.isoformat()}. Assicurarsi che DEBUG STEP 2 sia attivo e funzionante.")
                        is_any_mandatory_absence_day_var = model.NewBoolVar(
                            f"TEMP_abs_false_{emp_id}_{d_obj.isoformat()}")
                        model.Add(
                            is_any_mandatory_absence_day_var == False)  # Imposta a False per default in caso di errore

                    # Creiamo una variabile per il contributo orario delle assenze obbligatorie
                    # Assumiamo 0.8 ore per ogni ora non lavorata causa assenza obbligatoria (es. 8h * 0.8 = 6.4h)
                    absence_contrib_hours = model.NewIntVar(0, int(8 * 0.8 * 100),
                                                            f"absence_contrib_hours_{emp_id}_{d_obj.isoformat()}")
                    # Moltiplichiamo per 100 e poi dividiamo alla fine per mantenere precisione con i decimali
                    model.Add(absence_contrib_hours == int(8 * 0.8 * 100)).OnlyEnforceIf(
                        is_any_mandatory_absence_day_var)
                    model.Add(absence_contrib_hours == 0).OnlyEnforceIf(is_any_mandatory_absence_day_var.Not())

                    # Variabile per il contributo totale del giorno (turni lavorati O ore da assenza)
                    total_daily_contribution = model.NewIntVar(0, 24 * 100,
                                                               f"total_daily_contrib_{emp_id}_{d_obj.isoformat()}")  # Scalato per precisione

                    # Se c'è un turno assegnato, il contributo è daily_actual_hours (scalato)
                    # Converti daily_actual_hours in centesimi per coerenza
                    daily_actual_hours_scaled = model.NewIntVar(0, 24 * 100,
                                                                f"daily_actual_hours_scaled_{emp_id}_{d_obj.isoformat()}")
                    model.Add(daily_actual_hours_scaled == daily_actual_hours * 100)  # Converti ore a centesimi

                    model.Add(total_daily_contribution == daily_actual_hours_scaled).OnlyEnforceIf(
                        is_assigned[(emp_id, d_obj)])

                    # Se il dipendente è a riposo e non in assenza obbligatoria, il contributo è 0
                    # NOTA: Questa riga potrebbe sovrapporsi a quella sotto se has_rest e is_any_mandatory_absence_day_var.Not() sono entrambi veri.
                    # È importante la logica: se c'è un'assenza obbligatoria, quella prevale sulle "ore zero".
                    model.Add(total_daily_contribution == 0).OnlyEnforceIf(
                        has_rest[(emp_id, d_obj)], is_any_mandatory_absence_day_var.Not())

                    # Se è in assenza obbligatoria (e quindi a riposo forzato), il contributo è absence_contrib_hours
                    model.Add(total_daily_contribution == absence_contrib_hours).OnlyEnforceIf(
                        is_any_mandatory_absence_day_var)

                    ore_terms.append(total_daily_contribution)  # Aggiungi la variabile al totale settimanale

                # Vincolo sul monte ore settimanale totale (in centesimi di ora)
                if ore_terms:
                    monte_ore_settimanale_scaled = int(monte_ore_settimanale_num * 100)
                    print(
                        f"DEBUG MODEL: {emp_id}, Settimana {wnum} - Monte ore previsto (scalato): {monte_ore_settimanale_scaled} centesimi.")
                    model.Add(sum(ore_terms) == monte_ore_settimanale_scaled)
                print(f"DEBUG MODEL: {emp_id}, Settimana {wnum} - Fine vincoli specifici settimana.")

            print(f"DEBUG MODEL: Fine vincoli settimanali per dipendente {emp_id}.")
        ## FINE DEBUG STEP 6 ##

        # ## DEBUG STEP 7: Vincoli soft: preferenze “no_…” con penalità (SECTION 6) ##
        # Per attivare: scommenta TUTTO il blocco sottostante
        penalties = []  # Deve essere sempre dichiarato per l'obiettivo
        """
        print(f"DEBUG MODEL: *** DEBUG STEP 7: Inizio vincoli soft (penalità). ***")
        for emp_id, dip in active_employees.items():
            prefs = dip.dizionarioNecessita
            for d_obj in days:
                day_idx = d_obj.day
                if prefs.get('no_mattino', {}).get(day_idx, False):
                    for s in ['mat_1', 'mat_2', 'mat_3', 'mat_4']:
                        if (emp_id, d_obj, s) in x:
                            penalties.append(x[(emp_id, d_obj, s)])
                if prefs.get('no_pomeriggio', {}).get(day_idx, False):
                    for s in ['pom_1', 'pom_2', 'pom_3']:
                        if (emp_id, d_obj, s) in x:
                            penalties.append(x[(emp_id, d_obj, s)])
                if prefs.get('no_notte', {}).get(day_idx, False) and (emp_id, d_obj, 'notte') in x:
                    penalties.append(x[(emp_id, d_obj, 'notte')])
        print(f"DEBUG MODEL: Fine vincoli soft. Penalità totali aggiunte: {len(penalties)}")
        """
        ## FINE DEBUG STEP 7 ##

        # 7) Risolvi il modello
        if penalties:
            print(f"DEBUG MODEL: Obiettivo: Minimizzare {len(penalties)} penalità.")
            model.Minimize(sum(penalties))
        else:
            print(
                "DEBUG MODEL: Nessuna penalità aggiunta, modello non ha obiettivo di minimizzazione (solo vincoli rigidi).")
            model.Minimize(0)  # Obiettivo di base se non ci sono penalità

        solver = cp_model.CpSolver()
        solver.parameters.log_search_progress = True
        print("DEBUG MODEL: Chiamata a solver.Solve(model)...")
        status = solver.Solve(model)
        print(f"DEBUG MODEL: solver.Solve(model) completato. Status: {solver.StatusName(status)}")

        if status not in (cp_model.OPTIMAL, cp_model.FEASIBLE):
            print(f"ERRORE: Nessuna soluzione valida trovata per i vincoli dati. Status: {solver.StatusName(status)}")
            print(f"Statistiche risolutore: {solver.ResponseStats()}")
            raise RuntimeError("Nessuna soluzione valida trovata per i vincoli dati")
        else:
            print(f"Soluzione trovata! Status: {solver.StatusName(status)}")
            print(f"Penalità totali (violazioni preferenze): {solver.ObjectiveValue()}")
            print(f"Statistiche risolutore: {solver.ResponseStats()}")

        # 8) Estrai soluzioni e costruisci liste per DB e DataFrame
        print(f"DEBUG MODEL: Inizio estrazione soluzioni.")
        db_schedule = []
        excel_data_by_employee = defaultdict(
            lambda: {'Dipendente': '', 'Monte Ore Previsto': 0, 'Monte Ore Effettivo': 0})

        for emp_id, dip in active_employees.items():
            excel_data_by_employee[emp_id]['Dipendente'] = f"{dip.nome} {dip.cognome} (ID: {dip.id})"
            # Calcolo del monte ore previsto su base mensile (Monte Ore Settimanale / 7 giorni * giorni nel mese)
            # Questo calcolo qui è solo per l'output in Excel, non influenza la soluzione del solver.
            estimated_monthly_hours = (float(dip.monteOreSettimanale) / 7) * dim
            excel_data_by_employee[emp_id]['Monte Ore Previsto'] = round(estimated_monthly_hours, 2)
            excel_data_by_employee[emp_id]['Monte Ore Effettivo'] = 0.0  # Verrà aggiornato

        print(f"DEBUG MODEL: Dati base Excel preparati.")

        for d_obj in days:
            day_column = f"Giorno {d_obj.day} ({d_obj.strftime('%a')})"
            for emp_id, dip in active_employees.items():
                excel_data_by_employee[emp_id][day_column] = ""  # Inizializza la colonna del giorno

            for emp_id, dip in active_employees.items():
                assigned_shift = None
                assigned_hours = 0.0
                try:
                    # Verifica se è stato assegnato un turno effettivo
                    for s_type in all_shift_types:
                        if (emp_id, d_obj, s_type) in x and solver.Value(x[(emp_id, d_obj, s_type)]) == 1:
                            assigned_shift = s_type
                            assigned_hours = shift_hours[s_type]
                            break  # Trovato il turno, esci dal loop dei turni
                except Exception as e:
                    print(f"ERRORE ESTRAZIONE: Errore estrazione turno per {emp_id} giorno {d_obj.isoformat()}: {e}")
                    assigned_shift = "ERRORE"  # Segnaliamo un errore nell'estrazione

                if assigned_shift and assigned_shift != "ERRORE":
                    # Se è stato assegnato un turno, aggiorna i dati Excel e DB
                    excel_data_by_employee[emp_id][day_column] = assigned_shift
                    excel_data_by_employee[emp_id]['Monte Ore Effettivo'] += assigned_hours

                    db_schedule.append({
                        'data_turno': d_obj.isoformat(),
                        'codice_dipendente': emp_id,
                        'tipo_turno': assigned_shift,
                        'ore_assegnate': assigned_hours,
                        'note': ""
                    })
                else:
                    # Se non è stato assegnato un turno (o c'è stato un errore), controlla le assenze obbligatorie
                    permessi_ferie_day = dip.dizionarioNecessita.get('permessi_ferie', {}).get(d_obj.day, False)
                    mutua_infortunio_day = dip.dizionarioNecessita.get('mutua_infortunio', {}).get(d_obj.day, False)
                    non_retribuite_day = dip.dizionarioNecessita.get('non_retribuite', {}).get(d_obj.day, False)

                    is_mandatory_abs_day_python_check = permessi_ferie_day or mutua_infortunio_day or non_retribuite_day

                    assigned_type_for_excel = "RIP"
                    db_assigned_type = "RIPOSO"
                    db_hours = 0.0  # Normalmente riposo è 0 ore

                    if is_mandatory_abs_day_python_check:
                        if permessi_ferie_day:
                            assigned_type_for_excel = "FERIE"
                            db_assigned_type = "FERIE"
                            db_hours = 8 * 0.8  # Contributo ore per ferie
                        elif mutua_infortunio_day:
                            assigned_type_for_excel = "MUTUA"
                            db_assigned_type = "MUTUA"
                            db_hours = 8 * 0.8  # Contributo ore per mutua
                        elif non_retribuite_day:
                            assigned_type_for_excel = "NR"
                            db_assigned_type = "NON_RETRIBUITE"
                            db_hours = 0  # Le non retribuite non contribuiscono al monte ore

                        # Aggiorna il monte ore effettivo anche per le assenze con contributo
                        excel_data_by_employee[emp_id]['Monte Ore Effettivo'] += db_hours

                    excel_data_by_employee[emp_id][day_column] = assigned_type_for_excel

                    db_schedule.append({
                        'data_turno': d_obj.isoformat(),
                        'codice_dipendente': emp_id,
                        'tipo_turno': db_assigned_type,
                        'ore_assegnate': db_hours,
                        'note': "Assenza obbligatoria" if is_mandatory_abs_day_python_check else "Riposo"
                    })
        print(f"DEBUG MODEL: Estrazione soluzioni completata. Record per DB: {len(db_schedule)}")

        # 9) Salva nel DB (sovrascrive il mese)
        print("DEBUG: Salvataggio turni nel database...")
        self.dao.save_turni_mese(
            self.current_year,
            self.current_month,
            db_schedule
        )
        print("DEBUG: Turni salvati nel database.")

        # 10) Esporta in Excel
        final_excel_rows = list(excel_data_by_employee.values())
        df = pd.DataFrame(final_excel_rows)

        fixed_cols = ['Dipendente', 'Monte Ore Previsto', 'Monte Ore Effettivo']
        dynamic_day_cols = [f"Giorno {d.day} ({d.strftime('%a')})" for d in days]
        all_excel_cols = fixed_cols + dynamic_day_cols
        df = df.reindex(columns=all_excel_cols).fillna("")

        output_filename = f"turni_{self.current_year}_{self.current_month}.xlsx"
        output_path = os.path.join(os.getcwd(), output_filename)
        df.to_excel(output_path, index=False, engine="openpyxl")
        print(f"DEBUG: File Excel generato: {output_path}")
        os.startfile(output_path)

        print("DEBUG: Fine metodo genera_turni_mese. Restituisco il nome del file.")
        return output_filename
