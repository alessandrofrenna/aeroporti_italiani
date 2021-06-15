import re
import pandas
import pdfplumber
from . import INPUT_ENAV_2020_PDF_FILE, INPUT_ISTAT_2019_CSV_FILE, AIRPORTS_TRAFFIC_2019, AIRPORTS_TRAFFIC_2020
# Output CSV file column headers
columns = ["Aeroporto", "Categoria", "Origine", "Valore", "Anno"]


def extract_traffic_data():
    print("Extracting and cleaning 2019 and 2020 airports traffic data...")
    traffic_data_2020 = extract_enac_2020_traffic_data()
    traffic_data_2019 = extract_istat_2019_traffic_data()
    traffic_data_2019, traffic_data_2020 = __normalize_extracted_traffic_data((traffic_data_2019, traffic_data_2020))
    # traffic_data_2020.index.name = "Id"
    print("Saving 2020's traffic data to the disk...")
    traffic_data_2020.to_csv(AIRPORTS_TRAFFIC_2020, header=columns, index=False)
    # traffic_data_2019.index.name = "Id"
    print("Saving 2019's traffic data to the disk...")
    traffic_data_2019.to_csv(AIRPORTS_TRAFFIC_2019, header=columns, index=False)


def extract_istat_2019_traffic_data():
    data_f = pandas.read_csv(INPUT_ISTAT_2019_CSV_FILE)
    data_f["Value"] = data_f["Value"].fillna(0)
    # Let's change traffic origin column values
    data_f["Indicatori trasporto aereo"] = data_f["Indicatori trasporto aereo"].map({
        "passeggeri trasportati": "passeggeri",
        "movimenti commerciali": "voli commerciali",
        "merce e posta trasportate - tonnellate": "merci e posta",
    })
    # Let's change traffic transport indicator column values
    data_f["Tipo di servizio aereo"] = data_f["Tipo di servizio aereo"].map({
        "voli interni": "nazionale",
        "voli internazionali": "internazionale"
    })
    # Let's select 2019 traffic data values
    filtered_data = data_f[
        (data_f["TIME"] == "2019") &
        (data_f["Arrivo-Partenza                  "] == "Totale") &
        (data_f["Aeroporti "] != "Totale")
    ]
    return pandas.DataFrame(
        __istat_traffic_data_extractor(filtered_data),
        columns=columns
    )


def extract_enac_2020_traffic_data():
    with pdfplumber.open(INPUT_ENAV_2020_PDF_FILE) as raw_pdf:
        raw_traffic_data = __pdf_traffic_data_tables_extractor(raw_pdf, pages=[31, 33], bbox=(80, 200, 520, 740))
    return pandas.DataFrame(
        __enac_traffic_data_cleaner(raw_traffic_data),
        columns=columns
    )


def __pdf_traffic_data_tables_extractor(pdf, pages, bbox):
    extracted_data = []
    for page in pages:
        cells_list = [
            row.replace(".", "").replace(",", ".").replace("%", "").split(" ")
            for row in pdf.pages[page].within_bbox(bbox).extract_text().split("\n")
        ]
        parsed = []
        for cells in cells_list:
            index = 0
            airport_name_components = []
            for index in range(1, len(cells)):
                try:
                    float(cells[index])
                    break
                except ValueError:
                    airport_name_components.append((cells[index]))
            parsed.append([cells[0], " ".join(airport_name_components)] + cells[index: len(cells)])
        extracted_data.append(parsed)
    return enumerate(extracted_data)


def __enac_traffic_data_cleaner(raw_traffic_data):
    national_traffic_data = []
    for index, table in raw_traffic_data:
        for cols in table:
            if len(cols) > 8:
                continue
            airport = " ".join([token.capitalize() for token in cols[1].lower().split(" ")]).replace("S ", "S. ")
            movements = [airport, "voli commerciali"]
            travellers = [airport, "passeggeri"]
            cargo = [airport, "merci e posta"]
            if 0 == index:
                mov = list.copy(movements) + ["nazionale", int(cols[2]), 2020]
                trav = list.copy(travellers) + ["nazionale", int(cols[4]), 2020]
                carg = list.copy(cargo) + ["nazionale", float(cols[6]), 2020]
                national_traffic_data += [mov, trav, carg]
            else:
                mov = list.copy(movements) + ["internazionale", int(cols[2]), 2020]
                trav = list.copy(travellers) + ["intarnazionale", int(cols[4]), 2020]
                carg = list.copy(cargo) + ["internazionale", float(cols[6]), 2020]
                national_traffic_data += [mov, trav, carg]
    return national_traffic_data


def __istat_traffic_data_extractor(data_f):
    # Let's get only valid data
    allowed = ["nazionale", "internazionale"]
    data_f = data_f[data_f["Tipo di servizio aereo"].isin(allowed)]
    # We create a pandas data-frame in which we get all traffic data grouped by airport,
    # traffic origin, and traffic transport indicator
    group_by = data_f.groupby(
        ["Aeroporti ", "Indicatori trasporto aereo", "Tipo di servizio aereo"]
    )["Value"].sum().reset_index(name="Value")
    group_by["Anno"] = 2019
    traffic_data_list = group_by.values.tolist()
    # Now, we have to normalize airports names because they can have trailing spaces or dashes or other bad chars
    for data in traffic_data_list:
        name = data[0]
        name = name.replace("-", " ").strip()
        data[0] = re.sub(r"San |Sant\'", "S. ", name)
    return traffic_data_list


def __normalize_extracted_traffic_data(traffic_data_tuple):
    missing_airports = []
    traffic_2019, traffic_2020 = traffic_data_tuple
    istat_airports_denomination = traffic_2019["Aeroporto"].unique()
    enac_airports_denomination = traffic_2020["Aeroporto"].unique()
    airports_difference = list(set(enac_airports_denomination).difference(set(istat_airports_denomination)))
    airports_intersection = list(set(enac_airports_denomination).intersection(set(istat_airports_denomination)))
    airports_lut = dict(zip(airports_intersection, airports_intersection))
    for index, airport in enumerate(airports_difference):
        if len(tokens := airport.split(" ")) > 1:
            name_to_match = tokens[0]
        else:
            name_to_match = airport
        matching = [ap_name for ap_name in istat_airports_denomination if name_to_match in ap_name]
        if len(matching) > 0 and matching[0] != airport:
            airports_lut[matching[0]] = airport
        else:
            airports_lut[airport] = airport
            missing_airports.append(airport)
    traffic_2019["Aeroporto"] = traffic_2019["Aeroporto"].map(airports_lut)
    for airport in missing_airports:
        rows_to_add = [
            [airport, "passeggeri", "internazionale", 0.0, 2019],
            [airport, "passeggeri", "nazionale", 0.0, 2019],
            [airport, "merci e posta", "internazionale", 0.0, 2019],
            [airport, "merci e posta", "nazionale", 0.0, 2019],
            [airport, "voli commerciali", "internazionale", 0.0, 2019],
            [airport, "voli commerciali", "nazionale", 0.0, 2019]
        ]
        rows_to_add = [pandas.Series(row, index=traffic_2019.columns) for row in rows_to_add]
        traffic_2019 = traffic_2019.append(rows_to_add, ignore_index=True)
    return traffic_2019, traffic_2020
