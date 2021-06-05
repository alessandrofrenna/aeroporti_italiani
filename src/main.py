from pipeline import files_are_present
from pipeline.airports_traffic_data_extractor import extract_traffic_data
from pipeline.italian_airports_data_extractor import extract_airports
from pipeline.combinator import combine_airports_and_traffic_data
from pipeline.rdf_triples_generator import extract_rdf_from_data

if __name__ == '__main__':
    if files_are_present():
        print("Files already in the data directory, skipping elaboration pipeline")
    else:
        print("Files are not in the data directory, elaboration pipeline is starting...\n")
        extract_traffic_data()
        extract_airports()
        combine_airports_and_traffic_data()
    # Let's create the RDF turtle file
    extract_rdf_from_data()