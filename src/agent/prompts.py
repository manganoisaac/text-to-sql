USER_PROMPT = """
Turn the following natural language question into an SQL query:
{user_query}

Here are some examples:
{few_shot_examples}.

Here are the relevant parts of the database schema for you to generate a query for:
{relevant_schemas_with_sample_values}

If the user's question maps to multiple possible interpretations (e.g., "revenue" could mean gross or net), return a structured clarification request instead of guessing.
"""

BACKCHECK_PROMPT = """
What question does this SQL query answer?
{sql_query}
"""

SANITY_CHECKER_PROMPT = """
Given the user query:
    {user_query}

Which generated the SQL:
    {sql_query}

And the resulting retrieval:
    {result}

Perform the following sanity checks:
    - aggregate_range: Are aggregated values within plausible ranges?
    - count_magnitude: Do counts match expected magnitudes?
    - date_range: Are date ranges within the data's timespan?
    - null_heavy_join: Are there NULL-heavy columns that might indicate a bad JOIN?

For each violation, set category to exactly one of the listed names and include a reason and severity.
Return at most one violation for each category. If SQL is fine, return an empty list.
"""
