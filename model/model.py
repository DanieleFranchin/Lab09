from database.parco_DAO import ParcoDAO
from database.escursione_DAO import EscursioneDAO
from database.punto_interesse_DAO import PuntoInteresseDAO

class Model:
    def __init__(self):
        self.escursioni_map = {} # Mappa ID escursione -> oggetti Escursione
        self.punti_interesse_map = {} # Mappa ID punto di interesse -> oggetti PuntoInteresse
        self.escursioni_punti_interesse = []
        self.lista_escursioni = []
        self.opzioni = []

        self._pacchetto_ottimo = []
        self._valore_ottimo: int = -1
        self._costo = 0

        # TODO: Aggiungere eventuali altri attributi

        # Caricamento
        self.load_escursioni()
        self.load_punti_interesse()
        self.load_relazioni()

    @staticmethod
    def load_parchi():
        """ Restituisce tutti i parchi disponibili """
        return ParcoDAO.get_parchi()

    def load_escursioni(self):
        """ Carica tutte le escursioni in un dizionario [id, Escursione]"""
        self.escursioni_map = EscursioneDAO.get_escursioni()

    def load_punti_interesse(self):
        """ Carica tutti i punti di interesse in un dizionario [id, PuntoInteresse]"""
        self.punti_interesse_map = PuntoInteresseDAO.get_punti_interesse()

    def load_relazioni(self):
        """
            Interroga il database per ottenere tutte le relazioni fra escursioni e punti di interesse e salvarle nelle strutture dati
            Collega escursione <-> punti di interesse.
            --> Ogni Escursione ha un set di PuntoInteresse.
            --> Ogni PuntoInteresse ha un set di Escursioni.
        """
        self.escursioni_punti_interesse = EscursioneDAO.get_escursioni_punti_interesse()
        for legame in self.escursioni_punti_interesse:
            self.escursioni_map[legame["id_escursione"]].punti_interesse.add(self.punti_interesse_map[legame["id_punto_interesse"]])
            if legame["id_escursione"] not in self.punti_interesse_map[legame["id_punto_interesse"]].escursioni:
                self.punti_interesse_map[legame["id_punto_interesse"]].escursioni.add(self.escursioni_map[legame["id_escursione"]])

    def genera_pacchetto(self, id_parco: str, max_giorni: int = None, max_budget: float = None):
        """
        Calcola il pacchetto di escursioni ottimale per un parco rispettando i vincoli di durata, budget e punti di interesse unici.
        :param id_parco: id del parco
        :param max_giorni: numero massimo di giorni (può essere None --> nessun limite)
        :param max_budget: costo massimo del pacchetto (può essere None --> nessun limite)

        :return: self._pacchetto_ottimo (una lista di oggetti Escursione)
        :return: self._costo (il costo del pacchetto)
        :return: self._valore_ottimo (il voto complessivo dei visitatori per il pacchetto)
        """
        self._pacchetto_ottimo = []
        self._costo = 0
        self._valore_ottimo = -1
        self.id_parco = id_parco
        self.max_giorni = max_giorni
        self.max_budget = max_budget

        self._ricorsione([], 0, 0, 0, set())

        return self._pacchetto_ottimo, self._costo, self._valore_ottimo

    def _ricorsione(self, pacchetto_parziale: list, durata_corrente: int, costo_corrente: float, valore_corrente: int, punti_usati: set):
        """ Algoritmo di ricorsione che deve trovare il pacchetto che massimizza il voto complessivo dei visitatori"""
        if self._valore_ottimo == -1:
            parchi = self.load_parchi()
            for parco in parchi:
                if parco.id == self.id_parco:
                    for key in self.escursioni_map:
                        if self.escursioni_map[key].id_parco == parco.id:
                            somma = 0
                            for punto in self.escursioni_map[key].punti_interesse:
                                somma += punto.voto_visitatori
                            rapporto = (somma / self.escursioni_map[key].durata_giorni) / self.escursioni_map[key].costo
                            escursione = {"id": key, "rapporto": rapporto, "durata": self.escursioni_map[key].durata_giorni, "costo": self.escursioni_map[key].costo, "valore": somma}
                            self.opzioni.append(escursione)
            self.opzioni.sort(key=lambda escursione: escursione["rapporto"], reverse=True)
            self._valore_ottimo += 1

        if len(self.opzioni) == len(punti_usati):
            self._costo = costo_corrente
            self._valore_ottimo = valore_corrente
            self._pacchetto_ottimo = pacchetto_parziale
            return

        else:
            for opzione in self.opzioni:
                if opzione["id"] not in punti_usati:
                    if opzione["costo"]+costo_corrente<=self.max_budget and opzione["durata"]+durata_corrente <= self.max_giorni:
                        punti_usati.add(opzione["id"])
                        pacchetto_parziale.append(self.escursioni_map[opzione["id"]])
                        self._ricorsione(pacchetto_parziale, opzione["durata"]+durata_corrente, opzione["costo"]+costo_corrente, valore_corrente+opzione["valore"], punti_usati)
                    else:
                        punti_usati.add(opzione["id"])
                        self._ricorsione(pacchetto_parziale, durata_corrente, costo_corrente, valore_corrente,
                                         punti_usati)