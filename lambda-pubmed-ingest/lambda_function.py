import json
import boto3
import urllib.request
import urllib.parse
import time
import xml.etree.ElementTree as ET
from datetime import datetime
from botocore.exceptions import ClientError

s3 = boto3.client('s3')
sqs = boto3.client("sqs")

QUEUE_URL = "https://sqs.ap-south-1.amazonaws.com/654999855185/bedrock-processing-queue"

dynamodb=boto3.resource('dynamodb')
findings_table = dynamodb.Table('Findings')

BUCKET_NAME = "clinical-evidence-raw"


PUBMED_SEARCH_URL = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi"
PUBMED_FETCH_URL = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi"


# ---------------------------
# Fetch PubMed IDs
# ---------------------------

def fetch_pubmed_ids(query):
    params = {
        "db": "pubmed",
        "term": query,
        "retmax":  50,
        "retmode": "json"
    }

    url = PUBMED_SEARCH_URL + "?" + urllib.parse.urlencode(params)

    with urllib.request.urlopen(url) as response:
        data = json.loads(response.read().decode())

    return data.get("esearchresult", {}).get("idlist", [])


# ---------------------------
# Fetch PubMed Paper XML
# ---------------------------
def fetch_pubmed_xml(pubmed_id):
    params = {
        "db": "pubmed",
        "id": pubmed_id,
        "retmode": "xml"
    }

    url = PUBMED_FETCH_URL + "?" + urllib.parse.urlencode(params)

    with urllib.request.urlopen(url) as response:
        xml_data = response.read().decode()

    return xml_data


# ---------------------------
# Extract Metadata from XML
# ---------------------------
def extract_metadata(xml_text):

    root = ET.fromstring(xml_text)
    article = root.find(".//Article")

    if article is None:
        return {
            "title": "",
            "abstract": "",
            "journal": "",
            "publication_year": ""
        }

    title = article.findtext("ArticleTitle", default="")

    abstract_texts = article.findall(".//AbstractText")
    abstract = " ".join([elem.text for elem in abstract_texts if elem.text])

    journal = article.findtext(".//Journal/Title", default="")
    pub_date = root.findtext(".//PubDate/Year", default="")

    return {
        "title": title,
        "abstract": abstract,
        "journal": journal,
        "publication_year": pub_date
    }


# ---------------------------
# Lambda Handler
# ---------------------------
def lambda_handler(event, context):

    try:
        body = json.loads(event["body"])
        condition = body.get("condition")
        treatment = body.get("treatment")

    # query = event.get("query" , "Type 2 Diabetes AND Metformin")
    # max_results = 20

        if not condition or not treatment:
            return {
                "statusCode": 400,
                "body": "condition and treatment required"
            }

        condition_treatment = f"{condition}#{treatment}"
        query = f"{condition} AND {treatment}"

        pubmed_ids = fetch_pubmed_ids(query)

        success_count = 0
        failure_count = 0

        for pubmed_id in pubmed_ids:

            try:
                # Fetch full XML
                raw_xml = fetch_pubmed_xml(pubmed_id)

                # Extract metadata
                metadata = extract_metadata(raw_xml)

                if not metadata["abstract"]:
                    print(f"No abstract found for {pubmed_id}")
                    metadata["abstract"] = "Abstract not available."
                timestamp = datetime.utcnow().isoformat()

                if len(metadata["abstract"]) < 100:
                    continue
                # ---------- Store RAW in S3 ----------
                s3_key = f"{condition_treatment}/{pubmed_id}.xml"

                s3.put_object(
                    Bucket=BUCKET_NAME,
                    Key=s3_key,
                    Body=raw_xml,
                    ContentType="application/xml"
                )

                # ---------- Store Metadata in DynamoDB ----------
                findings_table.put_item(
                    Item={
                        "condition_treatment": condition_treatment,
                        "pubmed_id": pubmed_id,
                        "title": metadata["title"],
                        "abstract": metadata["abstract"],
                        "journal": metadata["journal"],
                        "publication_year": metadata["publication_year"],
                        "s3_key": s3_key,
                        "fetched_at": timestamp
                    }
                )

                sqs.send_message(
                    QueueUrl=QUEUE_URL,
                    MessageBody=json.dumps({
                        "condition_treatment": condition_treatment,
                        "pubmed_id": pubmed_id,
                        "abstract": metadata["abstract"]
                    })
                )


                success_count += 1

            except Exception as paper_error:
                print(f"Error processing PubMed ID {pubmed_id}: {str(paper_error)}")
                failure_count += 1
                continue  # Continue processing remaining papers

        return {
            "statusCode": 200,
            "body": json.dumps({
                "condition_treatment": condition_treatment,
                "total_found": len(pubmed_ids),
                "successfully_stored": success_count,
                "failed": failure_count
            })
        }

    except Exception as e:
        print("Fatal Error:", str(e))
        return {
            "statusCode": 500,
            "body": "Internal server error"
        }