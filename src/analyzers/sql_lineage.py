import re
import sqlglot
from sqlglot import exp
from typing import Set, List, Dict, Any

class SQLLineageAnalyzer:
    def __init__(self, dialect: str = "duckdb"):
        self.dialect = dialect

    def detect_dialect(self, sql_content: str) -> str:
        """
        Heuristic-based SQL dialect detection.
        """
        sql_lower = sql_content.lower()
        if "qualify" in sql_lower and "over" in sql_lower:
            return "snowflake" # or bigquery
        if "unnest" in sql_lower:
            return "bigquery" # or postgres
        if "copy " in sql_lower and "from stdin" in sql_lower:
            return "postgres"
        if "datetime" in sql_lower and "extract" in sql_lower:
            return "bigquery"
        return self.dialect # Default

    def extract_dependencies(self, sql_content: str) -> Dict[str, List[str]]:
        """
        Extracts source tables and target tables from a SQL string.
        Returns a dict with 'sources' and 'targets' keys.
        """
        sources = set()
        targets = set()
        
        # Detect dialect dynamically
        current_dialect = self.detect_dialect(sql_content)
        
        # Explicitly extract dbt refs and sources (definitive dependencies)
        dbt_refs = re.findall(r"\{\{\s*ref\(['\"](\w+)['\"]\)\s*\}\}", sql_content)
        for ref in dbt_refs:
            sources.add(ref)
            
        dbt_sources = re.findall(r"\{\{\s*source\(['\"](\w+)['\"]\s*,\s*['\"](\w+)['\"]\)\s*\}\}", sql_content)
        for src, table in dbt_sources:
            sources.add(f"{src}_{table}")

        # Pre-process dbt templates to satisfy parser for other SQL dependencies
        processed_sql = re.sub(r"\{\{\s*ref\(['\"](\w+)['\"]\)\s*\}\}", r"\1", sql_content)
        processed_sql = re.sub(r"\{\{\s*source\(['\"](\w+)['\"]\s*,\s*['\"](\w+)['\"]\)\s*\}\}", r"\1_\2", processed_sql)
        processed_sql = re.sub(r"\{%.*?%\}", "", processed_sql)
        processed_sql = re.sub(r"\{\{.*?\}\}", "placeholder_table", processed_sql)

        try:
            # Parse the SQL
            for expression in sqlglot.parse(processed_sql, read=current_dialect):
                # Find tables in FROM and JOIN
                for table in expression.find_all(exp.Table):
                    table_name = table.sql(dialect=current_dialect)
                    sources.add(table_name)
                
                # Find target table in INSERT INTO or CREATE TABLE
                if isinstance(expression, exp.Create) or isinstance(expression, exp.Insert):
                    target_table = expression.find(exp.Table)
                    if target_table:
                        targets.add(target_table.sql(dialect=current_dialect))
                        
                # Handle CTEs: remove CTE names from sources ONLY IF they aren't explicit dbt refs
                ctes = {cte.alias_or_name for cte in expression.find_all(exp.CTE)}
                sources = (sources - ctes).union(set(dbt_refs)).union({f"{src}_{tbl}" for src, tbl in dbt_sources})
                
        except Exception as e:
            # Fallback already handled by regex above
            pass
            
        return {
            "sources": list(sources),
            "targets": list(targets)
        }
