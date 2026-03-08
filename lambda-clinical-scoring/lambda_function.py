import boto3
from collections import defaultdict
from datetime import datetime

dynamodb = boto3.resource("dynamodb")

structured_table = dynamodb.Table("StructuredFindings")
scores_table = dynamodb.Table("Scores")


def lambda_handler(event, context):

    response = structured_table.scan()
    items = response.get("Items", [])

    grouped = defaultdict(list)

    for item in items:
        grouped[item["condition_treatment"]].append(item)

    results = []

    for condition_treatment, findings in grouped.items():

        total = len(findings)

        supports = sum(
            1 for f in findings if f.get("direction_of_effect") == "supports"
        )

        contradicts = sum(
            1 for f in findings if f.get("direction_of_effect") == "contradicts"
        )

        neutral = sum(
            1 for f in findings if f.get("direction_of_effect") == "neutral"
        )

        # Stability score = agreement percentage
        weighted_support = sum(
            f.get("evidence_strength_score",0)
            for f in findings
            if f.get("direction_of_effect") == "supports"
        )
        
        weighted_total = sum(
            f.get("evidence_strength_score",0)
            for f in findings
        )
        
        stability_score = int((weighted_support / weighted_total) * 100) if weighted_total else 0

        contradiction_score = int((contradicts / total) * 100) if total else 0

        today = datetime.utcnow().strftime("%Y-%m-%d")

        scores_table.put_item(
            Item={
                "condition_treatment": condition_treatment,
                "date": today,
                "stability_score": stability_score,
                "contradiction_score": contradiction_score,
                "paper_count": total,
                "supports": supports,
                "contradicts": contradicts,
                "neutral": neutral,
                "scored_at": datetime.utcnow().isoformat()
            }
        )

        results.append({
            "condition_treatment": condition_treatment,
            "stability_score": stability_score,
            "contradiction_score": contradiction_score,
            "papers": total
        })

    return {
        "statusCode": 200,
        "body": {
            "conditions_processed": len(results),
            "scores": results
        }
    }