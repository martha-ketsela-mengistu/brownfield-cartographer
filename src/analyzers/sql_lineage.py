import re
import sqlglot
from sqlglot import exp
from typing import Set, List, Dict, Any

class SQLLineageAnalyzer:
    def __init__(self, dialect: str = "duckdb"):
        self.dialect = dialect

    def extract_dependencies(self, sql_content: str) -> Dict[str, List[str]]:
        """
        Extracts source tables and target tables from a SQL string.
        Returns a dict with 'sources' and 'targets' keys.
        """
        sources = set()
        targets = set()
        
        # Pre-process dbt templates
        # {{ ref('name') }} -> name
        processed_sql = re.sub(r"\{\{\s*ref\(['\"](\w+)['\"]\)\s*\}\}", r"\1", sql_content)
        # {{ source('src', 'table') }} -> src_table
        processed_sql = re.sub(r"\{\{\s*source\(['\"](\w+)['\"]\s*,\s*['\"](\w+)['\"]\)\s*\}\}", r"\1_\2", processed_sql)
        # Remove other jinja tags to satisfy parser
        processed_sql = re.sub(r"\{%.*?%\}", "", processed_sql)
        processed_sql = re.sub(r"\{\{.*?\}\}", "placeholder_table", processed_sql)

        try:
            # Parse the SQL
            for expression in sqlglot.parse(processed_sql, read=self.dialect):
                # Find tables in FROM and JOIN
                for table in expression.find_all(exp.Table):
                    table_name = table.sql(dialect=self.dialect)
                    sources.add(table_name)
                
                # Find target table in INSERT INTO or CREATE TABLE
                if isinstance(expression, exp.Create) or isinstance(expression, exp.Insert):
                    target_table = expression.find(exp.Table)
                    if target_table:
                        targets.add(target_table.sql(dialect=self.dialect))
                        
                # Handle CTEs: remove CTE names from sources
                ctes = {cte.alias_or_name for cte in expression.find_all(exp.CTE)}
                sources = sources - ctes
        except Exception as e:
            # If sqlglot fails, fallback to regex for dbt specifically
            dbt_refs = re.findall(r"\{\{\s*ref\(['\"](\w+)['\"]\)\s*\}\}", sql_content)
            for ref in dbt_refs:
                sources.add(ref)
            dbt_sources = re.findall(r"\{\{\s*source\(['\"](\w+)['\"]\s*,\s*['\"](\w+)['\"]\)\s*\}\}", sql_content)
            for src, table in dbt_sources:
                sources.add(f"{src}_{table}")
            
        return {
            "sources": list(sources),
            "targets": list(targets)
        }
