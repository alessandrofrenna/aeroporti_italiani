import time
import pandas
import itertools
from decimal import Decimal
from urllib.error import HTTPError
from rdflib import Graph, RDF, RDFS, URIRef, Literal, XSD
from rdflib.namespace import Namespace
from SPARQLWrapper import SPARQLWrapper, JSON
from . import ITALIAN_AIRPORTS, AIRPORTS_TRAFFIC_2019, AIRPORTS_TRAFFIC_2020, COMBINED_DATA, RDF_TURTLE_FILE

# Domain base URIs
ns_domain = "http://purl.org/net/aeroporti_italiani/ontologia.owl/"
base_domain = "http://purl.org/net/aeroporti_italiani/risorse"
dbpedia_domain = "http://dbpedia.org/resource/"
# SPARQL Wikidata
sparql = SPARQLWrapper("https://query.wikidata.org/sparql")
# Namespaces
aio = Namespace(ns_domain)
schema = Namespace("https://schema.org")
geo = Namespace("https://schema.org/GeoCoordinates")
owl = Namespace("http://www.w3.org/2002/07/owl")


def extract_rdf_from_data():
    print("Generating RDF/Turtle file from extracted data...")
    g = Graph()
    g.bind("aio", aio)
    g.bind("schema", schema)
    g.bind("geo", geo)
    g.bind("schema", schema)
    g.bind("owl", owl)
    data_frame = pandas.read_csv(ITALIAN_AIRPORTS)
    # Country type definition for Italy
    country_uri = URIRef(base_domain + "/luoghi/Italia")
    g.add((country_uri, RDF.type, aio.Stato))
    g.add((country_uri, RDFS.label, Literal("Italia", datatype=XSD.string)))
    g.add((country_uri, aio.codicePaese, Literal("IT", datatype=XSD.string)))
    g.add((country_uri, owl.sameAs, URIRef(dbpedia_domain + "Italia")))
    # Let's get airports from wikidata and let's use them to link data with its knowledge base
    wikidata_airports = __get_italian_airports_from_wikidata()
    # Let's get humans from wikidata and let's use them to link data with its knowledge base
    wikidata_humans = __get_humans_from_wikidata(data_frame["Eponimi"].tolist())
    # Let's iterate through the rows of the airports csv to add triples to RDF/Turtle file
    for _, row in data_frame.iterrows():
        # Place location triple definitions
        urified_city = __urify_string(row["Comune"])
        urified_province = __urify_string(row["Provincia"])
        urified_region = __urify_string(row["Regione"])
        city_uri = URIRef(base_domain + "/luoghi/" + urified_city)
        province_uri = URIRef(base_domain + "/luoghi/" + urified_province)
        region_uri = URIRef(base_domain + "/luoghi/" + urified_region)
        coordinates_uri = URIRef(base_domain + "/geo/" + row["ICAO"] + "-Geo")
        location_uri = URIRef(base_domain + "/indirizi/" + row["ICAO"] + "-Indirizzo")
        # City type definition
        g.add((city_uri, RDF.type, aio.Comune))
        g.add((city_uri, RDFS.label, Literal(row["Comune"], datatype=XSD.string)))
        # Province, City type definition
        g.add((province_uri, RDF.type, aio.Provincia))
        g.add((province_uri, RDFS.label, Literal(row["Provincia"], datatype=XSD.string)))
        # Region type definition
        g.add((region_uri, RDF.type, aio.Regione))
        g.add((region_uri, RDFS.label, Literal(row["Regione"], datatype=XSD.string)))
        # Location type definition
        g.add((location_uri, RDF.type, aio.Indirizzo))
        # Let's create a GeoCoordinates instance
        g.add((coordinates_uri, RDF.type, schema.GeoCoordinates))
        g.add((coordinates_uri, geo.latitude, Literal(row["Latitudine"], datatype=XSD.decimal)))
        g.add((coordinates_uri, geo.longitude, Literal(row["Longitudine"], datatype=XSD.decimal)))
        g.add((coordinates_uri, geo.address, Literal(row["Indirizzo"], datatype=XSD.string)))
        # Let's add City, Province, Region, Location object properties and
        g.add((city_uri, aio.inProvinciaDi, province_uri))
        g.add((city_uri, aio.inRegione, region_uri))
        g.add((city_uri, aio.inStato, country_uri))
        g.add((province_uri, aio.èProvinciaDi, city_uri))
        g.add((province_uri, aio.inRegione, region_uri))
        g.add((province_uri, aio.inStato, country_uri))
        g.add((region_uri, aio.inStato, country_uri))
        g.add((region_uri, aio.haComune, city_uri))
        g.add((region_uri, aio.haProvincia, province_uri))
        g.add((location_uri, aio.comune, city_uri))
        g.add((location_uri, aio.regione, region_uri))
        g.add((location_uri, aio.stato, country_uri))
        g.add((location_uri, aio.geoDati, location_uri))
        g.add((location_uri, aio.provincia, province_uri))
        g.add((country_uri, aio.haZonaAmministrativa, region_uri))
        # Let's add OWL sameAs to City, Province and Region types
        g.add((city_uri, owl.sameAs, URIRef(dbpedia_domain + urified_city)))
        g.add((region_uri, owl.sameAs, URIRef(dbpedia_domain + urified_region)))
        g.add((province_uri, owl.sameAs, URIRef(dbpedia_domain + urified_province)))
        # Let's handle airport and managing authorities
        airport_uri = URIRef(base_domain + "/aeroporti/" + row["ICAO"])
        authority_url = URIRef(base_domain + "/gestori/" + row["ICAO"] + "-Gestore")
        # ManagingAuthority type definition
        g.add((authority_url, RDF.type, aio.Gestore))
        g.add((authority_url, RDFS.label, Literal(row["Gestore"], datatype=XSD.string)))
        # Airport type definition
        g.add((airport_uri, RDF.type, aio.Aeroporto))
        g.add((airport_uri, RDFS.label, Literal(row["Aeroporto"], datatype=XSD.string)))
        g.add((airport_uri, aio.nomeCommerciale, Literal(row["Nome Commerciale"], datatype=XSD.string)))
        g.add((airport_uri, aio.codiceIcao, Literal(row["ICAO"], datatype=XSD.string)))
        g.add((airport_uri, aio.codiceIata, Literal(row["IATA"], datatype=XSD.string)))
        # Let's add Airport and ManagingAuthority object properties
        g.add((airport_uri, aio.haIndirizzo, location_uri))
        g.add((airport_uri, aio.haGestore, authority_url))
        g.add((airport_uri, aio.haSitoWeb, Literal(wikidata_airports[row["ICAO"]]["website"], datatype=XSD.anyURI)))
        g.add((authority_url, aio.gestisceAeroporto, airport_uri))
        # Let's add OWL sameAs to City, Province and Region types
        g.add((airport_uri, owl.sameAs, URIRef(wikidata_airports[row["ICAO"]]["uri"])))
        # Person type definition and OWL sameAs object property definition
        if type(row["Eponimi"]) is str:
            humans = [name for name in row["Eponimi"].split(", ")]
            for human in humans:
                human_uri = URIRef(base_domain + "/persone/" + __urify_string(human))
                g.add((human_uri, RDF.type, aio.Persona))
                g.add((human_uri, RDFS.label, Literal(human, datatype=XSD.string)))
                if human in wikidata_humans:
                    g.add((human_uri, owl.sameAs, URIRef(wikidata_humans[human])))
                g.add((airport_uri, aio.intitolatoA, human_uri))
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
        uri = URIRef(base_domain + "/categorie_traffico/" + __urify_string(category))
        # Category type definition
        graph.add((uri, RDF.type, aio.Categoria))
        graph.add((uri, RDFS.label, Literal(category, datatype=XSD.string)))
    # Let's add traffic data triples to the graph iterating through the data_frame rows
    data_frame = pandas.read_csv(csv_filename)
    year_to_add = traffic_years_map[csv_filename]
    for _, row in data_frame.iterrows():
        airport_uri = URIRef(base_domain + "/aeroporti/" + row["Aeroporto"])
        category_uri = URIRef(base_domain + "/categorie_traffico/" + __urify_string(row["Categoria"]))
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
    traffic_uri = URIRef(base_domain + "/dati_traffico/" + res_name)
    # Traffic type definition
    graph.add((traffic_uri, RDF.type, aio.DatoTraffico))
    graph.add((traffic_uri, aio.origineTraffico, Literal(row["Origine"], datatype=XSD.string)))
    graph.add((traffic_uri, aio.totale, Literal(value, datatype=xsd_val_type)))
    graph.add((traffic_uri, aio.anno, Literal(row["Anno"], datatype=XSD.integer)))
    graph.add(
        (traffic_uri, RDFS.label, Literal(" ".join([row["Categoria"], str(row["Anno"])]), datatype=XSD.string))
    )
    # Let's add objects properties
    graph.add((airport_uri, aio.haDatoTraffico, traffic_uri))
    graph.add((traffic_uri, aio.haCategoria, category_uri))
    graph.add((traffic_uri, aio.riferitoAdAeroporto, airport_uri))
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
    variation = round(Decimal(row["Variazione Percentuale"]), 2)
    res_name = "-".join([row["Aeroporto"], __urify_string(row["Categoria"]), "2020-2019"])
    summary_uri = URIRef(base_domain + "/riepiloghi_traffico/" + res_name)
    # TrafficSummary type definition
    graph.add((summary_uri, RDF.type, aio.RiepilogoDatiTraffico))
    graph.add((summary_uri, RDFS.label, Literal(" ".join([row["Categoria"], "2020-2019"]), datatype=XSD.string)))
    graph.add((summary_uri, aio.totaleCorrente, Literal(value_present, datatype=xsd_val_type)))
    graph.add((summary_uri, aio.totalePassato, Literal(value_past, datatype=xsd_val_type)))
    graph.add((summary_uri, aio.variazionePercentuale, Literal(variation, datatype=XSD.decimal)))
    # Let's add objects properties
    graph.add((airport_uri, aio.haRiepilogoTraffico, summary_uri))
    graph.add((summary_uri, aio.haCategoria, category_uri))
    graph.add((summary_uri, aio.riferitoAdAeroporto, airport_uri))
    return graph


def __get_italian_airports_from_wikidata():
    query = """
        SELECT DISTINCT ?airport ?icao ?website
        WHERE { 
            ?airport wdt:P239 ?icao;
            wdt:P856 ?website.
            filter(strstarts(?icao,"LI"))
        }
    """
    bindings = __execute_sparql_query(query)
    results_dict = {}
    for raw in bindings:
        results_dict[raw["icao"]["value"]] = {
            "uri": raw["airport"]["value"],
            "website": raw["website"]["value"]
        }
    return results_dict


def __get_humans_from_wikidata(names_list):
    query = """
        SELECT DISTINCT ?item ?itemLabel WHERE {
            ?item wdt:P31 wd:Q5.
            ?item ?label "$1"@it.
            SERVICE wikibase:label { bd:serviceParam wikibase:language "it". }
        }
    """
    results_dict = {}
    names_list = list(itertools.chain(*[names.split(", ") for names in names_list if type(names) is str]))
    people_queries = dict(zip(names_list, [query.replace("$1", name) for name in names_list]))
    for person in people_queries:
        query = people_queries[person]
        time.sleep(2)
        bindings = __execute_sparql_query(query)
        if len(bindings) == 0:
            continue
        elif len(bindings) > 1:
            # If we have more than one result, we must know which is the correct person URI to get
            if person in ["Karol Wojtyła", "Pitagora", "Guglielmo Marconi", "Vincenzo Florio", "Marco Polo"]:
                bindings = bindings[-1]
            if person in ["Giovanni Falcone", "Cristoforo Colombo", "Vincenzo Bellini", "Luigi Ridolfi"]:
                bindings = bindings[0]
        else:
            bindings = bindings[0]
        results_dict[person] = bindings["item"]["value"]
    return results_dict


def __urify_string(original_string):
    return original_string.replace(" ", "_")


def __execute_sparql_query(query):
    sparql.setQuery(query)
    sparql.setReturnFormat(JSON)
    to_exec = True
    error_count = 0
    raw_q_result = {}
    while to_exec:
        try:
            raw_q_result = sparql.query().convert()
            to_exec = False
            error_count = 0
        except HTTPError:
            error_count += 1
            time.sleep(2 * error_count)
    bindings = {}
    if "results" in raw_q_result:
        if "bindings" in raw_q_result["results"]:
            bindings = raw_q_result["results"]["bindings"]
        else:
            raise ValueError("Query does not containes expected data")
    return bindings
