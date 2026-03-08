import json
import boto3
import os
from datetime import datetime
import re

dynamodb = boto3.resource("dynamodb")

BEDROCK_REGION = os.environ.get("BEDROCK_REGION", "us-east-1")


bedrock = boto3.client(
    "bedrock-runtime",
    region_name=BEDROCK_REGION
)
structured_table = dynamodb.Table("StructuredFindings")

MODEL_ID = "anthropic.claude-3-haiku-20240307-v1:0"


def build_prompt(abstract):
    return f"""
You are a clinical research analysis assistant.

Analyze the research abstract and extract structured findings.

Return ONLY valid JSON.

Rules:

direction_of_effect:
- supports → study supports effectiveness of treatment
- contradicts → study shows treatment ineffective or harmful
- neutral → study inconclusive or observational

confidence_level:
- high → randomized controlled trial or large study
- moderate → cohort study or medium sample
- low → review, commentary, or unclear evidence

sample_size:
- extract if mentioned otherwise null

evidence_strength_score:
- high confidence = 80–100
- moderate = 40–79
- low = 0–39

Required JSON format:

{{
"conclusion_summary": string,
"direction_of_effect": "supports" | "contradicts" | "neutral",
"sample_size": integer or null,
"confidence_level": "low" | "moderate" | "high",
"evidence_strength_score": integer
}}

Abstract:
\"\"\"{abstract}\"\"\"
"""


def call_bedrock(prompt):

    body = {
        "anthropic_version": "bedrock-2023-05-31",
        "max_tokens": 600,
        "temperature": 0,
        "messages": [
            {"role": "user", "content": prompt}
        ]
    }

    response = bedrock.invoke_model(
        modelId=MODEL_ID,
        body=json.dumps(body)
    )

    result = json.loads(response["body"].read())
    output_text = result["content"][0]["text"]

    json_match = re.search(r"\{.*\}", output_text, re.DOTALL)

    if json_match:
        return json.loads(json_match.group())
    else:
        raise ValueError("No JSON returned from model")
        return json.loads(output_text)


def lambda_handler(event, context):

    for record in event["Records"]:

        body = json.loads(record["body"])

        condition_treatment = body["condition_treatment"]
        pubmed_id = body["pubmed_id"]
        abstract = body["abstract"]



        if abstract == "Abstract not available.":
            structured_table.put_item(
                Item={
                    "condition_treatment": condition_treatment,
                    "pubmed_id": pubmed_id,
                    "conclusion_summary": "No abstract available",
                    "direction_of_effect": "neutral",
                    "sample_size": None,
                    "confidence_level": "low",
                    "evidence_strength_score": 0,
                    "processed_at": datetime.utcnow().isoformat()
                }
            )
            continue

        prompt = build_prompt(abstract)
        try:
            structured_output = call_bedrock(prompt)
        except Exception as e:
            print("Bedrock failed:", str(e))
            continue

        structured_table.put_item(
            Item={
                "condition_treatment": condition_treatment,
                "pubmed_id": pubmed_id,
                "conclusion_summary": structured_output.get("conclusion_summary"),
                "direction_of_effect": structured_output.get("direction_of_effect"),
                "sample_size": structured_output.get("sample_size"),
                "confidence_level": structured_output.get("confidence_level"),
                "evidence_strength_score": structured_output.get("evidence_strength_score"),
                "processed_at": datetime.utcnow().isoformat()
            }
        )

    lambda_client = boto3.client("lambda")

    lambda_client.invoke(
        FunctionName="clinical-scoring",
        InvocationType="Event"
    )

    return {"statusCode": 200}