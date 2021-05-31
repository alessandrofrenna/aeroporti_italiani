import pandas
from decimal import Decimal
from . import AIRPORTS_TRAFFIC_2019, AIRPORTS_TRAFFIC_2020, COMBINED_DATA, ITALIAN_AIRPORTS
# Combined output columns
columns = ["Aeroporto", "Categoria", "Valore 2020", "Valore 2019", "Variazione Percentuale"]


def combine_airports_and_traffic_data():
    print("Combining airports and traffic data...")
    italian_airports = pandas.read_csv(ITALIAN_AIRPORTS)
    airports_name_icao_lut = dict(zip(italian_airports["Aeroporto"], italian_airports["ICAO"]))
    traffic_2019 = pandas.read_csv(AIRPORTS_TRAFFIC_2019)
    traffic_2020 = pandas.read_csv(AIRPORTS_TRAFFIC_2020)
    traffic_2019["Aeroporto"] = traffic_2019["Aeroporto"].map(airports_name_icao_lut)
    traffic_2020["Aeroporto"] = traffic_2020["Aeroporto"].map(airports_name_icao_lut)
    traffic_2019.to_csv(AIRPORTS_TRAFFIC_2019, index=False)
    traffic_2020.to_csv(AIRPORTS_TRAFFIC_2020, index=False)
    combined_traffic_data = pandas.DataFrame(
        __combine_traffic_data(
            __traffic_reducer(traffic_2019, 2019),
            __traffic_reducer(traffic_2020, 2020)
        ),
        columns=columns
    )
    combined_traffic_data.index.name = "Id"
    print("Saving combined airports and traffic data to the disk...")
    combined_traffic_data.to_csv(COMBINED_DATA, header=columns)


def __traffic_reducer(data_frame, year):
    traffic_data = {}
    grouped_by = data_frame[["Aeroporto", "Categoria", "Valore"]].groupby(["Aeroporto", "Categoria"])
    for group, frame in grouped_by:
        airport, category = group
        value = frame["Valore"].sum()
        traffic_dict = {
            "value": value,
            "year": year
        }
        if airport in traffic_data:
            if category in traffic_data[airport]:
                traffic_data[airport][category].append(traffic_dict)
            else:
                traffic_data[airport][category] = [traffic_dict]
        else:
            traffic_data[airport] = {
                category: [traffic_dict]
            }
    return traffic_data


def __combine_traffic_data(traffic_2019, traffic_2020):
    combined_dict = {}
    combined_rows = []
    airports = traffic_2019.keys()
    for airport in airports:
        by_category = {}
        for cat in traffic_2019[airport]:
            by_category[cat] = traffic_2019[airport][cat]
        for cat in traffic_2020[airport]:
            by_category[cat] += traffic_2020[airport][cat]
        combined_dict[airport] = by_category
    for airport in combined_dict:
        for cat in combined_dict[airport]:
            data = combined_dict[airport][cat]
            if len(data) != 2:
                continue
            if data[0]["year"] == 2019:
                value_2019 = data[0]["value"]
                value_2020 = data[1]["value"]
            else:
                value_2020 = data[0]["value"]
                value_2019 = data[1]["value"]
            # Let's check what values we have to prevent division by 0
            if value_2019 == 0 and value_2020 == 0:
                variation = 0.0
            elif value_2019 == Decimal(0.0):
                variation = Decimal(100.0)
            else:
                variation = ((Decimal(value_2020) - Decimal(value_2019)) / Decimal(value_2019)) * 100
            combined_rows.append([airport, cat, value_2020, value_2019, round(variation, 2)])
    return combined_rows
