import gzip
import requests
import spacy
import trident
import json
from spacy import displacy
from collections import Counter
from elasticsearch import Elasticsearch
from bs4 import BeautifulSoup
from datetime import datetime
from difflib import SequenceMatcher
import operator
import random
import csv
import math


##Files or library need to be installed
## 1.Spacy and the 'en_core_web_sm' library
## pip3 install spacy
## python3 -m spacy download en_core_web_sm

##2.Beautiful Soup
##pip3 install beautifulsoup4

KEYNAME = "WARC-Record-ID"
ES_size = 60  # the query size for ES
Thereshold_ES_Rent=0.3


# The goal of this function process the webpage and returns a list of labels -> entity ID
def find_labels(payload):
    if payload == '':
        return

    # The variable payload contains the source code of a webpage and some additional meta-data.
    # We first retrieve the ID of the webpage, which is indicated in a line that starts with KEYNAME.
    # The ID is contained in the variable 'key'
    key = None

    for line in payload.splitlines():
        if line.startswith(KEYNAME):
            key = line.split(': ')[1]

            break

    # Problem 1: The webpage is typically encoded in HTML format.
    # We should get rid of the HTML tags and retrieve the text. How can we do it?

    ## Getting HTML part from payload
    html_part=get_html_part(payload)



    ## if there is HTML part in payload => proceed
    if html_part is not None:

        ## get the text from HTML
        text=get_html_text(html_part)



        # Problem 2: Let's assume that we found a way to retrieve the text from a webpage. How can we recognize the
        # entities in the text?
        ## Do NER for the retrieved TEXT with Spacy
        Recog_Entity = Identify_Entity_SPACY(text)

        ##Use Elastic Search to search for related entity in Wikidata


        for x in Recog_Entity:
            ELink_wikiID = ""
            Ident_Entity_Label=x ##Label of the Recognized Entity x
            NER_ID_Type=Recog_Entity[x]
            ES_Result = ES_search(x, ES_size)
            i = 0

            ## To skip the short entity
            if len(Ident_Entity_Label) < 5:
                continue

            CandEnt_MatchType={}

            for entity, labels in ES_Result.items():
                for values in ES_Result[entity]:
                    ES_Result_Label=values ## Label of the ES_Result
                    sim_ratio_ES_REnt=compare_string_similar(ES_Result_Label, Ident_Entity_Label)
                i = i + 1

                # Problem 3: We now have to disambiguate the entities in the text. For instance, let's assugme that we identified
                # the entity "Michael Jordan". Which entity in Wikidata is the one that is referred to in the text?


                ## if the ES_Result Label is not similar to the Recognized Entity Label, we skip the trident query
                if sim_ratio_ES_REnt>Thereshold_ES_Rent:
                    ent_type=trident_query(entity)

                    ent_type_match_Bol=entity_compare_type(NER_ID_Type,ent_type)
                    if ent_type_match_Bol:
                        CandEnt_MatchType[entity]=ES_Result[entity]
                else:
                    continue
                    print('"'+ES_Result_Label+'" of ES Result does not look like the recognized entity')


            if len(CandEnt_MatchType) >0:
                ELink_wikiID=rank_candidateEnt(CandEnt_MatchType,Ident_Entity_Label)

            ## Output the result
            print(key + '\t' + Ident_Entity_Label + '\t' + ELink_wikiID)

    else:
        return



def rank_candidateEnt(CanEnt_Final,Ident_Entity_Label):
    StrSim={}
    a = 0

    ## Calculating how similar the candidate entity string is similar to the identified entity
    for entity, labels in CanEnt_Final.items():
        a = a + 1

        ## if there is only 1 candidate, skip the whole ranking process
        if len(CanEnt_Final)==1:
            return entity


        for values in CanEnt_Final[entity]:
            StrSim[entity]=compare_string_similar(values, Ident_Entity_Label)


    max_StrSim_calue=max(StrSim.items(), key=operator.itemgetter(1))[1] ##getting the max String Similar Value
    list_MaxStrSim=[k for k, v in StrSim.items() if float(v) == max_StrSim_calue] ## list of candidate entity that has max String Similar Value

    ##Output the selected Value
    index=0
    if len(list_MaxStrSim)>1:
        HighScore = 0
        High_Entity=""
        for entity in list_MaxStrSim:
            CurScore = trident_query_popularity(entity)
            if CurScore>HighScore:
                High_Entity=entity
                HighScore=CurScore

        return High_Entity

    return str(list_MaxStrSim[index])

def compare_string_similar(str_a,str_b):
    return SequenceMatcher(None, str_a, str_b).ratio()

def print_dict(in_dict):
    a=0
    for x,y in in_dict.items():
        a=a+1
        print(str(a) + ': ' + str(x) + '-' + str(y))

def remove_punc(in_text):
    # define punctuation
    punctuations = '''!()-[]{};:'"\,<>./?@#$%^&*_~»™'''


    no_punct = ""
    for char in in_text:
       if char not in punctuations:
           no_punct = no_punct + char
    return no_punct

def split_records(stream):
    payload = ''
    for line in stream:
        if line.strip() == "WARC/1.0":
            yield payload
            payload = ''
        else:
            payload += line
    yield payload

def get_html_part(payload):
    html = ''
    start_here = False
    for line in payload.splitlines():

        if line.startswith("<html"):
            start_here = True
        if start_here:
            html += line
    if start_here == False:
        return
    else:
        return html

def get_html_text(html):
    soup = BeautifulSoup(html, features="html.parser")
    paragraph = soup.find_all("p")
    html_text = ""
    for p in paragraph:
        if p.get_text(" ", strip=True) != '':
            html_text += p.get_text(" ", strip=True) + "\n"
        if html_text == "":
            html_text = soup.get_text(" ", strip=True)
    return html_text

def Identify_Entity_SPACY(TEXT):
    Ent_Dict = {}
    labels_not_of_interest = ['TIME', 'DATE', 'PERCENT', 'MONEY', 'QUANTITY', 'ORDINAL', 'CARDINAL']
    # print(TEXT)
    nlp = spacy.load("en_core_web_sm")
    doc_result=nlp(TEXT)

    ##Final
    for ent in doc_result.ents:

        if ent.label_ not in labels_not_of_interest:
            entity, label = ent.text, ent.label_
            Ent_Dict[entity] = label
    #Return a dict with the recognized entity
    return Ent_Dict

def ES_search(query,des_size):
    #connection_string='fs0.das5.cs.vu.nl:10010'
    # e = Elasticsearch([connection_string,connection_string])
    e = Elasticsearch()
    query_statement=remove_punc(query)
    p = { "query" : { "query_string" : { "query" : query_statement }}} # Mod1
    response = e.search(index="wikidata_en", body=json.dumps(p), size=des_size,request_timeout=120)
    id_labels = {}



    if response:
        for hit in response['hits']['hits']:
            if 'schema_name' in hit['_source'].keys():
                label = hit['_source']['schema_name'] #original version
                id = hit['_id']
                id_labels.setdefault(id, set()).add(label)
            else:
                continue

    return id_labels


##### trident_query_ori was the first version of our trident query
def trident_query_ori(in_wikient):
    KBPATH = 'assets/wikidata-20200203-truthy-uri-tridentdb'

    query = "PREFIX wde: <http://www.wikidata.org/entity/> " \
            "PREFIX wdp: <http://www.wikidata.org/prop/direct/> " \
            "PREFIX wdpn: <http://www.wikidata.org/prop/direct-normalized/> " \
            "select * where { "+ in_wikient +" wdp:P31 ?instance ." \
                                              " ?instance wdp:P279 ?subclass1 ."\
                                              " ?subclass1 wdp:P279 ?subclass2 ."\
                                              " ?subclass2 wdp:P279 ?subclass3 .}"

    ##P31 instance of
    ##P279 subclass of

    # Load the KB
    db = trident.Db(KBPATH)
    results = db.sparql(query)
    json_results = json.loads(results)
    variables = json_results["head"]["vars"]

    results = json_results["results"]
    result_type = set()
    for b in results["bindings"]:
        line = ""
        for var in variables:
            line += var + ": " + b[var]["value"] + " "
            this_resulttype=str(b[var]["value"])
            result_type.add(this_resulttype)
    return result_type


### trident_query is the query we ended up using
def trident_query(in_wikient):
    ## Using Trident to query Wikidata
    ## return a list with 'instance of'
    KBPATH = 'assets/wikidata-20200203-truthy-uri-tridentdb'

    query = "PREFIX wde: <http://www.wikidata.org/entity/> " \
            "PREFIX wdp: <http://www.wikidata.org/prop/direct/> " \
            "PREFIX wdpn: <http://www.wikidata.org/prop/direct-normalized/> " \
            "select * where { "+ in_wikient +" wdp:P31 ?instance ." \
                                              " ?instance wdp:P279 ?subclass1 ."\
                                              " ?subclass1 wdp:P279 ?subclass2 ."\
                                              " ?subclass2 wdp:P279 ?subclass3 .}"

    query1 = "PREFIX wde: <http://www.wikidata.org/entity/> " \
            "PREFIX wdp: <http://www.wikidata.org/prop/direct/> " \
            "PREFIX wdpn: <http://www.wikidata.org/prop/direct-normalized/> " \
            "select * where { "+ in_wikient +" wdp:P31 ?instance .}" \


    query2 = "PREFIX wde: <http://www.wikidata.org/entity/> " \
            "PREFIX wdp: <http://www.wikidata.org/prop/direct/> " \
            "PREFIX wdpn: <http://www.wikidata.org/prop/direct-normalized/> " \
            "select * where {  ?instance wdp:P279 ?subclass1 .}"\

    ##P31 instance of
    ##P279 subclass of

    # Load the KB
    db = trident.Db(KBPATH)
    results = db.sparql(query1)
    json_results = json.loads(results)
    variables = json_results["head"]["vars"]

    results = json_results["results"]
    result_type = set()
    for b in results["bindings"]:
        line = ""
        for var in variables:
            line += var + ": " + b[var]["value"] + " "
            this_resulttype=str(b[var]["value"])
            result_type.add(this_resulttype)
    result_set=set()

    ## Get all subclass with trident_get_subclass()
    for instance in result_type:
        result_set.add(instance)
        for subclass1 in trident_get_subclass(instance):
            result_set.add(subclass1)
            for subclass2 in trident_get_subclass(subclass1):
                result_set.add(subclass2)
                for subclass3 in trident_get_subclass(subclass2):
                    result_set.add(subclass3)
    return result_set

def trident_get_subclass(in_wikient):
    mod_ent='<'+in_wikient+'>'
    KBPATH = 'assets/wikidata-20200203-truthy-uri-tridentdb'


    query1 = "PREFIX wde: <http://www.wikidata.org/entity/> " \
             "PREFIX wdp: <http://www.wikidata.org/prop/direct/> " \
             "PREFIX wdpn: <http://www.wikidata.org/prop/direct-normalized/> " \
             "select * where { " + mod_ent + " wdp:P279 ?instance .}"

    query2 = "PREFIX wde: <http://www.wikidata.org/entity/> " \
             "PREFIX wdp: <http://www.wikidata.org/prop/direct/> " \
             "PREFIX wdpn: <http://www.wikidata.org/prop/direct-normalized/> " \
             "select * where {  ?instance wdp:P279 ?subclass1 .}"

    ##P31 instance of
    ##P279 subclass of
    # Load the KB
    db = trident.Db(KBPATH)
    results = db.sparql(query1)
    json_results = json.loads(results)
    variables = json_results["head"]["vars"]

    results = json_results["results"]
    result_type = set()
    for b in results["bindings"]:
        line = ""
        for var in variables:
            line += var + ": " + b[var]["value"] + " "
            this_resulttype = str(b[var]["value"])
            result_type.add(this_resulttype)
    return result_type

def trident_query_popularity(in_wikient):

    ## Using Trident to query Wikidata
    ## return a list with 'instance of'

    KBPATH = 'assets/wikidata-20200203-truthy-uri-tridentdb'


    query = "PREFIX wde: <http://www.wikidata.org/entity/> " \
            "PREFIX wdp: <http://www.wikidata.org/prop/direct/> " \
            "PREFIX wdpn: <http://www.wikidata.org/prop/direct-normalized/> " \
            "select * where { "+ in_wikient +" ?type ?instance .}"

    query_sample = "PREFIX wde: <http://www.wikidata.org/entity/> " \
            "PREFIX wdp: <http://www.wikidata.org/prop/direct/> " \
            "PREFIX wdpn: <http://www.wikidata.org/prop/direct-normalized/> " \
            "select * where { <http://www.wikidata.org/entity/Q1142936> ?type ?instance .}"


    ##P31 instance of
    ##P279 subclass of

    db = trident.Db(KBPATH)
    results = db.sparql(query)
    json_results = json.loads(results)

    variables = json_results["head"]["vars"]

    results = json_results["results"]
    result_type = set()
    for b in results["bindings"]:
        line = ""
        for var in variables:
            line += var + ": " + b[var]["value"] + " "
            this_resulttype=str(b[var]["value"])
            result_type.add(this_resulttype)
    return len(result_type)

def entity_compare_type(EType,CandidateType):

    ## Declare Set of wiki_entity_type for the corresponding Spacy Label
    Ent_Person= {"http://www.wikidata.org/entity/Q5","http://www.wikidata.org/entity/Q1114461","http://www.wikidata.org/entity/Q215627","http://www.wikidata.org/entity/Q95074","http://www.wikidata.org/entity/Q16334295","http://www.wikidata.org/entity/Q874405"}
    Ent_NORP={"http://www.wikidata.org/entity/Q231002","http://www.wikidata.org/entity/Q6957341","http://www.wikidata.org/entity/Q7278","http://www.wikidata.org/entity/Q9174","http://www.wikidata.org/entity/Q1530022"}
    Ent_FAC = {"http://www.wikidata.org/entity/Q62447","http://www.wikidata.org/entity/Q41176","http://www.wikidata.org/entity/Q12280","http://www.wikidata.org/entity/Q34442"}
    Ent_ORG = {"http://www.wikidata.org/entity/Q43229","http://www.wikidata.org/entity/Q6881511","http://www.wikidata.org/entity/Q4830453","http://www.wikidata.org/entity/Q3563237"}
    Ent_GPE = {"http://www.wikidata.org/entity/Q6256","http://www.wikidata.org/entity/Q7275","http://www.wikidata.org/entity/Q515","http://www.wikidata.org/entity/Q3957","http://www.wikidata.org/entity/Q123705","http://www.wikidata.org/entity/Q2983893","http://www.wikidata.org/entity/Q486972"}
    Ent_LOC = {"http://www.wikidata.org/entity/Q46831","http://www.wikidata.org/entity/Q15324","http://www.wikidata.org/entity/Q82794","http://www.wikidata.org/entity/Q5107","http://www.wikidata.org/entity/Q107425","http://www.wikidata.org/entity/Q2221906","http://www.wikidata.org/entity/Q133346"}
    Ent_PRODUCT = {"http://www.wikidata.org/entity/Q2424752","http://www.wikidata.org/entity/Q223557","http://www.wikidata.org/entity/Q1183543","http://www.wikidata.org/entity/Q19861951","http://www.wikidata.org/entity/Q28877","http://www.wikidata.org/entity/Q7397"}
    Ent_EVENT = {"http://www.wikidata.org/entity/Q198","http://www.wikidata.org/entity/Q11514315","http://www.wikidata.org/entity/Q1920219","http://www.wikidata.org/entity/Q381072","http://www.wikidata.org/entity/Q1656682","http://www.wikidata.org/entity/Q1190554"}
    Ent_ART = {"http://www.wikidata.org/entity/Q47461344","http://www.wikidata.org/entity/Q17537576","http://www.wikidata.org/entity/Q732577","http://www.wikidata.org/entity/Q838948","http://www.wikidata.org/entity/Q15621286","http://www.wikidata.org/entity/Q4502142"}
    Ent_LAW = {"http://www.wikidata.org/entity/Q7748","http://www.wikidata.org/entity/Q820655","http://www.wikidata.org/entity/Q2006324","http://www.wikidata.org/entity/Q327197","http://www.wikidata.org/entity/Q1864008","http://www.wikidata.org/entity/Q49848"}
    Ent_LANGUAGE = {"http://www.wikidata.org/entity/Q17376908","http://www.wikidata.org/entity/Q20162172","http://www.wikidata.org/entity/Q33742","http://www.wikidata.org/entity/Q25295","http://www.wikidata.org/entity/Q28923954"}

    Ent_Main={
    'PERSON':Ent_Person,
    'NORP':Ent_NORP,
    'FAC':Ent_FAC,
    'ORG': Ent_ORG,
    'GPE':Ent_GPE,
    'LOC':Ent_LOC,
    'PRODUCT':Ent_PRODUCT,
    'EVENT':Ent_EVENT,
    'WORK_OF_ART':Ent_ART,
    'LAW':Ent_LAW,
    'LANGUAGE':Ent_LANGUAGE,
    }
    IsSameType=False
    for CanEnt in CandidateType:
        if CanEnt in Ent_Main[EType]:
            return True

    return IsSameType


## Main Start
if __name__ == '__main__':
    import sys
    try:
        _, INPUT = sys.argv
    except Exception as e:
        print('Usage: python starter-code.py INPUT')
        sys.exit(0)
    i=0
    # INPUT = 'data/sample.warc.gz'  ## for running without using shell files
    with gzip.open(INPUT, 'rt', errors='ignore') as fo:
        for record in split_records(fo):
            find_labels(record)



## Main End
