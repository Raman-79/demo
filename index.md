# AWS Bedrock Agent with Serper API Integration

This guide shows how to create an AWS Bedrock agent that can answer questions directly or use the Serper API to fetch the latest search results when needed.

## Prerequisites

- AWS account with Bedrock access
- Serper API key (from serper.dev)
- AWS CLI configured
- Python 3.9+ (for Lambda functions)

## Step 1: Create Lambda Function for Serper API

First, create a Lambda function that will handle the Serper API calls:

### Lambda Function Code (`lambda_function.py`)

```python
import json
import urllib3
import os

def lambda_handler(event, context):
    """
    Lambda function to call Serper API for web search
    Enhanced to handle multiple search requests efficiently
    """
    
    # Get Serper API key from environment variables
    serper_api_key = os.environ.get('SERPER_API_KEY')
    
    if not serper_api_key:
        return {
            'statusCode': 400,
            'body': json.dumps({
                'error': 'SERPER_API_KEY not found in environment variables'
            })
        }
    
    # Parse the input from Bedrock agent
    try:
        # Bedrock agent sends parameters in a specific format
        parameters = event.get('parameters', [])
        query = None
        num_results = 5  # Default number of results
        search_type = "search"  # Default to general search
        
        for param in parameters:
            if param.get('name') == 'query':
                query = param.get('value')
            elif param.get('name') == 'num_results':
                num_results = int(param.get('value', 5))
            elif param.get('name') == 'search_type':
                search_type = param.get('value', 'search')
        
        if not query:
            return {
                'statusCode': 400,
                'body': json.dumps({
                    'error': 'Query parameter is required'
                })
            }
    
    except Exception as e:
        return {
            'statusCode': 400,
            'body': json.dumps({
                'error': f'Failed to parse input: {str(e)}'
            })
        }
    
    # Call Serper API
    try:
        http = urllib3.PoolManager()
        
        search_payload = {
            'q': query,
            'num': min(num_results, 10),  # Cap at 10 results max
            'hl': 'en',  # Language
            'gl': 'us',  # Country
            'autocorrect': True  # Enable autocorrect for better results
        }
        
        # Determine endpoint based on search type
        endpoint_map = {
            'search': 'https://google.serper.dev/search',
            'news': 'https://google.serper.dev/news',
            'images': 'https://google.serper.dev/images',
            'shopping': 'https://google.serper.dev/shopping'
        }
        
        endpoint = endpoint_map.get(search_type, 'https://google.serper.dev/search')
        
        headers = {
            'X-API-KEY': serper_api_key,
            'Content-Type': 'application/json'
        }
        
        response = http.request(
            'POST',
            endpoint,
            body=json.dumps(search_payload),
            headers=headers,
            timeout=30  # 30 second timeout
        )
        
        if response.status == 200:
            search_results = json.loads(response.data)
            
            # Format results for the agent
            formatted_results = format_search_results(search_results, search_type)
            
            return {
                'statusCode': 200,
                'body': json.dumps({
                    'search_results': formatted_results,
                    'query': query,
                    'search_type': search_type,
                    'total_results': len(formatted_results.get('organic', []))
                })
            }
        else:
            return {
                'statusCode': response.status,
                'body': json.dumps({
                    'error': f'Serper API returned status {response.status}',
                    'query': query
                })
            }
            
    except Exception as e:
        return {
            'statusCode': 500,
            'body': json.dumps({
                'error': f'Failed to call Serper API: {str(e)}',
                'query': query
            })
        }

def format_search_results(search_results, search_type='search'):
    """
    Format search results into a clean structure
    Enhanced to handle different types of search results
    """
    formatted = {
        'organic': [],
        'answer_box': None,
        'knowledge_graph': None,
        'related_searches': []
    }
    
    # Get organic search results
    organic_results = search_results.get('organic', [])
    
    for result in organic_results:
        formatted['organic'].append({
            'title': result.get('title', ''),
            'link': result.get('link', ''),
            'snippet': result.get('snippet', ''),
            'position': result.get('position', 0),
            'date': result.get('date', '')  # Include date when available
        })
    
    # Get answer box if available (for direct answers)
    answer_box = search_results.get('answerBox')
    if answer_box:
        formatted['answer_box'] = {
            'answer': answer_box.get('answer', ''),
            'title': answer_box.get('title', ''),
            'link': answer_box.get('link', '')
        }
    
    # Get knowledge graph info if available
    knowledge_graph = search_results.get('knowledgeGraph')
    if knowledge_graph:
        formatted['knowledge_graph'] = {
            'title': knowledge_graph.get('title', ''),
            'description': knowledge_graph.get('description', ''),
            'attributes': knowledge_graph.get('attributes', {})
        }
    
    # Get related searches for follow-up queries
    related_searches = search_results.get('relatedSearches', [])
    for related in related_searches:
        formatted['related_searches'].append({
            'query': related.get('query', '')
        })
    
    # Handle news results differently
    if search_type == 'news':
        news_results = search_results.get('news', [])
        formatted['news'] = []
        for news in news_results:
            formatted['news'].append({
                'title': news.get('title', ''),
                'link': news.get('link', ''),
                'snippet': news.get('snippet', ''),
                'date': news.get('date', ''),
                'source': news.get('source', '')
            })
    
    return formatted
```

### Deploy Lambda Function

```bash
# Create deployment package
zip -r bedrock-serper-function.zip lambda_function.py

# Create Lambda function
aws lambda create-function \
    --function-name bedrock-serper-search \
    --runtime python3.9 \
    --role arn:aws:iam::YOUR_ACCOUNT_ID:role/lambda-execution-role \
    --handler lambda_function.lambda_handler \
    --zip-file fileb://bedrock-serper-function.zip \
    --environment Variables='{SERPER_API_KEY=your_serper_api_key}'
```

## Step 2: Create IAM Roles and Policies

### Lambda Execution Role

```json
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Effect": "Allow",
            "Action": [
                "logs:CreateLogGroup",
                "logs:CreateLogStream",
                "logs:PutLogEvents"
            ],
            "Resource": "arn:aws:logs:*:*:*"
        }
    ]
}
```

### Bedrock Agent Role

```json
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Effect": "Allow",
            "Action": [
                "bedrock:InvokeModel"
            ],
            "Resource": "*"
        },
        {
            "Effect": "Allow",
            "Action": [
                "lambda:InvokeFunction"
            ],
            "Resource": "arn:aws:lambda:*:*:function:bedrock-serper-search"
        }
    ]
}
```

## Step 3: Create Action Group Schema

Create an OpenAPI schema for the Serper search function:

```json
{
  "openapi": "3.0.1",
  "info": {
    "title": "Web Search API",
    "version": "1.0.0"
  },
  "paths": {
    "/web_search": {
      "post": {
        "operationId": "web_search_function",
        "description": "Search the web for current information",
        "requestBody": {
          "required": true,
          "content": {
            "application/json": {
              "schema": {
                "type": "object",
                "properties": {
                  "query": {
                    "type": "string",
                    "description": "The search query"
                  },
                  "num_results": {
                    "type": "integer",
                    "description": "Number of results to return",
                    "default": 5
                  },
                  "search_type": {
                    "type": "string",
                    "description": "Type of search: search, news, images, shopping",
                    "default": "search"
                  }
                },
                "required": ["query"]
              }
            }
          }
        },
        "responses": {
          "200": {
            "description": "Search results",
            "content": {
              "application/json": {
                "schema": {"type": "object"}
              }
            }
          }
        }
      }
    }
  }
}

```

## Step 4: Create Bedrock Agent using AWS CLI

```bash
# Create the agent
aws bedrock-agent create-agent \
    --agent-name "web-search-assistant" \
    --description "An assistant that can answer questions and search the web for current information" \
    --foundation-model "anthropic.claude-v2" \
    --instruction "You are a helpful AI assistant. For questions about current events, recent news, or information that might be outdated, use the web search function to get the latest information. For general knowledge questions, answer directly using your training data. Always be clear about whether you're using search results or your own knowledge." \
    --agent-resource-role-arn "arn:aws:iam::YOUR_ACCOUNT_ID:role/bedrock-agent-role"
```

## Step 5: Add Action Group to Agent

```bash
# First, upload your OpenAPI schema to S3
aws s3 cp search-api-schema.json s3://your-bucket/search-api-schema.json

# Create action group
aws bedrock-agent create-agent-action-group \
    --agent-id YOUR_AGENT_ID \
    --agent-version DRAFT \
    --action-group-name "web-search" \
    --description "Action group for web searching" \
    --action-group-executor lambda=arn:aws:lambda:us-east-1:YOUR_ACCOUNT_ID:function:bedrock-serper-search \
    --api-schema s3=s3://your-bucket/search-api-schema.json
```

## Step 6: Prepare and Create Agent Alias

```bash
# Prepare the agent
aws bedrock-agent prepare-agent --agent-id YOUR_AGENT_ID

# Create an alias
aws bedrock-agent create-agent-alias \
    --agent-id YOUR_AGENT_ID \
    --alias-name "production" \
    --description "Production version of the web search assistant"
```

## Step 7: Test the Agent

### Python Test Script

```python
import boto3
import json
import time

def test_bedrock_agent():
    client = boto3.client('bedrock-agent-runtime')
    
    # Test with a question that should use search
    response = client.invoke_agent(
        agentId='YOUR_AGENT_ID',
        agentAliasId='YOUR_ALIAS_ID',
        sessionId='test-session-1',
        inputText='What are the latest developments in AI technology this week?'
    )
    
    # Process the response
    for event in response['completion']:
        if 'chunk' in event:
            chunk = event['chunk']
            if 'bytes' in chunk:
                print(chunk['bytes'].decode('utf-8'))

def test_direct_answer():
    client = boto3.client('bedrock-agent-runtime')
    
    # Test with a general knowledge question
    response = client.invoke_agent(
        agentId='YOUR_AGENT_ID',
        agentAliasId='YOUR_ALIAS_ID',
        sessionId='test-session-2',
        inputText='What is the capital of France?'
    )
    
    # Process the response
    for event in response['completion']:
        if 'chunk' in event:
            chunk = event['chunk']
            if 'bytes' in chunk:
                print(chunk['bytes'].decode('utf-8'))

def test_multi_search_scenario():
    client = boto3.client('bedrock-agent-runtime')
    
    # Test with a complex question requiring multiple searches
    response = client.invoke_agent(
        agentId='YOUR_AGENT_ID',
        agentAliasId='YOUR_ALIAS_ID',
        sessionId='test-session-3',
        inputText='Compare the current market performance and recent news for Apple, Microsoft, and Google. Which company has the best outlook for 2024?'
    )
    
    # Process the response
    print("Multi-search scenario response:")
    for event in response['completion']:
        if 'chunk' in event:
            chunk = event['chunk']
            if 'bytes' in chunk:
                print(chunk['bytes'].decode('utf-8'))

def test_iterative_search():
    client = boto3.client('bedrock-agent-runtime')
    
    # Test with a question that might need follow-up searches
    response = client.invoke_agent(
        agentId='YOUR_AGENT_ID',
        agentAliasId='YOUR_ALIAS_ID',
        sessionId='test-session-4',
        inputText='What are the environmental impacts of the latest SpaceX launch, and how do they compare to previous launches this year?'
    )
    
    # Process the response
    print("Iterative search scenario response:")
    for event in response['completion']:
        if 'chunk' in event:
            chunk = event['chunk']
            if 'bytes' in chunk:
                print(chunk['bytes'].decode('utf-8'))

if __name__ == "__main__":
    print("Testing with search query...")
    test_bedrock_agent()
    print("\n" + "="*50 + "\n")
    print("Testing with direct answer...")
    test_direct_answer()
    print("\n" + "="*50 + "\n")
    print("Testing multi-search scenario...")
    test_multi_search_scenario()
    print("\n" + "="*50 + "\n")
    print("Testing iterative search...")
    test_iterative_search()
```

### Example Multi-Search Scenarios

The agent can handle complex queries like:

1. **Comparative Analysis**: "Compare the latest earnings reports for Tesla, Ford, and GM"
   - Search 1: "Tesla Q3 2024 earnings report"
   - Search 2: "Ford Q3 2024 earnings report"  
   - Search 3: "GM Q3 2024 earnings report"
   - Synthesize: Compare revenue, profits, guidance across all three

2. **Event Impact Analysis**: "How did the recent Fed interest rate decision affect tech stocks and crypto markets?"
   - Search 1: "Federal Reserve interest rate decision 2024"
   - Search 2: "tech stocks reaction Fed rate decision"
   - Search 3: "cryptocurrency market Fed interest rate"
   - Synthesize: Connect cause and effect across markets

3. **Trend Analysis**: "What are the latest developments in renewable energy adoption in Europe and Asia?"
   - Search 1: "renewable energy Europe 2024 latest"
   - Search 2: "renewable energy Asia 2024 developments"
   - Search 3: "solar wind energy adoption statistics 2024"
   - Synthesize: Regional comparison with supporting data

## Agent Instructions for Optimal Performance

Here's the recommended instruction prompt for your agent:

```text
You are a helpful AI assistant with access to current web search capabilities. 

Follow these guidelines:
1. For questions about current events, recent news, stock prices, weather, or any information that changes frequently, use the web search function to get up-to-date information.
2. For general knowledge questions, historical facts, or well-established information, answer directly using your training data.
3. If you're unsure whether information might be outdated, err on the side of searching for current information.
4. When presenting search results, cite the sources and indicate that the information comes from recent web searches.
5. Always be transparent about whether you're using search results or your own knowledge base.

**Multi-Search Strategy:**
6. For complex questions that require information from multiple sources or topics, perform multiple targeted searches:
   - Break down the question into component parts
   - Search for each component separately with specific queries
   - Synthesize all findings into a comprehensive answer
   - Example: "Compare the latest stock performance of Tesla vs Ford" → Search "Tesla stock price 2024" then "Ford stock price 2024"
7. Use follow-up searches when initial results are incomplete or raise new questions
8. Continue searching until you have enough information to provide a complete, well-rounded answer

When using search results:
- Synthesize information from multiple sources when possible
- Include relevant URLs for users who want to read more
- Note the recency of the information when relevant
- Clearly indicate when information comes from multiple searches
- If searches contradict each other, acknowledge the discrepancy and explain the differences
```

## Monitoring and Debugging

### CloudWatch Logs
Monitor your Lambda function logs and Bedrock agent traces in CloudWatch to debug any issues.

### Cost Optimization
- Set appropriate timeouts for your Lambda function
- Consider using Bedrock's streaming responses for better user experience
- Monitor Serper API usage to stay within your plan limits

This setup creates a sophisticated agent that can intelligently decide when to search for current information versus using its built-in knowledge, providing users with both comprehensive and up-to-date responses.
