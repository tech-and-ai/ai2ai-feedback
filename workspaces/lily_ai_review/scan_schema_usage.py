#!/usr/bin/env python
"""
Script to scan the codebase for references to database schemas and tables.
This helps identify which schemas and tables are actually being used in the code.
"""
import os
import re
import json
import argparse
from collections import defaultdict
from typing import Dict, List, Set, Tuple

# Define schemas and their tables
SCHEMAS = {
    "_be_deleted_dev_tools": ["code_templates", "template_categories", "template_category_map"],
    "_be_deleted_email_content": ["styles", "template_types", "templates"],
    "_be_deleted_rag_system": ["code_chunks", "indexed_files", "search_queries"],
    "auth": ["users"],  # Only checking auth.users since that's the main one we care about
    "autonomous": ["code", "config", "defects", "documentation", "plans", "review_tasks", "tests", "work_sessions"],
    "public": [
        "admin_users", "code_chunks", "indexed_files", "mxbai_chunks",
        "saas_citation_styles", "saas_job_tracking", "saas_lily_ai_config",
        "saas_lily_callout_types", "saas_lily_quotes", "saas_membership_types",
        "saas_notification_events", "saas_notification_logs", "saas_notification_settings",
        "saas_notification_templates", "saas_paper_credit_usage", "saas_paper_credits",
        "saas_paper_reviews", "saas_paper_sources", "saas_paper_usage_tracking",
        "saas_papers", "saas_pricing_addons", "saas_pricing_display",
        "saas_pricing_features", "saas_pricing_plans", "saas_prompts",
        "saas_research_chunks", "saas_research_citations", "saas_research_context",
        "saas_research_extraction_metadata", "saas_research_quotes",
        "saas_research_section_plans", "saas_research_sessions", "saas_research_sources",
        "saas_researchpack_sections", "saas_serp_api_resources", "saas_static_content",
        "saas_stripe_config", "saas_topic_moderation", "saas_user_subscriptions",
        "saas_users", "tool_context_entries", "tool_context_entry_tags",
        "tool_context_relationships", "tool_context_tags", "tool_todo_items"
    ],
    "research_content": [
        "citation_formats", "diagram_templates", "discipline_research_types",
        "discipline_section_templates", "disciplines", "lily_callout_templates",
        "lily_callout_types", "research_source_configs", "research_types",
        "section_templates", "section_types"
    ]
}

def find_schema_references(file_path: str, schemas: Dict[str, List[str]]) -> Dict[str, Set[str]]:
    """
    Find references to schemas and tables in a file.

    Args:
        file_path: Path to the file to scan
        schemas: Dictionary of schemas and their tables

    Returns:
        Dictionary of schemas and the tables referenced in the file
    """
    references = defaultdict(set)

    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()

            # Check for schema references
            for schema, tables in schemas.items():
                # Look for explicit schema references like "schema.table" or 'schema.table'
                schema_pattern = rf'["\']?{schema}\.["\']?'
                if re.search(schema_pattern, content):
                    references[schema].add("__schema_reference__")

                # Look for table references
                for table in tables:
                    # Different patterns to match table references
                    patterns = [
                        # Explicit schema.table reference
                        rf'{schema}\.{table}\b',
                        # Table name in quotes with schema
                        rf'{schema}\.[\'"]{table}[\'"]',
                        # Table name in SQL queries
                        rf'FROM\s+{schema}\.{table}\b',
                        rf'JOIN\s+{schema}\.{table}\b',
                        rf'UPDATE\s+{schema}\.{table}\b',
                        rf'INSERT\s+INTO\s+{schema}\.{table}\b',
                        # Table name in Supabase queries
                        rf'\.from\([\'"]?{schema}\.{table}[\'"]?\)',
                        # Table name without schema in public schema
                        rf'FROM\s+{table}\b' if schema == 'public' else None,
                        rf'JOIN\s+{table}\b' if schema == 'public' else None,
                        rf'UPDATE\s+{table}\b' if schema == 'public' else None,
                        rf'INSERT\s+INTO\s+{table}\b' if schema == 'public' else None,
                        rf'\.from\([\'"]?{table}[\'"]?\)' if schema == 'public' else None,
                    ]

                    # Remove None patterns
                    patterns = [p for p in patterns if p]

                    for pattern in patterns:
                        if re.search(pattern, content, re.IGNORECASE):
                            references[schema].add(table)
                            break
    except Exception as e:
        print(f"Error scanning {file_path}: {str(e)}")

    return references

def scan_directory(directory: str, schemas: Dict[str, List[str]], extensions: List[str] = None, exclude_dirs: List[str] = None) -> Dict[str, Dict[str, Set[str]]]:
    """
    Scan a directory for references to schemas and tables.

    Args:
        directory: Directory to scan
        schemas: Dictionary of schemas and their tables
        extensions: List of file extensions to scan (default: ['.py', '.sql', '.js', '.ts'])
        exclude_dirs: List of directories to exclude (default: ['venv', '.venv', 'node_modules', '.git'])

    Returns:
        Dictionary of schemas and tables with files where they are referenced
    """
    if extensions is None:
        extensions = ['.py', '.sql', '.js', '.ts', '.html']

    if exclude_dirs is None:
        exclude_dirs = ['venv', '.venv', 'node_modules', '.git', '__pycache__', '.pytest_cache']

    references = defaultdict(lambda: defaultdict(set))
    file_count = 0

    for root, dirs, files in os.walk(directory):
        # Skip excluded directories
        dirs[:] = [d for d in dirs if d not in exclude_dirs]

        for file in files:
            if any(file.endswith(ext) for ext in extensions):
                file_path = os.path.join(root, file)
                file_references = find_schema_references(file_path, schemas)

                for schema, tables in file_references.items():
                    for table in tables:
                        references[schema][table].add(file_path)

                file_count += 1
                if file_count % 100 == 0:
                    print(f"Scanned {file_count} files...")

    return references

def generate_report(references: Dict[str, Dict[str, Set[str]]], output_file: str = None):
    """
    Generate a report of schema and table references.

    Args:
        references: Dictionary of schemas and tables with files where they are referenced
        output_file: Path to the output file (default: None, print to console)
    """
    report = []
    report.append("# Schema Usage Report\n")

    # Count references
    schema_counts = {}
    for schema, tables in references.items():
        schema_counts[schema] = sum(len(files) for files in tables.values())

    # Sort schemas by reference count (descending)
    sorted_schemas = sorted(schema_counts.items(), key=lambda x: x[1], reverse=True)

    for schema, count in sorted_schemas:
        report.append(f"## {schema} ({count} references)\n")

        tables = references[schema]
        # Sort tables by reference count (descending)
        sorted_tables = sorted(tables.items(), key=lambda x: len(x[1]), reverse=True)

        for table, files in sorted_tables:
            if table == "__schema_reference__":
                report.append(f"- Schema referenced directly in {len(files)} files\n")
            else:
                report.append(f"- {table} ({len(files)} references)\n")
                # List up to 5 files
                file_list = list(files)[:5]
                for file in file_list:
                    report.append(f"  - {file}\n")
                if len(files) > 5:
                    report.append(f"  - ... and {len(files) - 5} more files\n")

        report.append("\n")

    # Add unused schemas section
    report.append("## Unused Schemas\n")
    for schema in SCHEMAS:
        if schema not in references:
            report.append(f"- {schema}\n")

    report_text = "".join(report)

    if output_file:
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(report_text)
        print(f"Report written to {output_file}")
    else:
        print(report_text)

def main():
    parser = argparse.ArgumentParser(description='Scan codebase for database schema references')
    parser.add_argument('directory', help='Directory to scan')
    parser.add_argument('--output', '-o', help='Output file for the report')
    parser.add_argument('--extensions', '-e', nargs='+',
                        help='File extensions to scan (default: .py .sql .js .ts .html)')
    parser.add_argument('--exclude-dirs', '-x', nargs='+',
                        help='Directories to exclude (default: venv .venv node_modules .git __pycache__ .pytest_cache)')

    args = parser.parse_args()

    print(f"Scanning {args.directory} for schema references...")

    # Use default values if not provided
    extensions = args.extensions
    exclude_dirs = args.exclude_dirs

    if exclude_dirs:
        print(f"Excluding directories: {', '.join(exclude_dirs)}")

    references = scan_directory(args.directory, SCHEMAS, extensions, exclude_dirs)

    generate_report(references, args.output)

if __name__ == "__main__":
    main()
