# Aeroporti Italiani 

<img src="./aeroporti_italiani_logo.svg" width="300" height="300" alt="Logo di Aeroporti italiani"/>

Il progetto nasce dalla necessità di creare dei linked open data sugli aeroporti italiani a partire dai dati 
messi a disposizione dall'ENAC (Ente Nazionale per l'Aviazione Civile) e dall'ISTAT (Istituto Nazionale di Statistica).
I dati originali sono stati elaborati attraverso una pipeline di elaborazione che si può trovare 
nella directory denominata `src` scritta in linguaggio `python`.
I datiset ottenuti dalla pipeline di elaborazione possono essere trovati nella directory `data`, ed il dataset in formato
RDF/Turtle denominato `aeroporti_italiani.ttl`, possono essere liberamente visionati e scaricati.
I dataset forniti all'interno di questo repository sono rilasciati attraverso licenza 
[Creative Commons Attribution 4.0](./LICENSE).

### Mappa degli aeroporti italiani
La mappa degli aeroporti italiani è disponibile su [http://u.osmfr.org/m/624143/](http://u.osmfr.org/m/624143/)
ed è resa disponibile attraverso licenza [Open Data Commons Open Database License (ODbL)](https://opendatacommons.org/licenses/odbl/).

### Altri Esempi
Con l'aiuto di [Virtuoso](https://virtuoso.openlinksw.com/) possiamo caricare tramite la query `SPARQL`:

```SPARQL
   LOAD <https://raw.githubusercontent.com/alessandrofrenna/aeroporti_italiani/main/aeroporti_italiani.ttl>
```

possiamo caricare il nostro grafo RDF su uno storage che, tramite SPARQL, ci permetterà di interrogare il nostro grafo di conoscenza.
Alcune query di esempio sono:

1. Classifica degli aeroporti italiani per numero di passeggeri in transito nel 2020:

    ```SPARQL
        PREFIX aio: <http://purl.org/net/aeroporti_italiani/ontologia.owl/>
        PREFIX xsd: <http://www.w3.org/2001/XMLSchema#>
        
        SELECT DISTINCT ?Nome_Aeroporto ?Categoria ?Totale_Passeggeri_2020 ?Variazione_Percentuale_2019  WHERE {
          ?aeroporto aio:nomeCommerciale ?Nome_Aeroporto ;
                     aio:haRiepilogoTraffico ?riepiloghi .
          ?riepiloghi aio:haCategoria/rdfs:label ?Categoria;
                      aio:totaleCorrente ?Totale_Passeggeri_2020 ;
                      aio:variazionePercentuale ?Variazione_Percentuale_2019
          FILTER (REGEX(?Categoria, "passeggeri")) .
        } ORDER BY DESC(?Totale_Passeggeri_2020)
    ```
2.  Mestiere e data di morte dei personaggi a cui sono intitolati gli aeroporti (la query usa Wikidata):

    ```SPARQL
        PREFIX aio: <http://purl.org/net/aeroporti_italiani/ontologia.owl/>
        PREFIX owl: <http://www.w3.org/2002/07/owl>
        PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
        PREFIX wd: <http://www.wikidata.org/entity/> 
        PREFIX wdt: <http://www.wikidata.org/prop/direct/>
        
        SELECT DISTINCT ?Nome_Aeroporto ?Eponimo ?wdata ?Professione ?Data_Morte WHERE {
          ?aeroporto aio:nomeCommerciale ?Nome_Aeroporto ;
                     aio:intitolatoA ?persona .
          ?persona rdfs:label ?Eponimo ;
                   owl:sameAs ?wdata .
          OPTIONAL { 
            ?wdata wdt:P106/rdfs:label ?Professione .
            FILTER (lang(?Professione) = "it") .
          } .
          OPTIONAL { ?wdata wdt:P570 ?Data_Morte . }
        }
    ```

# Italian Airports
<img src="./aeroporti_italiani_logo.svg" width="300" height="300" alt="Italian airoports logo"/>

The project was made to create a linked open data knowledge base about the italian airports provided by the ENAC
(Italian National Organization for the Civil Aviation) and by ISTAT (Italian National Institute of Statistics).
Original data were elaborated through a pipeline that can be found in the directory named `src`,
The pipeline is written in `python`.
The datasets in the `data` folder, and the RDF/Turtle dataset named `aeroporti_italiani.ttl`, elaborated by the pipeline,
can be freely seen downloaded.
All the datasets made available through this repository are provided under [Creative Commons Attribution 4.0](./LICENSE) 
license.

### Italian airports map
The italian airports map is available at [http://u.osmfr.org/m/624143/](http://u.osmfr.org/m/624143/).
The map is available under the [Open Data Commons Open Database License (ODbL)](https://opendatacommons.org/licenses/odbl/).

### Other Examples
With the help of the [Virtuoso](https://virtuoso.openlinksw.com/) storage, we can load our knowledge graph the `SPARQL` query:

```SPARQL
    LOAD <https://raw.githubusercontent.com/alessandrofrenna/aeroporti_italiani/main/aeroporti_italiani.ttl>
```

the knowledge graph will be queried using SPARQL to get new knowledge.
Here some SPARQL query as example:

1. Rank of the italian airports by passengers traffic in the 2020:

    ```SPARQL
    PREFIX aio: <http://purl.org/net/aeroporti_italiani/ontologia.owl/>
    PREFIX xsd: <http://www.w3.org/2001/XMLSchema#>
    
    SELECT DISTINCT ?Nome_Aeroporto ?Categoria ?Totale_Passeggeri_2020 ?Variazione_Percentuale_2019  WHERE {
      ?aeroporto aio:nomeCommerciale ?Nome_Aeroporto ;
                 aio:haRiepilogoTraffico ?riepiloghi .
      ?riepiloghi aio:haCategoria/rdfs:label ?Categoria;
                  aio:totaleCorrente ?Totale_Passeggeri_2020 ;
                  aio:variazionePercentuale ?Variazione_Percentuale_2019
      FILTER (REGEX(?Categoria, "passeggeri")) .
    } ORDER BY DESC(?Totale_Passeggeri_2020)
    ```
2.  Jobs and dates of death of people whom airports are entitled to (it uses Wikidata):

    ```SPARQL
    PREFIX aio: <http://purl.org/net/aeroporti_italiani/ontologia.owl/>
    PREFIX owl: <http://www.w3.org/2002/07/owl>
    PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
    PREFIX wd: <http://www.wikidata.org/entity/> 
    PREFIX wdt: <http://www.wikidata.org/prop/direct/>
    
    SELECT DISTINCT ?Nome_Aeroporto ?Eponimo ?wdata ?Professione ?Data_Morte WHERE {
      ?aeroporto aio:nomeCommerciale ?Nome_Aeroporto ;
                 aio:intitolatoA ?persona .
      ?persona rdfs:label ?Eponimo ;
               owl:sameAs ?wdata .
      OPTIONAL { 
        ?wdata wdt:P106/rdfs:label ?Professione .
        FILTER (lang(?Professione) = "it") .
      } .
      OPTIONAL { ?wdata wdt:P570 ?Data_Morte . }
    }
    ```