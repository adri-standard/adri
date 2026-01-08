"""ADRI Schema Consistency Validator.

This module validates ADRI schema definitions at design-time to catch conflicts
between field types and their descriptions, preventing runtime validation issues.

Key Features:
- Type/description conflict detection (e.g., type: string but description mentions "array")
- SQL reserved word detection in field names
- Constraint consistency validation
- Array type completeness checks
- Conflicting constraint detection

This validator runs at schema definition time to catch issues early.
"""

from typing import Dict, Any, List, Optional, Set
from dataclasses import dataclass
from enum import Enum
import re
import logging

logger = logging.getLogger(__name__)


# SQL Reserved Words that should trigger warnings
SQL_RESERVED_WORDS = {
    "SELECT",
    "FROM",
    "WHERE",
    "ORDER",
    "GROUP",
    "BY",
    "INSERT",
    "UPDATE",
    "DELETE",
    "JOIN",
    "INNER",
    "OUTER",
    "LEFT",
    "RIGHT",
    "FULL",
    "CROSS",
    "CASE",
    "WHEN",
    "THEN",
    "ELSE",
    "END",
    "NULL",
    "TRUE",
    "FALSE",
    "DATE",
    "TIME",
    "TIMESTAMP",
    "USER",
    "COUNT",
    "SUM",
    "AVG",
    "MIN",
    "MAX",
    "DISTINCT",
    "UNION",
    "INTERSECT",
    "EXCEPT",
    "HAVING",
    "AS",
    "ON",
    "CREATE",
    "DROP",
    "ALTER",
    "TABLE",
    "INDEX",
    "VIEW",
    "TRIGGER",
    "PRIMARY",
    "FOREIGN",
    "KEY",
    "REFERENCES",
    "CHECK",
    "UNIQUE",
    "AND",
    "OR",
    "NOT",
    "IN",
    "BETWEEN",
    "LIKE",
    "IS",
    "EXISTS",
}

# PostgreSQL-specific reserved words
POSTGRESQL_RESERVED_WORDS = SQL_RESERVED_WORDS | {
    "ANALYSE",
    "ANALYZE",
    "ARRAY",
    "ASYMMETRIC",
    "AUTHORIZATION",
    "BINARY",
    "COLLATE",
    "CONCURRENTLY",
    "CURRENT_CATALOG",
    "CURRENT_DATE",
    "CURRENT_ROLE",
    "CURRENT_SCHEMA",
    "CURRENT_TIME",
    "CURRENT_TIMESTAMP",
    "CURRENT_USER",
    "DEFERRABLE",
    "DO",
    "FETCH",
    "FREEZE",
    "GRANT",
    "ILIKE",
    "INITIALLY",
    "ISNULL",
    "LATERAL",
    "LIMIT",
    "LOCALTIME",
    "LOCALTIMESTAMP",
    "NOTNULL",
    "OFFSET",
    "OVERLAPS",
    "PLACING",
    "RETURNING",
    "SESSION_USER",
    "SIMILAR",
    "SYMMETRIC",
    "TABLESAMPLE",
    "VARIADIC",
    "VERBOSE",
    "WINDOW",
}

# MySQL-specific reserved words
MYSQL_RESERVED_WORDS = SQL_RESERVED_WORDS | {
    "ACCESSIBLE",
    "ADD",
    "ALL",
    "ANALYZE",
    "ASENSITIVE",
    "BEFORE",
    "BIGINT",
    "BINARY",
    "BLOB",
    "BOTH",
    "CALL",
    "CASCADE",
    "CHANGE",
    "CHAR",
    "CHARACTER",
    "CONDITION",
    "CONSTRAINT",
    "CONTINUE",
    "CONVERT",
    "CURRENT_DATE",
    "CURRENT_TIME",
    "CURRENT_TIMESTAMP",
    "CURRENT_USER",
    "CURSOR",
    "DATABASE",
    "DATABASES",
    "DAY_HOUR",
    "DAY_MICROSECOND",
    "DAY_MINUTE",
    "DAY_SECOND",
    "DEC",
    "DECIMAL",
    "DECLARE",
    "DEFAULT",
    "DELAYED",
    "DETERMINISTIC",
    "DIV",
    "DOUBLE",
    "DUAL",
    "EACH",
    "ELSEIF",
    "ENCLOSED",
    "ESCAPED",
    "EXIT",
    "EXPLAIN",
    "FLOAT",
    "FLOAT4",
    "FLOAT8",
    "FORCE",
    "FULLTEXT",
    "GENERAL",
    "HIGH_PRIORITY",
    "HOUR_MICROSECOND",
    "HOUR_MINUTE",
    "HOUR_SECOND",
    "IF",
    "IGNORE",
    "INFILE",
    "INOUT",
    "INT",
    "INT1",
    "INT2",
    "INT3",
    "INT4",
    "INT8",
    "INTEGER",
    "INTERVAL",
    "ITERATE",
    "KEYS",
    "KILL",
    "LEADING",
    "LEAVE",
    "LIMIT",
    "LINEAR",
    "LINES",
    "LOAD",
    "LOCALTIME",
    "LOCALTIMESTAMP",
    "LOCK",
    "LONG",
    "LONGBLOB",
    "LONGTEXT",
    "LOOP",
    "LOW_PRIORITY",
    "MATCH",
    "MEDIUMBLOB",
    "MEDIUMINT",
    "MEDIUMTEXT",
    "MIDDLEINT",
    "MINUTE_MICROSECOND",
    "MINUTE_SECOND",
    "MOD",
    "MODIFIES",
    "NATURAL",
    "NO_WRITE_TO_BINLOG",
    "NUMERIC",
    "OPTIMIZE",
    "OPTION",
    "OPTIONALLY",
    "OUT",
    "OUTFILE",
    "PRECISION",
    "PROCEDURE",
    "PURGE",
    "RANGE",
    "READ",
    "READS",
    "REAL",
    "REGEXP",
    "RELEASE",
    "RENAME",
    "REPEAT",
    "REPLACE",
    "REQUIRE",
    "RESIGNAL",
    "RESTRICT",
    "RETURN",
    "REVOKE",
    "RLIKE",
    "SCHEMA",
    "SCHEMAS",
    "SECOND_MICROSECOND",
    "SENSITIVE",
    "SEPARATOR",
    "SHOW",
    "SIGNAL",
    "SMALLINT",
    "SPATIAL",
    "SPECIFIC",
    "SQL",
    "SQLEXCEPTION",
    "SQLSTATE",
    "SQLWARNING",
    "SQL_BIG_RESULT",
    "SQL_CALC_FOUND_ROWS",
    "SQL_SMALL_RESULT",
    "SSL",
    "STARTING",
    "STRAIGHT_JOIN",
    "TERMINATED",
    "TINYBLOB",
    "TINYINT",
    "TINYTEXT",
    "TRAILING",
    "UNDO",
    "UNLOCK",
    "UNSIGNED",
    "USAGE",
    "USE",
    "USING",
    "UTC_DATE",
    "UTC_TIME",
    "UTC_TIMESTAMP",
    "VARBINARY",
    "VARCHAR",
    "VARCHARACTER",
    "VARYING",
    "WHILE",
    "WITH",
    "WRITE",
    "X509",
    "XOR",
    "YEAR_MONTH",
    "ZEROFILL",
}

# Oracle-specific reserved words
ORACLE_RESERVED_WORDS = SQL_RESERVED_WORDS | {
    "ACCESS",
    "ADD",
    "ALL",
    "AUDIT",
    "CLUSTER",
    "COLUMN",
    "COMMENT",
    "COMPRESS",
    "CONNECT",
    "EXCLUSIVE",
    "FILE",
    "IDENTIFIED",
    "IMMEDIATE",
    "INCREMENT",
    "INITIAL",
    "LOCK",
    "LONG",
    "MAXEXTENTS",
    "MINUS",
    "MODE",
    "NOAUDIT",
    "NOCOMPRESS",
    "NOWAIT",
    "NUMBER",
    "OFFLINE",
    "ONLINE",
    "PCTFREE",
    "PRIOR",
    "RAW",
    "RENAME",
    "RESOURCE",
    "ROW",
    "ROWID",
    "ROWNUM",
    "ROWS",
    "SESSION",
    "SHARE",
    "SIZE",
    "SMALLINT",
    "START",
    "SUCCESSFUL",
    "SYNONYM",
    "SYSDATE",
    "UID",
    "VALIDATE",
    "VARCHAR",
    "VARCHAR2",
    "WHENEVER",
}

# SQL dialect mapping
SQL_DIALECT_RESERVED_WORDS = {
    "postgresql": POSTGRESQL_RESERVED_WORDS,
    "mysql": MYSQL_RESERVED_WORDS,
    "oracle": ORACLE_RESERVED_WORDS,
    "standard": SQL_RESERVED_WORDS,
}


class ConsistencyIssueType(str, Enum):
    """Types of schema consistency issues."""

    TYPE_DESCRIPTION_CONFLICT = "TYPE_DESCRIPTION_CONFLICT"
    SQL_RESERVED_WORD = "SQL_RESERVED_WORD"
    INCOMPLETE_ARRAY_SPEC = "INCOMPLETE_ARRAY_SPEC"
    CONFLICTING_CONSTRAINTS = "CONFLICTING_CONSTRAINTS"
    INVALID_CONSTRAINT_VALUE = "INVALID_CONSTRAINT_VALUE"
    MISSING_TYPE = "MISSING_TYPE"
    INVALID_TYPE = "INVALID_TYPE"


class ConsistencyIssueSeverity(str, Enum):
    """Severity levels for consistency issues."""

    CRITICAL = "CRITICAL"  # Will cause runtime failures
    ERROR = "ERROR"  # Will likely cause issues
    WARNING = "WARNING"  # Best practice violation


@dataclass
class ConsistencyIssue:
    """Represents a schema consistency issue."""

    type: ConsistencyIssueType
    severity: ConsistencyIssueSeverity
    field_name: str
    message: str
    remediation: str
    conflicting_values: Optional[Dict[str, Any]] = None


@dataclass
class SchemaConsistencyReport:
    """Report of schema consistency validation."""

    is_valid: bool
    total_fields: int
    issues_found: int
    issues: List[ConsistencyIssue]

    def has_critical_issues(self) -> bool:
        """Check if there are critical issues."""
        return any(i.severity == ConsistencyIssueSeverity.CRITICAL for i in self.issues)

    def has_errors(self) -> bool:
        """Check if there are errors (CRITICAL or ERROR)."""
        return any(
            i.severity
            in [ConsistencyIssueSeverity.CRITICAL, ConsistencyIssueSeverity.ERROR]
            for i in self.issues
        )

    def get_issues_by_severity(
        self, severity: ConsistencyIssueSeverity
    ) -> List[ConsistencyIssue]:
        """Get issues filtered by severity."""
        return [i for i in self.issues if i.severity == severity]

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for logging/serialization."""
        return {
            "is_valid": self.is_valid,
            "total_fields": self.total_fields,
            "issues_found": self.issues_found,
            "has_critical_issues": self.has_critical_issues(),
            "has_errors": self.has_errors(),
            "issues": [
                {
                    "type": i.type.value,
                    "severity": i.severity.value,
                    "field_name": i.field_name,
                    "message": i.message,
                    "remediation": i.remediation,
                    "conflicting_values": i.conflicting_values,
                }
                for i in self.issues
            ],
        }


class SchemaConsistencyValidator:
    """Validates ADRI schema definitions for consistency issues."""

    # Valid ADRI types
    VALID_TYPES = {"string", "integer", "float", "boolean", "date", "array"}

    # Type indicator patterns in descriptions
    TYPE_INDICATORS = {
        "array": [
            r"\barray\b",
            r"\blist\b",
            r"\[\s*\]",
            r"JSON array",
            r"comma-separated",
            r"multiple",
            r"collection of",
        ],
        "integer": [r"\binteger\b", r"\bwhole number\b", r"\bcount\b", r"\bid\b"],
        "float": [
            r"\bfloat\b",
            r"\bdecimal\b",
            r"\bpercent\b",
            r"\brate\b",
            r"\bscore\b",
            r"\bratio\b",
        ],
        "boolean": [r"\bboolean\b", r"\btrue/false\b", r"\byes/no\b", r"\bflag\b"],
        "date": [r"\bdate\b", r"\btimestamp\b", r"\btime\b", r"ISO\s*8601"],
    }

    def __init__(self, strict_mode: bool = False):
        """Initialize validator.

        Args:
            strict_mode: If True, escalate some WARNINGs to ERRORs
        """
        self.strict_mode = strict_mode
        self.custom_type_patterns: Dict[str, List[Dict[str, Any]]] = {}
        self.sql_dialects: Set[str] = set()
        self.custom_sql_reserved: Set[str] = set()
        self.sql_strict_mode: bool = False

    def validate(self, adri_spec: Dict[str, Any]) -> SchemaConsistencyReport:
        """Validate ADRI schema for consistency issues.

        Args:
            adri_spec: ADRI specification with field_requirements

        Returns:
            SchemaConsistencyReport with validation results
        """
        issues: List[ConsistencyIssue] = []

        if not adri_spec or "field_requirements" not in adri_spec:
            return SchemaConsistencyReport(
                is_valid=False, total_fields=0, issues_found=0, issues=[]
            )

        field_requirements = adri_spec["field_requirements"]
        if not isinstance(field_requirements, dict):
            return SchemaConsistencyReport(
                is_valid=False, total_fields=0, issues_found=0, issues=[]
            )

        # Load custom type patterns from YAML if present
        self._load_type_patterns(adri_spec)

        # Load SQL compatibility settings from YAML if present
        self._load_sql_compatibility(adri_spec)

        # Validate each field
        for field_name, field_spec in field_requirements.items():
            if not isinstance(field_spec, dict):
                continue

            # Check for SQL reserved words (including dialect-specific)
            issues.extend(self._check_sql_reserved_words(field_name))
            issues.extend(self._check_sql_dialect_conflicts(field_name))

            # Check for missing or invalid type
            issues.extend(self._check_field_type(field_name, field_spec))

            # Check for type/description conflicts
            issues.extend(self._check_type_description_conflict(field_name, field_spec))

            # Check custom type patterns (domain-specific)
            issues.extend(self._check_custom_type_patterns(field_name, field_spec))

            # Check array type completeness
            if field_spec.get("type") == "array":
                issues.extend(self._check_array_completeness(field_name, field_spec))

            # Check constraint consistency
            issues.extend(self._check_constraint_consistency(field_name, field_spec))

        total_fields = len(field_requirements)
        issues_found = len(issues)
        is_valid = not any(
            i.severity == ConsistencyIssueSeverity.CRITICAL for i in issues
        )

        return SchemaConsistencyReport(
            is_valid=is_valid,
            total_fields=total_fields,
            issues_found=issues_found,
            issues=issues,
        )

    def _load_type_patterns(self, adri_spec: Dict[str, Any]) -> None:
        """Load custom type patterns from ADRI standard YAML.

        Args:
            adri_spec: ADRI specification that may contain type_patterns
        """
        # Clear any existing patterns
        self.custom_type_patterns = {}

        # Check if type_patterns section exists
        if "type_patterns" not in adri_spec:
            return

        type_patterns = adri_spec["type_patterns"]
        if not isinstance(type_patterns, dict):
            logger.warning("type_patterns section is not a dictionary, skipping")
            return

        # Load each type's patterns
        for expected_type, patterns in type_patterns.items():
            if expected_type not in self.VALID_TYPES:
                logger.warning(
                    f"Unknown type '{expected_type}' in type_patterns, skipping"
                )
                continue

            if not isinstance(patterns, list):
                logger.warning(
                    f"Patterns for type '{expected_type}' must be a list, skipping"
                )
                continue

            self.custom_type_patterns[expected_type] = []

            for pattern_config in patterns:
                if not isinstance(pattern_config, dict):
                    continue

                if "indicators" not in pattern_config:
                    continue

                indicators = pattern_config["indicators"]
                if isinstance(indicators, str):
                    indicators = [indicators]
                elif not isinstance(indicators, list):
                    continue

                self.custom_type_patterns[expected_type].append(
                    {
                        "indicators": indicators,
                        "constraints": pattern_config.get("constraints", {}),
                    }
                )

        if self.custom_type_patterns:
            logger.info(
                f"Loaded custom type patterns for {len(self.custom_type_patterns)} type(s)"
            )

    def _check_custom_type_patterns(
        self, field_name: str, field_spec: Dict[str, Any]
    ) -> List[ConsistencyIssue]:
        """Check custom domain-specific type patterns from YAML.

        Args:
            field_name: Name of the field
            field_spec: Field specification

        Returns:
            List of consistency issues
        """
        issues = []

        if not self.custom_type_patterns:
            return issues

        if "type" not in field_spec:
            return issues

        field_type = field_spec.get("type")

        # Check each custom type pattern
        for expected_type, pattern_configs in self.custom_type_patterns.items():
            if expected_type == field_type:
                continue  # Type matches expected, no issue

            for pattern_config in pattern_configs:
                indicators = pattern_config["indicators"]

                # Check if field name matches any indicator pattern
                for indicator in indicators:
                    if re.search(indicator, field_name, re.IGNORECASE):
                        issues.append(
                            ConsistencyIssue(
                                type=ConsistencyIssueType.TYPE_DESCRIPTION_CONFLICT,
                                severity=ConsistencyIssueSeverity.ERROR,
                                field_name=field_name,
                                message=(
                                    f"Field '{field_name}' has type '{field_type}' but name pattern "
                                    f"suggests '{expected_type}' (matched pattern: '{indicator}')"
                                ),
                                remediation=(
                                    f"Domain-specific type pattern suggests:\n"
                                    f"  • Change type from '{field_type}' to '{expected_type}'\n"
                                    f"  • Or rename field to avoid matching pattern '{indicator}'"
                                ),
                                conflicting_values={
                                    "declared_type": field_type,
                                    "pattern_suggests": expected_type,
                                    "matched_pattern": indicator,
                                },
                            )
                        )
                        break  # Only report first match per pattern

        return issues

    def _load_sql_compatibility(self, adri_spec: Dict[str, Any]) -> None:
        """Load SQL compatibility settings from ADRI standard YAML.

        This is an enterprise feature for multi-database compatibility checking.

        Args:
            adri_spec: ADRI specification that may contain sql_compatibility
        """
        # Clear any existing settings
        self.sql_dialects = set()
        self.custom_sql_reserved = set()
        self.sql_strict_mode = False

        # Check if sql_compatibility section exists
        if "sql_compatibility" not in adri_spec:
            return

        sql_config = adri_spec["sql_compatibility"]
        if not isinstance(sql_config, dict):
            logger.warning("sql_compatibility section is not a dictionary, skipping")
            return

        # Load target dialects
        target_dialects = sql_config.get("target_dialects", [])
        if isinstance(target_dialects, str):
            target_dialects = [target_dialects]

        if isinstance(target_dialects, list):
            for dialect in target_dialects:
                dialect_lower = dialect.lower()
                if dialect_lower in SQL_DIALECT_RESERVED_WORDS:
                    self.sql_dialects.add(dialect_lower)
                else:
                    logger.warning(f"Unknown SQL dialect '{dialect}', skipping")

        # Load strict mode setting
        self.sql_strict_mode = sql_config.get("strict_mode", False)

        # Load custom reserved words
        custom_reserved = sql_config.get("custom_reserved_words", [])
        if isinstance(custom_reserved, list):
            self.custom_sql_reserved = {word.upper() for word in custom_reserved}

        if self.sql_dialects:
            logger.info(
                f"Loaded SQL compatibility for dialects: {', '.join(self.sql_dialects)}"
            )
            if self.sql_strict_mode:
                logger.info("SQL strict mode enabled")

    def _check_sql_dialect_conflicts(self, field_name: str) -> List[ConsistencyIssue]:
        """Check if field name conflicts with dialect-specific SQL reserved words.

        Enterprise feature for multi-database compatibility.

        Args:
            field_name: Name of the field to check

        Returns:
            List of consistency issues (empty if none found)
        """
        issues = []

        # Skip if no dialects configured
        if not self.sql_dialects and not self.custom_sql_reserved:
            return issues

        field_name_upper = field_name.upper()

        # Check custom reserved words first
        if field_name_upper in self.custom_sql_reserved:
            severity = (
                ConsistencyIssueSeverity.ERROR
                if self.sql_strict_mode
                else ConsistencyIssueSeverity.WARNING
            )
            issues.append(
                ConsistencyIssue(
                    type=ConsistencyIssueType.SQL_RESERVED_WORD,
                    severity=severity,
                    field_name=field_name,
                    message=f"Field name '{field_name}' conflicts with custom SQL reserved word",
                    remediation=(
                        f"Field name conflicts with custom reserved words. Consider renaming:\n"
                        f"  • {field_name}_value\n"
                        f"  • {field_name}_field\n"
                        f"  • {field_name}_data"
                    ),
                )
            )

        # Check each configured dialect
        conflicting_dialects = []
        for dialect in self.sql_dialects:
            reserved_words = SQL_DIALECT_RESERVED_WORDS.get(dialect, set())
            if field_name_upper in reserved_words:
                conflicting_dialects.append(dialect)

        if conflicting_dialects:
            severity = (
                ConsistencyIssueSeverity.ERROR
                if self.sql_strict_mode
                else ConsistencyIssueSeverity.WARNING
            )
            dialects_str = ", ".join(conflicting_dialects)
            issues.append(
                ConsistencyIssue(
                    type=ConsistencyIssueType.SQL_RESERVED_WORD,
                    severity=severity,
                    field_name=field_name,
                    message=f"Field name '{field_name}' is reserved in SQL dialect(s): {dialects_str}",
                    remediation=(
                        f"Field name conflicts with {dialects_str} reserved words. Suggestions:\n"
                        f"  • {field_name}_value\n"
                        f"  • {field_name}_field\n"
                        f"  • {field_name}_data\n"
                        f"Affected databases: {dialects_str}"
                    ),
                    conflicting_values={"conflicting_dialects": conflicting_dialects},
                )
            )

        return issues

    def _check_sql_reserved_words(self, field_name: str) -> List[ConsistencyIssue]:
        """Check if field name is a SQL reserved word.

        Args:
            field_name: Name of the field to check

        Returns:
            List of consistency issues (empty if none found)
        """
        issues = []

        # Check if field name (case-insensitive) is a reserved word
        if field_name.upper() in SQL_RESERVED_WORDS:
            severity = (
                ConsistencyIssueSeverity.ERROR
                if self.strict_mode
                else ConsistencyIssueSeverity.WARNING
            )
            issues.append(
                ConsistencyIssue(
                    type=ConsistencyIssueType.SQL_RESERVED_WORD,
                    severity=severity,
                    field_name=field_name,
                    message=f"Field name '{field_name}' is a SQL reserved word",
                    remediation=(
                        f"Consider renaming to avoid SQL conflicts. Suggestions:\n"
                        f"  • {field_name}_value\n"
                        f"  • {field_name}_field\n"
                        f"  • {field_name}_data"
                    ),
                )
            )

        return issues

    def _check_field_type(
        self, field_name: str, field_spec: Dict[str, Any]
    ) -> List[ConsistencyIssue]:
        """Check if field has valid type definition.

        Args:
            field_name: Name of the field
            field_spec: Field specification

        Returns:
            List of consistency issues
        """
        issues = []

        if "type" not in field_spec:
            issues.append(
                ConsistencyIssue(
                    type=ConsistencyIssueType.MISSING_TYPE,
                    severity=ConsistencyIssueSeverity.CRITICAL,
                    field_name=field_name,
                    message=f"Field '{field_name}' is missing 'type' attribute",
                    remediation=(
                        f"Add a 'type' attribute to field '{field_name}'. "
                        f"Valid types: {', '.join(self.VALID_TYPES)}"
                    ),
                )
            )
        elif field_spec["type"] not in self.VALID_TYPES:
            issues.append(
                ConsistencyIssue(
                    type=ConsistencyIssueType.INVALID_TYPE,
                    severity=ConsistencyIssueSeverity.CRITICAL,
                    field_name=field_name,
                    message=(
                        f"Field '{field_name}' has invalid type '{field_spec['type']}'"
                    ),
                    remediation=(
                        f"Change type to one of: {', '.join(self.VALID_TYPES)}"
                    ),
                    conflicting_values={"current_type": field_spec["type"]},
                )
            )

        return issues

    def _check_type_description_conflict(
        self, field_name: str, field_spec: Dict[str, Any]
    ) -> List[ConsistencyIssue]:
        """Check for conflicts between field type and description.

        Args:
            field_name: Name of the field
            field_spec: Field specification

        Returns:
            List of consistency issues
        """
        issues = []

        if "type" not in field_spec or "description" not in field_spec:
            return issues

        field_type = field_spec["type"]
        description = field_spec["description"].lower()

        # Check if description suggests a different type
        for suggested_type, patterns in self.TYPE_INDICATORS.items():
            if suggested_type == field_type:
                continue  # Type matches, no conflict

            for pattern in patterns:
                if re.search(pattern, description, re.IGNORECASE):
                    issues.append(
                        ConsistencyIssue(
                            type=ConsistencyIssueType.TYPE_DESCRIPTION_CONFLICT,
                            severity=ConsistencyIssueSeverity.ERROR,
                            field_name=field_name,
                            message=(
                                f"Field '{field_name}' has type '{field_type}' but description "
                                f"suggests '{suggested_type}' (matched pattern: '{pattern}')"
                            ),
                            remediation=(
                                f"Fix the conflict by either:\n"
                                f"  1. Changing type from '{field_type}' to '{suggested_type}'\n"
                                f"  2. Updating the description to match type '{field_type}'"
                            ),
                            conflicting_values={
                                "declared_type": field_type,
                                "description_suggests": suggested_type,
                                "description": field_spec["description"],
                                "matched_pattern": pattern,
                            },
                        )
                    )
                    break  # Only report first match per type

        return issues

    def _check_array_completeness(
        self, field_name: str, field_spec: Dict[str, Any]
    ) -> List[ConsistencyIssue]:
        """Check if array type has complete specification.

        Args:
            field_name: Name of the field
            field_spec: Field specification

        Returns:
            List of consistency issues
        """
        issues = []

        if "items" not in field_spec:
            severity = (
                ConsistencyIssueSeverity.ERROR
                if self.strict_mode
                else ConsistencyIssueSeverity.WARNING
            )
            issues.append(
                ConsistencyIssue(
                    type=ConsistencyIssueType.INCOMPLETE_ARRAY_SPEC,
                    severity=severity,
                    field_name=field_name,
                    message=(f"Array field '{field_name}' lacks 'items' specification"),
                    remediation=(
                        "Add 'items' specification to define array element type:\n"
                        "  items:\n"
                        "    type: string  # or integer, float, etc.\n"
                        "    min_length: 1  # optional constraints\n"
                        "    max_length: 100"
                    ),
                )
            )
        else:
            # Check items specification completeness
            items_spec = field_spec["items"]
            if isinstance(items_spec, dict) and "type" not in items_spec:
                issues.append(
                    ConsistencyIssue(
                        type=ConsistencyIssueType.INCOMPLETE_ARRAY_SPEC,
                        severity=ConsistencyIssueSeverity.ERROR,
                        field_name=field_name,
                        message=(
                            f"Array field '{field_name}' items specification lacks 'type'"
                        ),
                        remediation=(
                            "Add 'type' to items specification:\n"
                            "  items:\n"
                            "    type: string  # or integer, float, etc."
                        ),
                    )
                )

        # Check for array bounds
        if "min_items" not in field_spec and "max_items" not in field_spec:
            issues.append(
                ConsistencyIssue(
                    type=ConsistencyIssueType.INCOMPLETE_ARRAY_SPEC,
                    severity=ConsistencyIssueSeverity.WARNING,
                    field_name=field_name,
                    message=(
                        f"Array field '{field_name}' lacks size constraints "
                        f"(min_items/max_items)"
                    ),
                    remediation=(
                        "Consider adding array size constraints:\n"
                        "  min_items: 1  # minimum number of elements\n"
                        "  max_items: 50  # maximum number of elements"
                    ),
                )
            )

        return issues

    def _check_constraint_consistency(
        self, field_name: str, field_spec: Dict[str, Any]
    ) -> List[ConsistencyIssue]:
        """Check for conflicting or invalid constraints.

        Args:
            field_name: Name of the field
            field_spec: Field specification

        Returns:
            List of consistency issues
        """
        issues = []
        field_type = field_spec.get("type")

        # Check min/max value consistency for numeric types
        if field_type in ["integer", "float"]:
            if "min_value" in field_spec and "max_value" in field_spec:
                min_val = field_spec["min_value"]
                max_val = field_spec["max_value"]
                if min_val > max_val:
                    issues.append(
                        ConsistencyIssue(
                            type=ConsistencyIssueType.CONFLICTING_CONSTRAINTS,
                            severity=ConsistencyIssueSeverity.ERROR,
                            field_name=field_name,
                            message=(
                                f"Field '{field_name}' has min_value ({min_val}) "
                                f"greater than max_value ({max_val})"
                            ),
                            remediation=(
                                f"Fix constraint values:\n"
                                f"  min_value: {min_val}  # must be <= max_value\n"
                                f"  max_value: {max_val}"
                            ),
                            conflicting_values={
                                "min_value": min_val,
                                "max_value": max_val,
                            },
                        )
                    )

        # Check min/max length consistency for strings
        if field_type == "string":
            if "min_length" in field_spec and "max_length" in field_spec:
                min_len = field_spec["min_length"]
                max_len = field_spec["max_length"]
                if min_len > max_len:
                    issues.append(
                        ConsistencyIssue(
                            type=ConsistencyIssueType.CONFLICTING_CONSTRAINTS,
                            severity=ConsistencyIssueSeverity.ERROR,
                            field_name=field_name,
                            message=(
                                f"Field '{field_name}' has min_length ({min_len}) "
                                f"greater than max_length ({max_len})"
                            ),
                            remediation=(
                                f"Fix constraint values:\n"
                                f"  min_length: {min_len}  # must be <= max_length\n"
                                f"  max_length: {max_len}"
                            ),
                            conflicting_values={
                                "min_length": min_len,
                                "max_length": max_len,
                            },
                        )
                    )

        # Check min/max items consistency for arrays
        if field_type == "array":
            if "min_items" in field_spec and "max_items" in field_spec:
                min_items = field_spec["min_items"]
                max_items = field_spec["max_items"]
                if min_items > max_items:
                    issues.append(
                        ConsistencyIssue(
                            type=ConsistencyIssueType.CONFLICTING_CONSTRAINTS,
                            severity=ConsistencyIssueSeverity.ERROR,
                            field_name=field_name,
                            message=(
                                f"Field '{field_name}' has min_items ({min_items}) "
                                f"greater than max_items ({max_items})"
                            ),
                            remediation=(
                                f"Fix constraint values:\n"
                                f"  min_items: {min_items}  # must be <= max_items\n"
                                f"  max_items: {max_items}"
                            ),
                            conflicting_values={
                                "min_items": min_items,
                                "max_items": max_items,
                            },
                        )
                    )

        # Check for invalid constraint values
        for constraint_name in [
            "min_value",
            "max_value",
            "min_length",
            "max_length",
            "min_items",
            "max_items",
        ]:
            if constraint_name in field_spec:
                value = field_spec[constraint_name]
                if not isinstance(value, (int, float)):
                    issues.append(
                        ConsistencyIssue(
                            type=ConsistencyIssueType.INVALID_CONSTRAINT_VALUE,
                            severity=ConsistencyIssueSeverity.ERROR,
                            field_name=field_name,
                            message=(
                                f"Field '{field_name}' has invalid {constraint_name} type: "
                                f"{type(value).__name__} (expected number)"
                            ),
                            remediation=f"Change {constraint_name} to a numeric value",
                            conflicting_values={constraint_name: value},
                        )
                    )
                elif value < 0 and constraint_name.startswith("min"):
                    issues.append(
                        ConsistencyIssue(
                            type=ConsistencyIssueType.INVALID_CONSTRAINT_VALUE,
                            severity=ConsistencyIssueSeverity.WARNING,
                            field_name=field_name,
                            message=(
                                f"Field '{field_name}' has negative {constraint_name}: {value}"
                            ),
                            remediation=f"Consider if negative {constraint_name} is intentional",
                            conflicting_values={constraint_name: value},
                        )
                    )

        return issues


def validate_schema_consistency(
    adri_spec: Dict[str, Any], strict_mode: bool = False
) -> SchemaConsistencyReport:
    """Validate ADRI schema for consistency issues.

    Convenience function for one-off validation.

    Args:
        adri_spec: ADRI specification with field_requirements
        strict_mode: If True, escalate some WARNINGs to ERRORs

    Returns:
        SchemaConsistencyReport with validation results
    """
    validator = SchemaConsistencyValidator(strict_mode=strict_mode)
    report = validator.validate(adri_spec)

    # Log results
    if report.issues_found > 0:
        logger.warning(
            f"Schema consistency validation found {report.issues_found} issue(s) "
            f"in {report.total_fields} field(s)"
        )
        for issue in report.issues:
            log_level = (
                logging.ERROR
                if issue.severity
                in [ConsistencyIssueSeverity.CRITICAL, ConsistencyIssueSeverity.ERROR]
                else logging.WARNING
            )
            logger.log(
                log_level,
                f"[{issue.severity.value}] {issue.field_name}: {issue.message}",
            )
    else:
        logger.info(
            f"Schema consistency validation passed for {report.total_fields} field(s)"
        )

    return report
