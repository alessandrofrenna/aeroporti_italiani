import pandas
from decimal import Decimal
from rdflib import Graph, RDF, RDFS, URIRef, Literal, XSD
from rdflib.namespace import Namespace
from SPARQLWrapper import SPARQLWrapper, JSON
from . import ITALIAN_AIRPORTS, AIRPORTS_TRAFFIC_2019, AIRPORTS_TRAFFIC_2020, COMBINED_DATA, RDF_TURTLE_FILE
# Domain base URIs
ns_domain = "http://purl.org/net/italian_airports/ontology#"
base_domain = "http://purl.org/net/italian_airports/resources"
dbpedia_domain = "http://dbpedia.org/resource/"
# SPARQL Wikidata
sparql = SPARQLWrapper("https://query.wikidata.org/sparql")
# Namespaces
aio = Namespace(ns_domain)
schema = Namespace("https://schema.org")
geo = Namespace("https://schema.org/GeoCoordinates")
address = Namespace("https://schema.org/PostalAddress")
owl = Namespace("http://www.w3.org/2002/07/owl")


def extract_rdf_from_data():
    print("Generating RDF/Turtle file from extracted data...")
    g = Graph()
    g.bind("aio", aio)
    g.bind("schema", schema)
    g.bind("geo", geo)
    g.bind("schema", schema)
    g.bind("addr", address)
    g.bind("owl", owl)
    data_frame = pandas.read_csv(ITALIAN_AIRPORTS)
    # Country type definition for Italy
    country_uri = URIRef(base_domain + "/countries/IT")
    g.add((country_uri, RDF.type, aio.Country))
    g.add((country_uri, RDFS.label, Literal("Italia", datatype=XSD.string)))
    g.add((country_uri, aio.countryCode, Literal("IT", datatype=XSD.string)))
    g.add((country_uri, owl.sameAs, URIRef(dbpedia_domain + "Italia")))
    # Let's get airports from wikidata and let's use them to link data with its knowledge base
    wikidata_airports = __get_wikidata_italian_airports_uri()
    # Let's iterate through the rows of the airports csv to add triples to RDF/Turtle file
    for _, row in data_frame.iterrows():
        # Place location triple definitions
        urified_city = __urify_string(row["Comune"])
        urified_province = __urify_string(row["Provincia"])
        urified_region = __urify_string(row["Regione"])
        city_uri = URIRef(base_domain + "/cities/" + urified_city)
        province_uri = URIRef(base_domain + "/provinces/" + urified_province)
        region_uri = URIRef(base_domain + "/regions/" + urified_region)
        coordinates_uri = URIRef(base_domain + "/geo/" + row["ICAO"] + "-Geo")
        location_uri = URIRef(base_domain + "/locations/" + row["ICAO"] + "-Location")
        # Province type definition
        g.add((province_uri, RDF.type, aio.Province))
        g.add((province_uri, RDFS.label, Literal(row["Provincia"], datatype=XSD.string)))
        # City type definition
        g.add((city_uri, RDF.type, aio.City))
        g.add((city_uri, RDFS.label, Literal(row["Comune"], datatype=XSD.string)))
        # Region type definition
        g.add((region_uri, RDF.type, aio.Region))
        g.add((region_uri, RDFS.label, Literal(row["Regione"], datatype=XSD.string)))
        # Location type definition
        g.add((location_uri, RDF.type, aio.Location))
        # Let's create a GeoCoordinates instance
        g.add((coordinates_uri, RDF.type, schema.GeoCoordinates))
        g.add((coordinates_uri, geo.latitude, Literal(row[13], datatype=XSD.decimal)))
        g.add((coordinates_uri, geo.longitude, Literal(row[14], datatype=XSD.decimal)))
        g.add((coordinates_uri, geo.address, Literal(row[7], datatype=XSD.string)))
        # Let's add City, Province and Region object properties
        g.add((region_uri, aio.hasProvince, province_uri))
        g.add((region_uri, aio.inCountry, country_uri))
        g.add((province_uri, aio.hasCity, city_uri))
        g.add((province_uri, aio.inRegion, region_uri))
        g.add((province_uri, aio.inCountry, country_uri))
        g.add((city_uri, aio.inProvinceOf, province_uri))
        g.add((city_uri, aio.inRegion, region_uri))
        g.add((city_uri, aio.inCountry, country_uri))
        # Let's add object properties to Location type
        g.add((location_uri, aio.city, city_uri))
        g.add((location_uri, aio.province, province_uri))
        g.add((location_uri, aio.region, region_uri))
        g.add((location_uri, aio.country, country_uri))
        g.add((location_uri, aio.geoAddress, location_uri))
        # Let's add OWL sameAs to City, Province and Region types
        g.add((province_uri, owl.sameAs, URIRef(dbpedia_domain + urified_province)))
        g.add((city_uri, owl.sameAs, URIRef(dbpedia_domain + urified_city)))
        g.add((region_uri, owl.sameAs, URIRef(dbpedia_domain + urified_region)))
        # Let's handle airport and managing authorities
        airport_uri = URIRef(base_domain + "/airports/" + row["ICAO"])
        authority_url = URIRef(base_domain + "/authority/" + row["ICAO"] + "-Manager")
        # ManagingAuthority type definition
        g.add((authority_url, RDF.type, aio.ManagingAuthority))
        g.add((authority_url, RDFS.label, Literal(row["Gestore"], datatype=XSD.string)))
        # Airport type definition
        g.add((airport_uri, RDF.type, aio.Airport))
        g.add((airport_uri, RDFS.label, Literal(row["Aeroporto"], datatype=XSD.string)))
        g.add((airport_uri, aio.commercialName, Literal(row["Nome Commerciale"], datatype=XSD.string)))
        g.add((airport_uri, aio.icaoCode, Literal(row["ICAO"], datatype=XSD.string)))
        g.add((airport_uri, aio.iataCode, Literal(row["IATA"], datatype=XSD.string)))
        # Let's add Airport and ManagingAuthority object properties
        g.add((airport_uri, aio.isLocatedAt, location_uri))
        g.add((airport_uri, aio.isManagedBy, authority_url))
        g.add((airport_uri, aio.webSite, Literal(wikidata_airports[row["ICAO"]]["website"], datatype=XSD.anyURI)))
        g.add((authority_url, aio.isManagerOf, airport_uri))
        # Let's add OWL sameAs to City, Province and Region types
        g.add((airport_uri, owl.sameAs, URIRef(wikidata_airports[row["ICAO"]]["uri"])))
    # Let's add traffic data to the graph
    g = __add_traffic_data_to_graph(AIRPORTS_TRAFFIC_2019, g)
    g = __add_traffic_data_to_graph(AIRPORTS_TRAFFIC_2020, g)
    g = __add_traffic_data_to_graph(COMBINED_DATA, g)
    # Saving the turtle data
    print("Saving RDF/Turtle file to the disk...")
    g.serialize(RDF_TURTLE_FILE, format="turtle")


def __add_traffic_data_to_graph(csv_filename, graph):
    traffic_years_map = {
        AIRPORTS_TRAFFIC_2019: 2019,
        AIRPORTS_TRAFFIC_2020: 2020,
        COMBINED_DATA: "both"
    }
    # Add categories instances to the graph
    categories = ["merci e posta", "passeggeri", "voli commerciali"]
    for category in categories:
        uri = URIRef(base_domain + "/categories/" + __urify_string(category))
        # Category type definition
        graph.add((uri, RDF.type, aio.Category))
        graph.add((uri, RDFS.label, Literal(category, datatype=XSD.string)))
    # Let's add traffic data triples to the graph iterating through the data_frame rows
    data_frame = pandas.read_csv(csv_filename)
    year_to_add = traffic_years_map[csv_filename]
    for _, row in data_frame.iterrows():
        airport_uri = URIRef(base_domain + "/airports/" + row["Aeroporto"])
        category_uri = URIRef(base_domain + "/categories/" + __urify_string(row["Categoria"]))
        if year_to_add == "both":
            graph = __add_traffic_summary_triples(row, graph, category_uri, airport_uri)
        else:
            graph = __add_traffic_data_triples(row, graph, category_uri, airport_uri)
    return graph


def __add_traffic_data_triples(row, graph, category_uri, airport_uri):
    # Let's define the XSD type for traffic value
    if "merci" in row["Categoria"]:
        xsd_val_type = XSD.decimal
        value = Decimal(row["Valore"])
    else:
        xsd_val_type = XSD.integer
        value = int(row["Valore"])
    # We need to define the traffic URI according to its category, origin and year
    res_name = "-".join([row["Aeroporto"], __urify_string(row["Categoria"]), row["Origine"], str(row["Anno"])])
    traffic_uri = URIRef(base_domain + "/summaries/" + res_name)
    # Traffic type definition
    graph.add((traffic_uri, RDF.type, aio.TrafficData))
    graph.add((traffic_uri, aio.trafficOrigin, Literal(row["Origine"], datatype=XSD.string)))
    graph.add((traffic_uri, aio.value, Literal(value, datatype=xsd_val_type)))
    graph.add((traffic_uri, aio.year, Literal(row["Anno"], datatype=XSD.integer)))
    graph.add(
        (traffic_uri, RDFS.label, Literal(" ".join([row["Categoria"], str(row["Anno"])]), datatype=XSD.string))
    )
    # Let's add objects properties
    graph.add((airport_uri, aio.trafficData, traffic_uri))
    graph.add((traffic_uri, aio.hasCategory, category_uri))
    graph.add((traffic_uri, aio.belongsToAirport, airport_uri))
    graph.add((category_uri, aio.belongsToTrafficData, traffic_uri))
    return graph


def __add_traffic_summary_triples(row, graph, category_uri, airport_uri):
    # Let's define the XSD type for traffic value
    if "merci" in row["Categoria"]:
        xsd_val_type = XSD.decimal
        value_past = Decimal(row["Valore 2019"])
        value_present = Decimal(row["Valore 2020"])
    else:
        xsd_val_type = XSD.integer
        value_past = int(row["Valore 2019"])
        value_present = int(row["Valore 2020"])
    res_name = "-".join([row["Aeroporto"], __urify_string(row["Categoria"]), "2020-2019"])
    summary_uri = URIRef(base_domain + "/summaries/" + res_name)
    # TrafficSummary type definition
    graph.add((summary_uri, RDF.type, aio.TrafficSummary))
    graph.add((summary_uri, RDFS.label, Literal(" ".join([row["Categoria"], "2019-2020"]), datatype=XSD.string)))
    graph.add((summary_uri, aio.currentValue, Literal(value_present, datatype=xsd_val_type)))
    graph.add((summary_uri, aio.pastValue, Literal(value_past, datatype=xsd_val_type)))
    graph.add((summary_uri, aio.pastValue, Literal(value_past, datatype=xsd_val_type)))
    graph.add((summary_uri, aio.variation, Literal(Decimal(row["Variazione Percentuale"]), datatype=XSD.decimal)))
    # Let's add objects properties
    graph.add((airport_uri, aio.summaryData, summary_uri))
    graph.add((summary_uri, aio.hasCategory, category_uri))
    graph.add((summary_uri, aio.belongsToAirport, airport_uri))
    graph.add((category_uri, aio.belongsToSummaryData, summary_uri))
    return graph


def __get_wikidata_italian_airports_uri():
    query = """
        SELECT DISTINCT ?airport ?icao ?website
        WHERE { 
            ?airport wdt:P239 ?icao;
            wdt:P856 ?website.
            filter(strstarts(?icao,"LI"))
        }
    """
    sparql.setQuery(query)
    sparql.setReturnFormat(JSON)
    result_dict = {}
    raw_q_result = sparql.query().convert()
    bindings = {}
    if "results" in raw_q_result:
        if "bindings" in raw_q_result["results"]:
            bindings = raw_q_result["results"]["bindings"]
        else:
            raise ValueError("Query does not containes expected data")
    for raw in bindings:
        result_dict[raw["icao"]["value"]] = {
            "uri": raw["airport"]["value"],
            "website": raw["website"]["value"]
        }
    return result_dict


def __urify_string(original_string):
    return original_string.replace(" ", "_")
