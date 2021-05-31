from pipeline.airports_traffic_data_extractor import extract_traffic_data
from pipeline.italian_airports_data_extractor import extract_airports
from pipeline.combinator import combine_airports_and_traffic_data

if __name__ == '__main__':
    extract_traffic_data()
    extract_airports()
    combine_airports_and_traffic_data()
