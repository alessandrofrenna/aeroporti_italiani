from os import environ
from pathlib import Path
base_path = environ["AEROPORTI_ITALIANI_LOCATION"]
INPUT_ENAV_2020_PDF_FILE = base_path + "/input/DATI_DI_TRAFFICO_2020.pdf"
INPUT_ISTAT_2019_CSV_FILE = base_path + "/input/DCSC_INDTRAEREO_24052021180717528.csv"
INPUT_AIRPORTS_CSV_FILE = base_path + "/input/anagrafica-aereoporti-nuovo-dataset.csv"
AIRPORTS_TRAFFIC_2020 = base_path + "/data/traffico_aereo_2020.csv"
AIRPORTS_TRAFFIC_2019 = base_path + "/data/traffico_aereo_2019.csv"
ITALIAN_AIRPORTS = base_path + "/data/aeroporti_italiani.csv"
COMBINED_DATA = base_path + "/data/variazioni_traffico_aereo_2019_2020.csv"
RDF_TURTLE_FILE = base_path + "/aeroporti_italiani.ttl"


def files_are_present():
    files = [AIRPORTS_TRAFFIC_2019, AIRPORTS_TRAFFIC_2020, ITALIAN_AIRPORTS, COMBINED_DATA]
    if any([Path(file).is_file() for file in files]):
        return True
    else:
        return False
