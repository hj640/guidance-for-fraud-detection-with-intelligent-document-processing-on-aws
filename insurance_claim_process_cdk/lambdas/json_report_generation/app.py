import json
import boto3
from boto3.dynamodb.conditions import Key

dynamodb_raw_table = "insuranceclaim-bda-results-raw"

def lambda_handler(event, context):
    claim_id = event["claimId"]

    raw = read_items_from_dynamodb(dynamodb_raw_table, claim_id)
    print(len(raw))
    cleansed = cleanse(raw)

    messages = [ 
      { "Role": "user",
         "Content": [ 
            { 
                "Text": '```json\n' + json.dumps(cleansed,  default=str)+'\n```'
            }
         ]
      }
    ]
    system = [ 
      { 
        "Text": """
        You are an insurance claims analyst. Analyze the provided input JSON and generate a comprehensive claims assessment output.

        INSTRUCTIONS:
        1. Extract and synthesize all relevant information from the input
        2. Cross-reference data points to identify inconsistencies or patterns
        3. Assess validity and potential fraud indicators
        4. Generate the output using the EXACT structure and field names below

        OUTPUT JSON STRUCTURE:
        {
        "callRecordingsSummary": "string - Summary from customer call recordings",
        "claimId": "string - ID of the claim",
        "claimInfo": {
            "claimDate": "string - When claim was filed",
            "claimantSignature": "string - Signature status or empty string",
            "estimatedDamageValue": "string - Estimated damage cost with $ symbol",
            "estimatedRepairCost": "string - Estimated repair cost with $ symbol"
        },
        "descriptionOfDamage": "string - Comprehensive damage summary",
        "estimatesOfTotalCostToRepairPerEachVendor": [
            {
            "scopeOfWork": ["string array - detailed work items with costs, NO 'Total Cost' entry"],
            "totalCost": "string - Total cost as string number",
            "vendorName": "string - Vendor company name"
            }
        ],
        "fraudWarning": "boolean - true if fraud suspected",
        "incidentInfo": {
            "date": "string - Date of incident",
            "description": "string - What happened",
            "time": "string - Time of incident",
            "location": "string - Where it occurred"
        },
        "insights": "string - Key factors and contradictions identified",
        "observations": "string - Validity assessment and fraud indicators",
        "policyHolderDetails": {
            "address": "string - Full address with zip",
            "emailAddress": "string - Email",
            "name": "string - Policy holder name",
            "phoneNumber": "string - Phone with formatting"
        },
        "policyInfo": {
            "agentName": "string - Agent name",
            "contact": "string - Agent phone",
            "insuranceCompany": "string - Company name"
        },
        "policyNo": "string - Policy number",
        "proofOfDamage": [
            {
            "description": "string - Evidence description",
            "fileName": "string - File name",
            "validity": "string - Valid/Invalid assessment",
            "type": "string - Evidence type"
            }
        ],
        "propertyInfo": {
            "additionalInfo": {
            "damagedValue": "string - Property damage value with $",
            "previousClaim": "boolean - Has previous claims",
            "repairCost": "string - Repair cost with $"
            },
            "address": "string - Property address",
            "type": "string - Property type"
        },
        "suspicion": "string - Specific suspicious elements identified",
        "witness": {
            "exists": "boolean - Witness available",
            "name": "string - Witness name",
            "signature": "boolean - Witness signed",
            "statement": "string - Witness statement"
        },
        "riskScore": "number - Risk assessment from 1-10 (10 = highest fraud risk)",
        "recommendedAction": "string - APPROVE/INVESTIGATE/DENY with brief reasoning",
        "inconsistencies": ["string array - Specific data contradictions found during analysis"]
        }

        ANALYSIS REQUIREMENTS:
        - Compare timestamps, locations, and statements for consistency
        - Evaluate damage estimates against incident severity
        - Check for missing documentation or signatures
        - Identify unusual patterns or red flags
        - Calculate riskScore based on: fraud indicators (4 pts), missing docs (2 pts), inconsistencies (2 pts), tampered evidence (2 pts)
        - Set recommendedAction: APPROVE (risk 1-3), INVESTIGATE (risk 4-7), DENY (risk 8-10)
        - List specific inconsistencies found (dates, amounts, locations, statements)

        ANALYSIS DEPTH REQUIREMENTS:
        - observations: 2-3 sentences focusing on evidence validity, missing signatures, and specific fraud indicators with exact file names and dollar amounts
        - insights: 2-3 sentences covering vendor estimate analysis, timeline logic, and final legitimacy assessment with concrete reasoning
        - Be specific: reference exact amounts, dates, file names, and percentages
        - Avoid repetition between observations and insights
        - COST ANALYSIS: Compare vendor estimates against claimant's estimated repair cost for reasonableness. Flag if vendor quotes are significantly higher/lower than claimant estimates or if there's unusual variance between vendors (>20% difference). Assess if repair costs align with damage severity described.
        - VENDOR ASSESSMENT: Evaluate if multiple vendor estimates show consistent pricing patterns and scope alignment. Identify any outliers in pricing or scope that may indicate inflated claims or vendor collusion.

        Generate only valid JSON output with no additional text.
        """
      }
    ]
    
    # TODO implement
    return {
        'statusCode': 200,
        'body': {
            "messages" : messages,
            "system" : system
        }
    }

def cleanse(raw):
    cleansed = {}
    for i in raw:
        print(i.keys())
        cleansed["claimId"] = i["claimId"]
        cleansed[i["name"]] = i["inference_result"] if i["documentType"] != "Others" else i["audio"]
        cleansed[i["name"]]["fraudWarning"] = i.get("fraudDetection", "None")
    return cleansed

def read_items_from_dynamodb(table_name, claim_id):
    # Initialize DynamoDB resource
    dynamodb = boto3.resource('dynamodb')
    
    # Get the table
    table = dynamodb.Table(table_name)
    
    # Perform the query
    response = table.query(
        KeyConditionExpression=Key("claimId").eq(claim_id)
    )
    
    # Extract items from the response
    items = response['Items']
    
    return items