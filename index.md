# pip install ragas datasets boto3

import boto3, json, os
from datasets import Dataset
from ragas import evaluate
from ragas.metrics import faithfulness, answer_relevancy, answer_correctness

# --------------------------------------------------
# 1.  Config
REGION = "us-east-1"
KB_ID  = "<your-knowledge-base-id>"
MODEL_ARN = "arn:aws:bedrock:us-east-1::foundation-model/anthropic.claude-3-sonnet-20240229-v1:0"

agent_runtime = boto3.client("bedrock-agent-runtime", region_name=REGION)
bedrock_runtime = boto3.client("bedrock-runtime", region_name=REGION)   # for the judge LLM

# --------------------------------------------------
# 2.  Evaluation pairs (only question + ground_truth)
eval_pairs = [
    {
        "question": "What is Amazon Bedrock?",
        "ground_truth": "Amazon Bedrock is a fully managed service providing access to high-performing foundation models."
    },
    {
        "question": "How does Bedrock protect my data?",
        "ground_truth": "Bedrock keeps customer data private; it is not shared with model providers."
    },
    # … add more …
]

# --------------------------------------------------
# 3.  Retrieve-and-Generate (answer + contexts)
def retrieve_and_generate(question: str):
    resp = agent_runtime.retrieve_and_generate(
        input={"text": question},
        retrieveAndGenerateConfiguration={
            "type": "KNOWLEDGE_BASE",
            "knowledgeBaseConfiguration": {
                "knowledgeBaseId": KB_ID,
                "modelArn": MODEL_ARN
            }
        }
    )
    contexts = [c["content"]["text"] for c in resp["retrievalResults"]]
    answer   = resp["output"]["text"]
    return answer, contexts

# --------------------------------------------------
# 4.  Build dataset
rows = []
for pair in eval_pairs:
    answer, contexts = retrieve_and_generate(pair["question"])
    rows.append({
        "question":      pair["question"],
        "ground_truth":  pair["ground_truth"],
        "answer":        answer,
        "contexts":      contexts
    })

dataset = Dataset.from_list(rows)

# --------------------------------------------------
# 5.  Evaluate with RAGAS
# RAGAS will automatically use the Bedrock judge model
# (anthropic.claude-3-sonnet-20240229-v1:0) via boto3 under the hood
scores = evaluate(
    dataset,
    metrics=[faithfulness, answer_relevancy, answer_correctness]
)

print(scores)                   # overall averages
scores.to_pandas().to_csv("ragas_scores.csv", index=False)
