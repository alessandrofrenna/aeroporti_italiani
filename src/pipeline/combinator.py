import pandas
import numpy as np
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
    print("Saving combined airports and traffic data to the disk...")
    combined_traffic_data.to_csv(COMBINED_DATA, header=columns, index=False)


def __traffic_reducer(data_frame, year):
    return data_frame[["Aeroporto", "Categoria", "Anno", "Valore"]]\
        .groupby(["Aeroporto", "Categoria"])["Valore"]\
        .sum()\
        .reset_index(name="Valore " + str(year))


def __combine_traffic_data(traffic_2019, traffic_2020):
    combined = pandas.merge(traffic_2019, traffic_2020, on=["Aeroporto", "Categoria"])
    conditions = [
        (combined["Valore 2019"] == 0) & (combined["Valore 2020"] == 0),
        (combined["Valore 2019"] == 0),
        (combined["Valore 2019"] != 0)
    ]
    values = [
        0.0,
        100.0,
        ((combined["Valore 2020"] - combined["Valore 2019"]) / combined["Valore 2019"]) * 100,
    ]
    combined["Variazione Percentuale"] = np.round(np.select(conditions, values), decimals=2)
    return combined
