import calendar
import os
import datetime
from collections import defaultdict

import pandas as pd
from dateutil.utils import today
from openpyxl.styles import PatternFill, Alignment, Font
from openpyxl.utils import get_column_letter
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
            self.is_first_month_historically = False # <--- AGGIUNGI ANCHE QUI per sicurezza
            return False

        self.current_month = month_val
        self.current_year = year_val

        # Definisci il primo mese storico (Maggio 2025 secondo il tuo output)
        FIRST_MONTH_YEAR = 2025 # Secondo il tuo output
        FIRST_MONTH_NUM = 5   # Secondo il tuo output

        print(f"DEBUG: Mese corrente impostato a: {self.current_month}-{self.current_year}")
        print(f"DEBUG: Primo mese storico configurato: {FIRST_MONTH_NUM}-{FIRST_MONTH_YEAR}")

        if (self.current_year < FIRST_MONTH_YEAR) or \
           (self.current_year == FIRST_MONTH_YEAR and self.current_month < FIRST_MONTH_NUM):
            print("DEBUG: Condizione TRUE: Mese troppo vecchio")
            print("Mese troppo vecchio per essere il primo del database (anteriormente a Maggio 2025).")
            self.is_first_month_historically = False # <--- IMPOSTA QUI
            return False
        elif self.current_year == FIRST_MONTH_YEAR and self.current_month == FIRST_MONTH_NUM:
            print("DEBUG: Condizione TRUE: Primo mese storico identificato (Maggio 2025)")
            print("Primo mese del database.")
            self.is_first_month_historically = True # <--- IMPOSTA QUI
            self.loadNecessitaDipendenti(mese_str)
            return True
        else:
            print("DEBUG: Condizione: Mese successivo al primo storico.")
            # Controlla l'esistenza del mese precedente usando il DAO
            if self.dao.controlla_mese_precedente(self.current_year, self.current_month):
                print("DEBUG: Mese precedente trovato nel database.")
                self.is_first_month_historically = False # <--- IMPOSTA QUI
                self.loadNecessitaDipendenti(mese_str)
                return True
            else:
                print("DEBUG: Mese precedente NON trovato nel database.")
                print(f"IMPOSSIBILE PROCEDERE: Il mese precedente ({self.current_month-1 if self.current_month > 1 else 12}-{self.current_year if self.current_month > 1 else self.current_year-1}) non è stato trovato nel database. Genera prima i mesi precedenti.")
                self.is_first_month_historically = False # <--- IMPOSTA QUI
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
            ntype: { day: False for day in days }
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
            print(f"DEBUG: set_permesso_dipendente per {emp_id}, giorno {giorno}, valore {valore}. Stato attuale: {self.dictDipendenti[emp_id].dizionarioNecessita['permessi_ferie'][giorno]}")

    def set_mutua_dipendente(self, emp_id: int, giorno: int, valore: bool):
        if emp_id in self.dictDipendenti:
            if 'mutua_infortunio' not in self.dictDipendenti[emp_id].dizionarioNecessita:
                self.dictDipendenti[emp_id].dizionarioNecessita['mutua_infortunio'] = {}
            self.dictDipendenti[emp_id].dizionarioNecessita['mutua_infortunio'][giorno] = valore
            print(f"DEBUG: set_mutua_dipendente per {emp_id}, giorno {giorno}, valore {valore}. Stato attuale: {self.dictDipendenti[emp_id].dizionarioNecessita['mutua_infortunio'][giorno]}")

    def set_esigenza_dipendente(self, emp_id: int, giorno: int, valore: bool):
        # Questo è "non_retribuite"
        if emp_id in self.dictDipendenti:
            if 'non_retribuite' not in self.dictDipendenti[emp_id].dizionarioNecessita:
                self.dictDipendenti[emp_id].dizionarioNecessita['non_retribuite'] = {}
            self.dictDipendenti[emp_id].dizionarioNecessita['non_retribuite'][giorno] = valore
            print(f"DEBUG: set_esigenza_dipendente per {emp_id}, giorno {giorno}, valore {valore}. Stato attuale: {self.dictDipendenti[emp_id].dizionarioNecessita['non_retribuite'][giorno]}")

    def set_pref_noNott_dipendente(self, emp_id: int, giorno: int, valore: bool):
        if emp_id in self.dictDipendenti:
            if 'no_notte' not in self.dictDipendenti[emp_id].dizionarioNecessita:
                self.dictDipendenti[emp_id].dizionarioNecessita['no_notte'] = {}
            self.dictDipendenti[emp_id].dizionarioNecessita['no_notte'][giorno] = valore
            print(f"DEBUG: set_pref_noNott_dipendente per {emp_id}, giorno {giorno}, valore {valore}. Stato attuale: {self.dictDipendenti[emp_id].dizionarioNecessita['no_notte'][giorno]}")

    def set_pref_noMatt_dipendente(self, emp_id: int, giorno: int, valore: bool):
        if emp_id in self.dictDipendenti:
            if 'no_mattino' not in self.dictDipendenti[emp_id].dizionarioNecessita:
                self.dictDipendenti[emp_id].dizionarioNecessita['no_mattino'] = {}
            self.dictDipendenti[emp_id].dizionarioNecessita['no_mattino'][giorno] = valore
            print(f"DEBUG: set_pref_noMatt_dipendente per {emp_id}, giorno {giorno}, valore {valore}. Stato attuale: {self.dictDipendenti[emp_id].dizionarioNecessita['no_mattino'][giorno]}")

    def set_pref_noPom_dipendente(self, emp_id: int, giorno: int, valore: bool):
        if emp_id in self.dictDipendenti:
            if 'no_pomeriggio' not in self.dictDipendenti[emp_id].dizionarioNecessita:
                self.dictDipendenti[emp_id].dizionarioNecessita['no_pomeriggio'] = {}
            self.dictDipendenti[emp_id].dizionarioNecessita['no_pomeriggio'][giorno] = valore
            print(f"DEBUG: set_pref_noPom_dipendente per {emp_id}, giorno {giorno}, valore {valore}. Stato attuale: {self.dictDipendenti[emp_id].dizionarioNecessita['no_pomeriggio'][giorno]}")






    def controlloTuttiCinque(self):
        for dipendente in self.dictDipendenti:
            if dipendente.daIncludere != ("maternità", "aspettativa") and (int(dipendente.notti) + int(dipendente.mattini) + int(dipendente.pomeriggi) < 5):
                #il dipendente con "da Includere" oppure "non selezionato" non ha 5 turni settimanali
                return False
            else:
                return True

    def genera_turni_mese(self):
        # --- 1) Prepara i dati di base ---
        year, month = self.current_year, self.current_month
        dim = calendar.monthrange(year, month)[1]
        days = [datetime.date(year, month, d) for d in range(1, dim + 1)]
        shift_types_8h = ['mat_1', 'mat_2', 'mat_3', 'mat_4', 'pom_1', 'pom_2', 'pom_3', 'notte']
        shift_types_3h = ['mj', 'pc']
        all_shifts = shift_types_8h + shift_types_3h

        employees = {eid: d for eid, d in self.dictDipendenti.items()
                     if d.daIncludere not in ['maternità', 'aspettativa']}

        # --- 2) Costruisci il modello CP-SAT ---
        model = cp_model.CpModel()
        x = {}  # x[(eid,day,shift)] = BoolVar
        is_assigned = {}
        has_rest = {}

        # Base: ogni employee in ogni giorno o lavora (1 turno) o riposa
        for eid, dip in employees.items():
            for d in days:
                a = model.NewBoolVar(f"asgn_{eid}_{d}")
                r = model.NewBoolVar(f"rest_{eid}_{d}")
                model.Add(a + r == 1)
                is_assigned[(eid, d)] = a
                has_rest[(eid, d)] = r

                for s in all_shifts:
                    b = model.NewBoolVar(f"x_{eid}_{d}_{s}")
                    x[(eid, d, s)] = b
                # se assegnato, esattamente un turno; se no, nessuno
                model.Add(sum(x[(eid, d, s)] for s in all_shifts) == a)

        # Copertura: ogni turno ogni giorno esattamente da 1 persona
        for d in days:
            for s in all_shifts:
                model.AddExactlyOne(x[(eid, d, s)] for eid in employees)

        # Quotes settimanali ≤ esigenze
        weeks = defaultdict(list)
        for d in days:
            w = d.isocalendar()[1]
            weeks[w].append(d)
        for eid, dip in employees.items():
            m_quota = int(dip.esigenzeMattiniSettimanali)
            p_quota = int(dip.esigenzePomeriggiSettimanali)
            n_quota = int(dip.esigenzeNottiSettimanali)
            for wdays in weeks.values():
                m_vars = [x[(eid, d, s)] for d in wdays for s in shift_types_8h[:4]]
                p_vars = [x[(eid, d, s)] for d in wdays for s in shift_types_8h[4:7]]
                n_vars = [x[(eid, d, 'notte')] for d in wdays]
                if m_vars: model.Add(sum(m_vars) <= m_quota)
                if p_vars: model.Add(sum(p_vars) <= p_quota)
                if n_vars: model.Add(sum(n_vars) <= n_quota)

        # --- 3) Risolvi ---
        solver = cp_model.CpSolver()
        status = solver.Solve(model)
        if status not in (cp_model.OPTIMAL, cp_model.FEASIBLE):
            raise RuntimeError("Nessuna soluzione valida per i vincoli dati")

            # --- 4) Estrai in struttura per DB e Excel, gestendo necessità e ferie in esubero ---
        db_schedule = []
        rows = []
        # Per contare i riposi settimanali
        rest_quota = {}  # eid -> quoziente di riposi settimanali
        for eid, dip in employees.items():
            # FTN full-time normale → 2 riposi/settimana; PTN part-time notte → 3
            rest_quota[eid] = 2 if dip.tipoContratto == 'FTN' else 3

        # Raggruppa i giorni per settimana ISO
        weeks = defaultdict(list)
        for d in days:
            weeks[d.isocalendar()[1]].append(d)

        for eid, dip in employees.items():
            name = f"{dip.nome} {dip.cognome} (ID:{eid})"
            prefs = dip.dizionarioNecessita
            # Conta riposi "normali" assegnati in ogni settimana
            assigned_rests = {w: [] for w in weeks}

            # Prima pass: estrai turno o riposo per ogni giorno
            daily_assignment = {}
            for d in days:
                # Gestione assenze obbligatorie in base a prefs
                if prefs.get('permessi_ferie', {}).get(d.day):
                    tag = 'FERIE'
                elif prefs.get('mutua_infortunio', {}).get(d.day):
                    tag = 'MUTUA'
                elif prefs.get('non_retribuite', {}).get(d.day):
                    tag = 'NR'
                else:
                    # Assegna turno o riposo generico
                    found = False
                    for s in all_shifts:
                        if solver.Value(x[(eid, d, s)]) == 1:
                            tag = s
                            found = True
                            break
                    if not found:
                        tag = 'RIPOSO'
                        week = d.isocalendar()[1]
                        assigned_rests[week].append(d)

                daily_assignment[d] = tag

            # Seconda pass: trasformiamo in FERIE i riposi "in esubero"
            for week, rest_days in assigned_rests.items():
                quota = rest_quota[eid]
                # I primi `quota` rest_days restano "RIPOSO", il resto diventano "FERIE"
                for extra_day in rest_days[quota:]:
                    daily_assignment[extra_day] = 'FERIE'

            # Popola db_schedule e rows
            for d, tag in daily_assignment.items():
                ore = 8 if tag in shift_types_8h else (
                    3 if tag in shift_types_3h else (8 * 0.8 if tag in ['FERIE', 'MUTUA'] else 0))
                note = ""
                if tag == 'FERIE' and not prefs.get('permessi_ferie', {}).get(d.day):
                    # ferie "in esubero"
                    note = "Ferie auto"
                db_schedule.append({
                    'data_turno': d.isoformat(),
                    'codice_dipendente': eid,
                    'tipo_turno': tag,
                    'ore_assegnate': ore,
                    'note': note
                })
                rows.append({'Dipendente': name, 'Giorno': d.day, 'Turno': tag})
        # Sovrascrivi DB
        self.dao.save_turni_mese(year, month, db_schedule)

        # --- 5) Esporta in Excel con formattazione ---
        df = pd.DataFrame(rows)
        pivot = df.pivot(index='Dipendente', columns='Giorno', values='Turno')
        filename = f"turni_{year}_{month:02d}.xlsx"
        with pd.ExcelWriter(filename, engine='openpyxl') as writer:
            pivot.to_excel(writer, sheet_name='Turni')
            wb = writer.book
            ws = writer.sheets['Turni']

            # Intestazioni in grassetto e centralizzate
            for cell in ws[1]:
                cell.font = Font(bold=True)
                cell.alignment = Alignment(horizontal='center')

            # Colori per tipo turno
            color_map = {
                'mat_': 'FFF2CC',  # mattina
                'pom_': 'D9EAD3',  # pomeriggio
                'notte': 'CFE2F3',
                'mj': 'F4CCCC',
                'pc': 'EAD1DC',
                'RIP': 'FFFFFF'
            }
            for row in ws.iter_rows(min_row=2, min_col=2, max_col=1 + len(days)):
                for cell in row:
                    val = str(cell.value or '')
                    for key, col in color_map.items():
                        if key in val:
                            cell.fill = PatternFill("solid", fgColor=col)
                            break

            # Regola larghezza colonne
            for idx, column_cells in enumerate(ws.columns, 1):
                length = max(len(str(c.value)) for c in column_cells) + 2
                ws.column_dimensions[get_column_letter(idx)].width = length

        print(f"File Excel generato e formattato: {filename}")
        return filename