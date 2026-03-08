import json
import boto3
from decimal import Decimal
from boto3.dynamodb.conditions import Key

dynamodb = boto3.resource("dynamodb")

scores_table = dynamodb.Table("Scores")
findings_table = dynamodb.Table("StructuredFindings")

lambda_client = boto3.client("lambda")


def convert_decimals(obj):
    if isinstance(obj, list):
        return [convert_decimals(i) for i in obj]
    elif isinstance(obj, dict):
        return {k: convert_decimals(v) for k, v in obj.items()}
    elif isinstance(obj, Decimal):
        return float(obj)
    return obj


def cors_headers():
    return {
        "Content-Type": "application/json",
        "Access-Control-Allow-Origin": "*",
        "Access-Control-Allow-Headers": "*",
        "Access-Control-Allow-Methods": "GET,OPTIONS"
    }


def lambda_handler(event, context):

    print("EVENT:", json.dumps(event))

    if event.get("httpMethod") == "OPTIONS":
        return {
            "statusCode": 200,
            "headers": cors_headers(),
            "body": ""
        }

    path = event.get("path") or event.get("resource") or ""

    params = event.get("queryStringParameters")
    if params is None:
        params = {}

    # -------------------------
    # /scores
    # -------------------------
    if path.endswith("/scores"):

        response = scores_table.scan()

        return {
            "statusCode": 200,
            "headers": cors_headers(),
            "body": json.dumps(convert_decimals(response.get("Items", [])))
        }

    # -------------------------
    # /findings
    # -------------------------
    if path.endswith("/findings"):

        condition = params.get("condition")
        treatment = params.get("treatment")

        if not condition or not treatment:
            return {
                "statusCode": 400,
                "headers": cors_headers(),
                "body": json.dumps({
                    "message": "condition and treatment required"
                })
            }

        key = f"{condition}#{treatment}"

        response = findings_table.query(
            KeyConditionExpression=Key("condition_treatment").eq(key)
        )

        items = response.get("Items", [])

        # If no research found → trigger ingestion
        if len(items) == 0:

            try:
                lambda_client.invoke(
                    FunctionName="pubmed-ingest",
                    InvocationType="Event",
                    Payload=json.dumps({
                        "body": json.dumps({
                            "condition": condition,
                            "treatment": treatment
                        })
                    })
                )
            
            except Exception as e:
                print("INGESTION ERROR:", str(e))

            return {
                "statusCode": 200,
                "headers": cors_headers(),
                "body": json.dumps({
                    "message": "Fetching research from PubMed. Please retry in ~20 seconds."
                })
            }

        return {
            "statusCode": 200,
            "headers": cors_headers(),
            "body": json.dumps(convert_decimals(items))
        }

    return {
        "statusCode": 400,
        "headers": cors_headers(),
        "body": json.dumps({"message": "Invalid endpoint"})
    }