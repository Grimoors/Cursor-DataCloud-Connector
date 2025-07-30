# Salesforce Data Cloud MCP Server Usage Examples

This guide provides practical examples of how to use the Salesforce Data Cloud MCP Server with Cursor.

## Basic Query Examples

### 1. Simple Contact Query

**User Prompt:**

```
Show me all contacts from California
```

**Expected SQL Generated:**

```sql
SELECT Id__c, Name__c, Email__c, State__c
FROM Contact__dlm
WHERE State__c = 'CA'
```

**Expected Response:**

```
| Name | Email | State |
|------|-------|-------|
| John Doe | john.doe@example.com | CA |
| Jane Smith | jane.smith@example.com | CA |
```

### 2. Opportunity Analysis

**User Prompt:**

```
Find all opportunities over $50,000 in the technology industry
```

**Expected SQL Generated:**

```sql
SELECT Id__c, Name__c, Amount__c, Industry__c, StageName__c
FROM Opportunity__dlm
WHERE Amount__c > 50000 AND Industry__c = 'Technology'
```

### 3. Complex Join Query

**User Prompt:**

```
Show me contacts with their associated opportunities, but only for accounts in the energy sector
```

**Expected SQL Generated:**

```sql
SELECT
    c.Name__c as ContactName,
    c.Email__c,
    o.Name__c as OpportunityName,
    o.Amount__c,
    a.Name__c as AccountName,
    a.Industry__c
FROM Contact__dlm c
JOIN Account__dlm a ON c.AccountId__c = a.Id__c
JOIN Opportunity__dlm o ON a.Id__c = o.AccountId__c
WHERE a.Industry__c = 'Energy'
```

## Metadata Exploration Examples

### 1. Discover Available Objects

**User Prompt:**

```
What objects are available in Data Cloud?
```

**Tool Used:** `list_available_objects`

**Expected Response:**

```
Available Data Model Objects:
- Contact__dlm (Contact records)
- Account__dlm (Account records)
- Opportunity__dlm (Opportunity records)
- UnifiedIndividual__dlm (Unified individual profiles)
- Lead__dlm (Lead records)
...
```

### 2. Explore Object Schema

**User Prompt:**

```
What fields are available in the Contact object?
```

**Tool Used:** `get_object_metadata`

**Expected SQL Generated:**

```sql
-- The AI will first get metadata, then show available fields
```

**Expected Response:**

```
Contact__dlm Fields:
- Id__c (Text) - Unique identifier
- Name__c (Text) - Contact name
- Email__c (Text) - Email address
- Phone__c (Text) - Phone number
- State__c (Text) - State/province
- Industry__c (Text) - Industry
...
```

## Advanced Query Examples

### 1. Aggregation and Grouping

**User Prompt:**

```
What's the total opportunity value by industry?
```

**Expected SQL Generated:**

```sql
SELECT
    Industry__c,
    COUNT(*) as OpportunityCount,
    SUM(Amount__c) as TotalValue,
    AVG(Amount__c) as AverageValue
FROM Opportunity__dlm
GROUP BY Industry__c
ORDER BY TotalValue DESC
```

### 2. Date Range Queries

**User Prompt:**

```
Show me opportunities created in the last 30 days
```

**Expected SQL Generated:**

```sql
SELECT Id__c, Name__c, Amount__c, CreatedDate__c
FROM Opportunity__dlm
WHERE CreatedDate__c >= DATE_SUB(CURRENT_DATE, INTERVAL 30 DAY)
```

### 3. Subqueries and Complex Logic

**User Prompt:**

```
Find accounts that have more than 5 opportunities
```

**Expected SQL Generated:**

```sql
SELECT
    a.Id__c,
    a.Name__c,
    a.Industry__c,
    COUNT(o.Id__c) as OpportunityCount
FROM Account__dlm a
JOIN Opportunity__dlm o ON a.Id__c = o.AccountId__c
GROUP BY a.Id__c, a.Name__c, a.Industry__c
HAVING COUNT(o.Id__c) > 5
```

## Real-World Use Cases

### 1. Sales Pipeline Analysis

**User Prompt:**

```
Analyze our sales pipeline by stage and show conversion rates
```

**Expected SQL Generated:**

```sql
SELECT
    StageName__c,
    COUNT(*) as StageCount,
    SUM(Amount__c) as StageValue,
    ROUND(COUNT(*) * 100.0 / SUM(COUNT(*)) OVER(), 2) as ConversionRate
FROM Opportunity__dlm
GROUP BY StageName__c
ORDER BY StageValue DESC
```

### 2. Customer Segmentation

**User Prompt:**

```
Segment our customers by opportunity value and show their contact information
```

**Expected SQL Generated:**

```sql
SELECT
    c.Name__c,
    c.Email__c,
    c.Phone__c,
    a.Name__c as AccountName,
    a.Industry__c,
    SUM(o.Amount__c) as TotalOpportunityValue,
    CASE
        WHEN SUM(o.Amount__c) > 100000 THEN 'Enterprise'
        WHEN SUM(o.Amount__c) > 50000 THEN 'Mid-Market'
        ELSE 'SMB'
    END as CustomerSegment
FROM Contact__dlm c
JOIN Account__dlm a ON c.AccountId__c = a.Id__c
JOIN Opportunity__dlm o ON a.Id__c = o.AccountId__c
GROUP BY c.Id__c, c.Name__c, c.Email__c, c.Phone__c, a.Name__c, a.Industry__c
ORDER BY TotalOpportunityValue DESC
```

### 3. Lead Quality Analysis

**User Prompt:**

```
Show me leads with their conversion status and associated opportunities
```

**Expected SQL Generated:**

```sql
SELECT
    l.Id__c,
    l.Name__c,
    l.Email__c,
    l.Company__c,
    l.Status__c,
    l.LeadSource__c,
    COUNT(o.Id__c) as ConvertedOpportunities,
    SUM(o.Amount__c) as TotalConvertedValue
FROM Lead__dlm l
LEFT JOIN Opportunity__dlm o ON l.Id__c = o.LeadId__c
GROUP BY l.Id__c, l.Name__c, l.Email__c, l.Company__c, l.Status__c, l.LeadSource__c
ORDER BY TotalConvertedValue DESC
```

## Error Handling Examples

### 1. Invalid Object Name

**User Prompt:**

```
Query the Users table
```

**Expected Response:**

```
❌ Error: Object 'Users' not found in Data Cloud. Available objects include: Contact__dlm, Account__dlm, Opportunity__dlm, etc.
```

### 2. Invalid Field Reference

**User Prompt:**

```
Show me contacts with their phone numbers
```

**Expected SQL Generated:**

```sql
SELECT Id__c, Name__c, Phone__c FROM Contact__dlm LIMIT 10
```

**If Phone\_\_c doesn't exist:**

```
❌ Error: Field 'Phone__c' not found in Contact__dlm. Available fields: Id__c, Name__c, Email__c, State__c, etc.
```

## Best Practices

### 1. Always Use LIMIT for Large Queries

**Good:**

```
Show me the first 10 contacts from California
```

**Better:**

```
Show me contacts from California (limit to 10 results)
```

### 2. Be Specific About Fields

**Good:**

```
Show me contact names and emails from California
```

**Better than:**

```
Show me all contacts from California
```

### 3. Use Clear Industry/State Names

**Good:**

```
Find opportunities in the Technology industry
```

**Better than:**

```
Find tech opportunities
```

## Troubleshooting Queries

### 1. Check Available Objects

If you're unsure what objects exist:

```
What objects are available in Data Cloud?
```

### 2. Check Object Schema

If you're unsure what fields exist:

```
What fields are available in the Contact object?
```

### 3. Test Simple Queries First

Start with simple queries to verify the connection:

```
Show me 5 contacts
```

### 4. Use Connection Test

If you're having issues:

```
Test the connection to Salesforce Data Cloud
```

## Advanced Tips

1. **Use the AI's Context**: The AI remembers previous queries and can build on them
2. **Ask for Explanations**: "Explain what this query does" or "What does this result mean?"
3. **Request Formatting**: "Format this as a table" or "Show this as a chart"
4. **Combine Queries**: "Now show me the same data but only for closed opportunities"

Remember, the AI will generate ANSI SQL queries, not SOQL. The Data Cloud Query API uses standard SQL syntax with Data Model Object names (ending in `__dlm`).
