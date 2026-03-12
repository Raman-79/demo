Here is the complete, doc-verified breakdown of exact metrics per service, with corrected NRQL.

---

## ✅ Official AWS Docs — Exact Metrics Per AgentCore Service

---

### ⚙️ RUNTIME

Runtime metrics are batched at 1-minute intervals. AgentCore also provides aggregated metrics for total invocations and sessions.

| Metric | Description |
|---|---|
| `Invocations` | Total requests to the Data Plane API |
| `Throttles` | Requests throttled due to exceeding TPS limits |
| `SystemErrors` | Server-side errors (5xx) |
| `UserErrors` | Client-side errors requiring user action |
| `Errors` | Total system + user errors |
| `Latency` | End-to-end processing time |
| `Sessions` | Total number of agent sessions |
| `TotalSessions` | Sessions across all resources |
| `ActiveConnections` | *(WebSocket only)* Current active WebSocket connections per agent |
| `WebSocketBytesReceived` | *(WebSocket only)* Bytes received from clients to agent containers |
| `WebSocketBytesSent` | *(WebSocket only)* Bytes sent from agent containers to clients |
| `agent.runtime.vcpu.hours.used` | CPU consumption in vCPU-hours |
| `agent.runtime.memory.gb_hours.used` | Memory consumption in GB-hours |

**Dimensions:** `Resource` (Agent Runtime ARN), `AgentRuntimeId`, `AgentEndpointId`, `Operation`

```sql
-- Runtime: Core health
SELECT sum(aws.bedrock-agentcore.Invocations),
       average(aws.bedrock-agentcore.Latency),
       sum(aws.bedrock-agentcore.Errors),
       sum(aws.bedrock-agentcore.Throttles),
       sum(aws.bedrock-agentcore.SystemErrors),
       sum(aws.bedrock-agentcore.UserErrors)
FROM Metric
WHERE aws.namespace = 'Bedrock-AgentCore'
AND Resource LIKE '%agentruntime%'
FACET AgentRuntimeId
TIMESERIES SINCE 1 hour ago

-- Runtime: Sessions
SELECT sum(aws.bedrock-agentcore.Sessions),
       sum(aws.bedrock-agentcore.TotalSessions)
FROM Metric
WHERE Resource LIKE '%agentruntime%'
TIMESERIES SINCE 1 hour ago

-- Runtime: WebSocket (if applicable)
SELECT sum(aws.bedrock-agentcore.ActiveConnections),
       sum(aws.bedrock-agentcore.WebSocketBytesReceived),
       sum(aws.bedrock-agentcore.WebSocketBytesSent)
FROM Metric
WHERE Resource LIKE '%agentruntime%'
TIMESERIES SINCE 1 hour ago

-- Runtime: Resource usage
SELECT sum(`aws.bedrock-agentcore.agent.runtime.vcpu.hours.used`),
       sum(`aws.bedrock-agentcore.agent.runtime.memory.gb_hours.used`)
FROM Metric
WHERE Resource LIKE '%agentruntime%'
FACET AgentEndpointId
TIMESERIES SINCE 24 hours ago
```

---

### 🧠 MEMORY

The AgentCore memory resource type provides the following metrics by default: Latency, Invocations, SystemErrors, UserErrors, Errors, Throttles, and CreationCount.

| Metric | Description |
|---|---|
| `Latency` | End-to-end processing time |
| `Invocations` | Total API requests (data + control plane + ingestion events) |
| `SystemErrors` | AWS server-side errors |
| `UserErrors` | Client-side errors |
| `Errors` | Total errors including memory ingestion errors |
| `Throttles` | Throttled requests (also counted in Invocations, Errors, UserErrors) |
| `CreationCount` | Number of memory events and records created |

**Dimensions:** `Resource` (Memory ARN), `Operation` (e.g. `CreateEvent`, `RetrieveMemoryRecords`)

```sql
-- Memory: Core health
SELECT sum(aws.bedrock-agentcore.Invocations),
       average(aws.bedrock-agentcore.Latency),
       sum(aws.bedrock-agentcore.Errors),
       sum(aws.bedrock-agentcore.SystemErrors),
       sum(aws.bedrock-agentcore.UserErrors),
       sum(aws.bedrock-agentcore.Throttles),
       sum(aws.bedrock-agentcore.CreationCount)
FROM Metric
WHERE aws.namespace = 'Bedrock-AgentCore'
AND Resource LIKE '%memory%'
FACET Operation
TIMESERIES SINCE 1 hour ago
```

---

### 🔗 GATEWAY

Gateway publishes invocation and usage metrics to CloudWatch, batched at 1-minute intervals. Dimensions include: `Operation`, `Protocol`, `Method`, `Resource`, and `Name` (tool name).

**Invocation Metrics:**

| Metric | Description |
|---|---|
| `Invocations` | Total requests to Data Plane API |
| `Throttles` | Requests throttled (HTTP 429) |
| `SystemErrors` | Requests failed with 5xx status |
| `UserErrors` | Requests failed with 4xx (excluding 429) |
| `Latency` | Time to first response token (ms) |
| `Duration` | Total end-to-end processing time (ms) |
| `TargetExecutionTime` | Time taken by Lambda/OpenAPI target alone (ms) |

**Usage Metrics:**

| Metric | Description |
|---|---|
| `TargetType` | Total requests served per target type (MCP, Lambda, OpenAPI) |

```sql
-- Gateway: Core invocation health
SELECT sum(aws.bedrock-agentcore.Invocations),
       average(aws.bedrock-agentcore.Latency),
       average(aws.bedrock-agentcore.Duration),
       average(aws.bedrock-agentcore.TargetExecutionTime),
       sum(aws.bedrock-agentcore.SystemErrors),
       sum(aws.bedrock-agentcore.UserErrors),
       sum(aws.bedrock-agentcore.Throttles)
FROM Metric
WHERE aws.namespace = 'Bedrock-AgentCore'
AND Resource LIKE '%gateway%'
FACET Method
TIMESERIES SINCE 1 hour ago

-- Gateway: Target type breakdown
SELECT sum(aws.bedrock-agentcore.TargetType)
FROM Metric
WHERE Resource LIKE '%gateway%'
FACET Name
SINCE 1 hour ago
```

---

### 💻 CODE INTERPRETER & 🌐 BROWSER

Built-in tool metrics are batched at one-minute intervals. For resource usage metrics, the `Service` dimension takes the value `AgentCore.CodeInterpreter` or `AgentCore.Browser`.

**Invoke Tool:**

| Metric | Description |
|---|---|
| `Invocations` | Total API requests |
| `Throttles` | Throttled requests (HTTP 429) |
| `SystemErrors` | Server-side errors |
| `UserErrors` | Client-side errors |
| `Latency` | Time to first response token |

**Create Tool Session:**

| Metric | Description |
|---|---|
| `Invocations` | Total session creation requests |
| `Throttles` | Throttled session creation requests |
| `SystemErrors` | Server-side errors |
| `UserErrors` | Client-side errors |
| `Latency` | Time to first response token |
| `Duration` | Duration of the tool session (`CodeInterpreterSession` / `BrowserSession`) |

**Browser-only (User Takeover):**

| Metric | Description |
|---|---|
| `TakerOverCount` | Total user takeovers |
| `TakerOverReleaseCount` | Total user control releases |
| `TakerOverDuration` | Duration of each takeover |

**Resource Usage (both tools):**

| Metric | Dimension |
|---|---|
| `CPUUsed-vCPUHours` | `Service = AgentCore.CodeInterpreter` or `AgentCore.Browser` |
| `MemoryUsed-GBHours` | same |

```sql
-- Code Interpreter: All metrics
SELECT sum(aws.bedrock-agentcore.Invocations),
       average(aws.bedrock-agentcore.Latency),
       average(aws.bedrock-agentcore.Duration),
       sum(aws.bedrock-agentcore.SystemErrors),
       sum(aws.bedrock-agentcore.UserErrors),
       sum(aws.bedrock-agentcore.Throttles),
       sum(`aws.bedrock-agentcore.CPUUsed-vCPUHours`),
       sum(`aws.bedrock-agentcore.MemoryUsed-GBHours`)
FROM Metric
WHERE Service = 'AgentCore.CodeInterpreter'
TIMESERIES SINCE 1 hour ago

-- Browser: All metrics including takeover
SELECT sum(aws.bedrock-agentcore.Invocations),
       average(aws.bedrock-agentcore.Latency),
       average(aws.bedrock-agentcore.Duration),
       sum(aws.bedrock-agentcore.SystemErrors),
       sum(aws.bedrock-agentcore.UserErrors),
       sum(aws.bedrock-agentcore.TakerOverCount),
       sum(aws.bedrock-agentcore.TakerOverReleaseCount),
       average(aws.bedrock-agentcore.TakerOverDuration),
       sum(`aws.bedrock-agentcore.CPUUsed-vCPUHours`),
       sum(`aws.bedrock-agentcore.MemoryUsed-GBHours`)
FROM Metric
WHERE Service = 'AgentCore.Browser'
TIMESERIES SINCE 1 hour ago
```

---

### 🔐 IDENTITY

Identity metrics are split across two namespaces and three categories — Usage (in `AWS/Usage`), Authorization, and Resource Access (both in `AWS/Bedrock-AgentCore`).

**Usage Metrics** (`AWS/Usage` namespace):

| Metric | Description |
|---|---|
| `CallCount` | Number of calls to Identity Service operations |
| `ThrottleCount` | Number of throttled calls |

**Authorization Metrics** (`AWS/Bedrock-AgentCore` namespace):

| Metric | Description |
|---|---|
| `WorkloadAccessTokenFetchSuccess` | Successful workload access token fetches |
| `WorkloadAccessTokenFetchFailures` | Failed fetches by `ExceptionType` |
| `WorkloadAccessTokenFetchThrottles` | Throttled workload token fetches |

**Resource Access Metrics** (`AWS/Bedrock-AgentCore` namespace):

| Metric | Description |
|---|---|
| `ResourceAccessTokenFetchSuccess` | Successful OAuth2 token fetches |
| `ResourceAccessTokenFetchFailures` | Failed OAuth2 fetches by `ExceptionType` |
| `ResourceAccessTokenFetchThrottles` | Throttled OAuth2 fetches |
| `ApiKeyFetchSuccess` | Successful API key fetches |
| `ApiKeyFetchFailures` | Failed API key fetches by `ExceptionType` |
| `ApiKeyFetchThrottles` | Throttled API key fetches |

**Dimensions:** `WorkloadIdentity`, `WorkloadIdentityDirectory`, `TokenVault`, `ProviderName`, `FlowType`, `ExceptionType`

```sql
-- Identity: Authorization health
SELECT sum(aws.bedrock-agentcore.WorkloadAccessTokenFetchSuccess),
       sum(aws.bedrock-agentcore.WorkloadAccessTokenFetchFailures),
       sum(aws.bedrock-agentcore.WorkloadAccessTokenFetchThrottles)
FROM Metric
WHERE aws.namespace = 'Bedrock-AgentCore'
FACET WorkloadIdentity
TIMESERIES SINCE 1 hour ago

-- Identity: Resource access (OAuth2 + API Key)
SELECT sum(aws.bedrock-agentcore.ResourceAccessTokenFetchSuccess),
       sum(aws.bedrock-agentcore.ResourceAccessTokenFetchFailures),
       sum(aws.bedrock-agentcore.ApiKeyFetchSuccess),
       sum(aws.bedrock-agentcore.ApiKeyFetchFailures)
FROM Metric
WHERE aws.namespace = 'Bedrock-AgentCore'
FACET ProviderName
TIMESERIES SINCE 1 hour ago

-- Identity: Failures by exception type
SELECT sum(aws.bedrock-agentcore.WorkloadAccessTokenFetchFailures),
       sum(aws.bedrock-agentcore.ResourceAccessTokenFetchFailures),
       sum(aws.bedrock-agentcore.ApiKeyFetchFailures)
FROM Metric
FACET ExceptionType
SINCE 1 hour ago

-- Identity: Usage quota tracking (AWS/Usage namespace)
SELECT sum(aws.usage.CallCount),
       sum(aws.usage.ThrottleCount)
FROM Metric
WHERE aws.namespace = 'AWS/Usage'
AND Service = 'BedrockAgentCore'
TIMESERIES SINCE 1 hour ago
```

---

### 📌 Master Summary Table

| Service | Total Metrics | Unique Differentiator |
|---|---|---|
| **Runtime** | 13 (incl. WebSocket + resource usage) | `Resource LIKE '%agentruntime%'` |
| **Memory** | 7 | `Resource LIKE '%memory%'` |
| **Gateway** | 8 (7 invocation + 1 usage) | `Resource LIKE '%gateway%'` |
| **Code Interpreter** | 8 (invoke + session + resource) | `Service = 'AgentCore.CodeInterpreter'` |
| **Browser** | 11 (invoke + session + takeover + resource) | `Service = 'AgentCore.Browser'` |
| **Identity** | 11 across 2 namespaces | `WorkloadIdentity` / `ProviderName` dimensions |
