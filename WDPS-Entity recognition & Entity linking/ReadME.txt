#--------------------------------------------------------
## PART I - Retrieving text from WARC file
#--------------------------------------------------------
The first part of the assignment as mentioned in the introduction is about extracting text from webpages which are in a WARC format. The WARC file contains among other things the key ID and a part that includes the html code. The goal is to retrieve the key-ID and the text contained within the html code.
#--------------------------------------------------------
## PART II - Named-entity generation
#--------------------------------------------------------
The next step after having retrieved the text is the Named-Entity Recognition (NER). There are a number of NLP libraries for Python. These are among others NLTK, spaCy and neuroLAN.
They can all be used to serve the same purpose, namely to recognize named-entities and their corresponding labels. 
#--------------------------------------------------------
##PART III - Entity Linking (Candidate Entity Generation and Ranking)
#--------------------------------------------------------
The third and last part of our problem is linking the recognized entities to their corresponding Wikidata entry. This part consists of two sub-parts: andidate entity generation and the Ranking of these candidate entities.
3.1 - Candidate Generation
To find the matching Wikidata entry an elastic search server is used. The search engine is queried
based on the named-entities found in part II. The elastic search returns 60 entities. Performance
restrictions made it such that the amount of candidates that are generated are just enough to
ensure relatively good results and performance.
3.2 Candidate Ranking
To find the best candidate entity, a ranking procedure has to be followed. In this procedure
we use a SPARQL engine(Trident) to extract extra information about the candidate entity, e.g.
popularity, type of entity, in order to select the best candidate entity.
3.3 SPARQL Query
Before the queries were performed, the desired Wikidata ID’s of the labels corresponding to the
entities recognized in the text needed to be identified. For example for the label ‘PEOPLE’ this
would be the Wikidata entry ‘human’ with ID Q5 or for ‘ORG’ we have the entry ’organization’
with ID Q43229. For every label there are multiple Wikidata entries that are considered. A
dictionary is made where for each label a set of IDs is assigned.

#--------------------------------------------------------
#       Steps for running the code
#--------------------------------------------------------
The steps to run the code (in chronological order) are:
1. Install Spacy:
• pip3 install spacy
• python3 -m spacy download en core web sm
2. Install BeautifulSoup:
• pip3 install beautifulsoup4
3. Start the Elastic Search Server:
• sh start elasticsearch server.sh
4. Run the code:
Change the input file names ‘input warc files’ and ‘input sample annotations’ in the shell file Run Gp33.sh to the appropiate names of the input files that the code will be tested with
• sh Run Gp33.sh
• This will run the two python scripts Run Gp33 Final.py and score.py
The following packages are imported in the code:
• gzip
• spacy
• trident
• json
• (from spacy) displacy
• (from collections) Counter
• (from elasticsearch) Elasticsearch
• (from bs4) BeautifulSoup
• (from difflib) SequenceMatcher


