from pathlib import Path

INPUT_ENAV_2020_PDF_FILE = "../input/DATI_DI_TRAFFICO_2020.pdf"
INPUT_ISTAT_2019_CSV_FILE = "../input/DCSC_INDTRAEREO_24052021180717528.csv"
INPUT_AIRPORTS_CSV_FILE = "../input/anagrafica-aereoporti-nuovo-dataset.csv"
AIRPORTS_TRAFFIC_2020 = "../data/traffico_aereo_2020.csv"
AIRPORTS_TRAFFIC_2019 = "../data/traffico_aereo_2019.csv"
ITALIAN_AIRPORTS = "../data/aeroporti_italiani.csv"
COMBINED_DATA = "../data/variazioni_traffico_aereo_2019_2020.csv"


def files_are_present():
    files = [AIRPORTS_TRAFFIC_2019, AIRPORTS_TRAFFIC_2020, ITALIAN_AIRPORTS, COMBINED_DATA]
    if any([Path(file).is_file() for file in files]):
        return True
    else:
        return False
