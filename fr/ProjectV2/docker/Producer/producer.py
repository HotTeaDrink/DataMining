import pandas as pd
import sys
from SPARQLWrapper import SPARQLWrapper, JSON
import os
import pika
from pyspark import SparkContext

def get_results(endpoint_url, query):
    user_agent = "WDQS-example Python/%s.%s" % (
        sys.version_info[0],
        sys.version_info[1],
    )
    sparql = SPARQLWrapper(endpoint_url, agent=user_agent)
    sparql.setQuery(query)
    sparql.setReturnFormat(JSON)
    return sparql.query().convert()

def gather_image_links():
    endpoint_url = "https://query.wikidata.org/sparql"
    query = """SELECT DISTINCT ?grandeville ?grandevilleLabel ?pays ?paysLabel ?image {
      ?grandeville wdt:P31 wd:Q1549591;
                   wdt:P17 ?pays;
                   wdt:P18 ?image.
     SERVICE wikibase:label { bd:serviceParam wikibase:language "fr". }
    }
    LIMIT 100"""

    results = get_results(endpoint_url, query)
    links = []

    for result in results["results"]["bindings"]:
        link = result["image"]["value"]
        print(f"[DEBUG] Sending link: {link}")
        links.append(link)

    return links

def send_links_to_queue(links):
    connection = pika.BlockingConnection(pika.ConnectionParameters(host='rabbitmq'))
    channel = connection.channel()

    channel.queue_declare(queue='image_links')

    for link in links:
        channel.basic_publish(exchange='',
                              routing_key='image_links',
                              body=link)
        print(f"[DEBUG] Link sent: {link}")

    connection.close()

if __name__ == "__main__":
    sc = SparkContext("local", "ImageLinkGatherer")
    links_rdd = sc.parallelize(gather_image_links())
    links_rdd.foreach(lambda link: send_links_to_queue([link]))
