import re
import pandas
from geopy import geocoders, Point
from . import AIRPORTS_TRAFFIC_2020, INPUT_AIRPORTS_CSV_FILE, ITALIAN_AIRPORTS
# Default airports name as in the traffic data files
it_airports_names = pandas.read_csv(AIRPORTS_TRAFFIC_2020)["Aeroporto"].unique()
# Nominatim instance to get detailed address information
nominatim = geocoders.Nominatim(user_agent="italian_airports")
# Output dataframe columns headers
columns = [
    "Aeroporto",
    "Nome Commerciale",
    "Eponimi",
    "ICAO",
    "IATA",
    "Gestore",
    "Indirizzo",
    "Comune",
    "Provincia",
    "Regione",
    "Paese",
    "ISO Paese",
    "Latitudine",
    "Longitudine"
]


def extract_airports():
    print("Extracting and cleaning airports data...")
    data_f = pandas.read_csv(INPUT_AIRPORTS_CSV_FILE, encoding="cp1252")
    data_f = __normalize_airports_names(data_f)
    airports_data_frame = pandas.DataFrame(__clean_enac_airports_dataset(data_f), columns=columns)
    airports_data_frame = __add_missing_airports(airports_data_frame)
    airports_data_frame.index.name = "Id"
    print("Saving airports data to the disk...")
    airports_data_frame.to_csv(ITALIAN_AIRPORTS, header=columns)


def __clean_enac_airports_dataset(data_frame):
    eponyms = __extract_airports_eponyms(data_frame["NOME COMMERCIALE"].unique())
    raw_airports = []
    for index, df_row in data_frame.iterrows():
        if "\r\n" in df_row["NOME COMMERCIALE"]:
            commercial_name = df_row["NOME COMMERCIALE"].split("\r\n")[0]
        else:
            commercial_name = df_row["NOME COMMERCIALE"]
        if "Karol Wojty?a" in commercial_name:
            commercial_name = commercial_name.replace("Karol Wojty?a", "Karol Wojtyła")
        if "Pietro Savorgnan di Brazz\u00ef\u00bf\u00bd" in commercial_name:
            commercial_name = commercial_name.replace(
                "Pietro Savorgnan di Brazz\u00ef\u00bf\u00bd",
                "Pietro Savorgnan di Brazzà"
            )
        longitude = df_row["LON (EPSG:4326)"]
        latitude = df_row["LAT (EPSG:4326)"]
        result = nominatim.reverse(Point(latitude, longitude), language="it")
        address = result.raw["address"]
        # Let's get the municipality of the address got from nominatim
        if "city" in address:
            municipality = address["city"]
        elif "town" in address:
            municipality = address["town"]
        elif "suburb" in address:
            municipality = address["suburb"]
        elif "village" in address:
            municipality = address["village"]
        else:
            municipality = ""
        # Let's get the province information
        if "province" in address:
            province = address["province"]
        elif "county" in address:
            province = address["county"]
        else:
            province = ""
        raw_airports.append([
            df_row["AEROPORTO"],
            commercial_name,
            ", ".join(eponyms[df_row["NOME COMMERCIALE"]]),
            df_row["CODICE ICAO"],
            df_row["CODICE IATA"],
            df_row["GESTORE"],
            df_row["INDIRIZZO"],
            municipality,
            re.sub(r" Capitale|Città metropolitana di ", "", province).strip(),
            address["state"],
            address["country"],
            address["country_code"].upper(),
            latitude,
            longitude
        ])
    return raw_airports


def __normalize_airports_names(data_frame):
    df_airports_names = data_frame["AEROPORTO"].unique()
    it_ap_names_set = set([ap.upper() for ap in it_airports_names])
    airports_intsect = list(it_ap_names_set.intersection(set(df_airports_names)))
    airports_intsect_capitalized = [" ".join([tok.capitalize() for tok in ap.split(" ")]) for ap in airports_intsect]
    airports_lut = dict(zip(airports_intsect, airports_intsect_capitalized))
    difference = it_ap_names_set.difference(airports_intsect)
    for airport in difference:
        if len(tokens := airport.split(" ")) > 1:
            name_to_match = tokens[0].lower()
        else:
            name_to_match = airport.lower()
        matching = [ap_name for ap_name in df_airports_names if name_to_match in ap_name.lower()]
        if len(matching) > 0:
            airports_lut[matching[0]] = " ".join([ap.capitalize() for ap in airport.split(" ")])
    # We have to normalize also the forlì airport name if it exists in the list
    forli_list = [ap for ap in df_airports_names if "FORLI\u00ef\u00bf\u00bd" in ap]
    if len(forli_list) != 0:
        airports_lut[forli_list[0]] = "Forlì"
        airports_lut.pop("FORL\u00cc", None)
    data_frame["AEROPORTO"] = data_frame["AEROPORTO"].map(airports_lut)
    return data_frame


def __add_missing_airports(data_frame):
    df_airports_set = set(data_frame["Aeroporto"].unique())
    difference = set(it_airports_names).difference(df_airports_set)
    # The only missing elements should be "Pantelleria's airport"
    if "Pantelleria" in difference:
        result = nominatim.geocode("Airport of Pantelleria", country_codes="IT", addressdetails=True)
        address = result.raw["address"]
        latitude = float(result.raw["lat"])
        longitude = float(result.raw["lon"])
        row = [
            "Pantelleria",
            address["aeroway"],
            "Italo D'Amico",
            "LICG",
            "PNL",
            "G.A.P. S.P.A.",
            " ".join([" - ".join([address["road"], address["postcode"]]), address["village"], "(TP)"]),
            address["village"],
            address["county"],
            address["state"],
            address["country"],
            address["country_code"].upper(),
            latitude,
            longitude
        ]
        data_frame = data_frame.append(pandas.Series(row, index=columns), ignore_index=True)
    return data_frame


def __extract_airports_eponyms(commercial_names):
    italian_eponyms = {}
    not_allowed = ["Riviera del Corallo", "Papola Casale", "Costa Smeralda"]
    # Let's check if the extracted data from wikipedia are in the airport
    for c_name in commercial_names:
        indexes = [index for index, char in enumerate(c_name) if char == '"']
        if len(indexes) < 2:
            italian_eponyms[c_name] = []
            continue
        entitled_to = c_name[indexes[0] + 1: indexes[1]]
        if entitled_to not in not_allowed:
            if "Falcone e Borsellino" == entitled_to:
                entitled_to = ["Giovanni Falcone", "Paolo Borsellino"]
            elif "Il Caravaggio" == entitled_to:
                entitled_to = ["Caravaggio"]
            elif "Karol Wojty?a" == entitled_to:
                entitled_to = ["Karol Wojtyła"]
            elif "Pietro Savorgnan di Brazz\u00ef\u00bf\u00bd" == entitled_to:
                entitled_to = ["Pietro Savorgnan di Brazzà"]
            else:
                entitled_to = [entitled_to]
        else:
            entitled_to = []
        italian_eponyms[c_name] = entitled_to
        # print(c_name, "=", entitled_to)
    return italian_eponyms
