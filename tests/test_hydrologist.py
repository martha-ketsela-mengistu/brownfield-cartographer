import pytest
from src.agents.hydrologist import HydrologistAgent
from src.analyzers.sql_lineage import SQLLineageAnalyzer

def test_sql_lineage_extraction():
    analyzer = SQLLineageAnalyzer()
    sql = "CREATE TABLE target AS SELECT * FROM source_table JOIN secondary_table ON 1=1"
    deps = analyzer.extract_dependencies(sql)
    
    assert "source_table" in deps["sources"]
    assert "secondary_table" in deps["sources"]
    assert "target" in deps["targets"]

def test_sql_dialect_detection():
    analyzer = SQLLineageAnalyzer()
    sql_bq = "SELECT * FROM `project.dataset.table` WHERE _PARTITIONTIME > TIMESTAMP('2023-01-01')"
    dialect = analyzer.detect_dialect(sql_bq)
    # Our simple heuristic should pick up hallmarks
    assert analyzer.detect_dialect("SELECT * FROM table QUALIFY ROW_NUMBER() OVER() = 1") == "snowflake"
