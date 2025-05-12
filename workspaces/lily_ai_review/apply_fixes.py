#!/usr/bin/env python3
"""
Script to apply fixes to the SERP API integration issues.

This script will:
1. Create backups of the original files
2. Apply the fixes to the files
3. Print a summary of the changes made
"""

import os
import re
import shutil
import datetime
from pathlib import Path

# Define the files to modify
FILES_TO_MODIFY = {
    "app/services/research_generator/serp_api_service.py": "SERP API Service",
    "research_pack/ResearchPackOrchestrator.py": "Research Pack Orchestrator",
    "app/services/research_generator/content_extractor.py": "Content Extractor"
}

# Base directory
BASE_DIR = "/home/admin/projects/lily_ai"

def create_backup(file_path):
    """Create a backup of the file."""
    timestamp = datetime.datetime.now().strftime("%Y%m%d%H%M%S")
    backup_path = f"{file_path}.bak.{timestamp}"
    shutil.copy2(file_path, backup_path)
    return backup_path

def fix_serp_api_service(file_path):
    """Apply fixes to the SERP API Service file."""
    with open(file_path, 'r') as f:
        content = f.read()
    
    # Find the extract_academic_sources method
    extract_method_pattern = r"async def extract_academic_sources\(self, results: Dict\) -> List\[Dict\]:(.*?)(?=\n    async def|\n\n# Example usage|\Z)"
    extract_method_match = re.search(extract_method_pattern, content, re.DOTALL)
    
    if not extract_method_match:
        print("❌ Could not find extract_academic_sources method in SERP API Service")
        return False
    
    # Replace the extract_academic_sources method with the fixed version
    fixed_extract_method = """
    async def extract_academic_sources(self, results: Dict) -> List[Dict]:
        \"\"\"
        Extract academic sources from search results.

        Args:
            results: Dictionary mapping engine names to search results or direct SERP API response

        Returns:
            List of academic sources with metadata
        \"\"\"
        try:
            academic_sources = []

            # Save the raw response for debugging
            with open('/tmp/serp_response.json', 'w') as f:
                json.dump(results, f, indent=2)

            # Log the structure of the results for debugging
            logger.info(f"Results type: {type(results)}")
            if isinstance(results, dict):
                logger.info(f"Results keys: {list(results.keys())}")
                
            # Case 1: Direct SERP API response with organic_results at the top level
            if isinstance(results, dict) and "organic_results" in results:
                logger.info(f"Processing direct SERP API response with {len(results.get('organic_results', []))} results")
                for result in results.get("organic_results", []):
                    # Extract source information
                    source = self._extract_source_from_result(result)
                    if source:
                        academic_sources.append(source)
                        
            # Case 2: Nested structure with engine names as keys
            elif isinstance(results, dict):
                # Process each engine's results
                for engine, engine_results in results.items():
                    if isinstance(engine_results, dict) and "organic_results" in engine_results:
                        logger.info(f"Processing {engine} results with {len(engine_results.get('organic_results', []))} items")
                        for result in engine_results.get("organic_results", []):
                            source = self._extract_source_from_result(result)
                            if source:
                                academic_sources.append(source)
                    elif isinstance(engine_results, list):
                        logger.info(f"Processing {engine} results list with {len(engine_results)} items")
                        for result in engine_results:
                            source = self._extract_source_from_result(result)
                            if source:
                                academic_sources.append(source)

            logger.info(f"Extracted {len(academic_sources)} academic sources")
            return academic_sources

        except Exception as e:
            logger.error(f"Error extracting academic sources: {str(e)}")
            return []

    def _extract_source_from_result(self, result: Dict) -> Optional[Dict]:
        \"\"\"
        Extract source information from a single result.
        
        Args:
            result: A single result from the SERP API
            
        Returns:
            Source dictionary or None if not a valid source
        \"\"\"
        try:
            # Skip if no title or link
            if not result.get("title") or not (result.get("link") or result.get("url")):
                return None
                
            # Extract basic information
            title = result.get("title", "")
            link = result.get("link", result.get("url", ""))
            snippet = result.get("snippet", "")

            # Extract authors and publication info
            authors = []
            publication_year = ""
            publication_venue = ""

            # Extract publication info if available
            publication_info = result.get("publication_info", {})
            if publication_info:
                # Extract authors
                if "authors" in publication_info and isinstance(publication_info["authors"], list):
                    authors = [author.get("name", "") for author in publication_info["authors"] if "name" in author]

                # Extract year and venue from summary
                summary = publication_info.get("summary", "")
                if summary:
                    import re
                    year_match = re.search(r'\\b(19|20)\\d{2}\\b', summary)
                    if year_match:
                        publication_year = year_match.group(0)

                    # Extract publication venue
                    if " - " in summary and "," in summary:
                        try:
                            venue_part = summary.split(" - ")[1].split(",")[0].strip()
                            if venue_part:
                                publication_venue = venue_part
                        except:
                            pass

            # Extract citation count if available
            citations = 0
            if "inline_links" in result and "cited_by" in result["inline_links"]:
                citations = result["inline_links"]["cited_by"].get("total", 0)

            # Create source object
            source = {
                "title": title,
                "link": link,
                "url": link,  # Add url field for compatibility
                "snippet": snippet,
                "source_type": "academic_paper",
                "authors": authors,
                "publication_year": publication_year,
                "year": publication_year,  # Add year field for compatibility
                "publication_venue": publication_venue,
                "citations": citations
            }
            return source
            
        except Exception as e:
            logger.error(f"Error extracting source from result: {str(e)}")
            return None
    """
    
    # Replace the method
    new_content = re.sub(extract_method_pattern, fixed_extract_method, content, flags=re.DOTALL)
    
    # Add Optional to imports if not already there
    if "Optional" not in new_content:
        new_content = re.sub(
            r"from typing import (.*?)\n",
            r"from typing import \1, Optional\n",
            new_content
        )
    
    with open(file_path, 'w') as f:
        f.write(new_content)
    
    return True

def fix_research_pack_orchestrator(file_path):
    """Apply fixes to the Research Pack Orchestrator file."""
    with open(file_path, 'r') as f:
        content = f.read()
    
    # Find the research context section in _generate_content
    research_context_pattern = r'(if research_context:.*?content_prompt \+= f""".*?Sources:.*?{json\.dumps\(\[{.*?"year": source\.get\("year", ""\),.*?} for source in research_context\["sources"\]\[:10\]\], indent=2\)})'
    research_context_match = re.search(research_context_pattern, content, re.DOTALL)
    
    if not research_context_match:
        print("❌ Could not find research context section in Research Pack Orchestrator")
        return False
    
    # Replace the year field with publication_year
    fixed_research_context = research_context_match.group(1).replace(
        '"year": source.get("year", "")',
        '"year": source.get("publication_year", "")'
    )
    
    # Replace the section
    new_content = content.replace(research_context_match.group(1), fixed_research_context)
    
    with open(file_path, 'w') as f:
        f.write(new_content)
    
    return True

def fix_content_extractor(file_path):
    """Apply fixes to the Content Extractor file."""
    with open(file_path, 'r') as f:
        content = f.read()
    
    # Find the process_source_batch method
    process_batch_pattern = r"async def process_source_batch\(self, sources: List\[Dict\], session_id: str = None\) -> List\[Dict\]:(.*?)(?=\n    async def|\n    def|\Z)"
    process_batch_match = re.search(process_batch_pattern, content, re.DOTALL)
    
    if not process_batch_match:
        print("❌ Could not find process_source_batch method in Content Extractor")
        return False
    
    # Find the part where URL is added to the source
    url_addition_pattern = r"(if \"url\" not in source:.*?source\[\"url\"\] = url)"
    url_addition_match = re.search(url_addition_pattern, process_batch_match.group(1), re.DOTALL)
    
    if not url_addition_match:
        # If not found, we'll add the code to add both url and link fields
        new_process_batch = process_batch_match.group(1).replace(
            "# Add the URL to the source if it doesn't have one\n                if \"url\" not in source:\n                    source[\"url\"] = url",
            "# Add both url and link fields for compatibility\n                source[\"url\"] = url\n                source[\"link\"] = url"
        )
    else:
        # Replace the existing code
        new_process_batch = process_batch_match.group(1).replace(
            url_addition_match.group(1),
            "# Add both url and link fields for compatibility\n                source[\"url\"] = url\n                source[\"link\"] = url"
        )
    
    # Replace the method
    new_content = re.sub(process_batch_pattern, f"async def process_source_batch(self, sources: List[Dict], session_id: str = None) -> List[Dict]:{new_process_batch}", content, flags=re.DOTALL)
    
    with open(file_path, 'w') as f:
        f.write(new_content)
    
    return True

def main():
    """Apply all fixes."""
    print("🔧 Applying fixes to SERP API integration issues...\n")
    
    # Create backups
    backups = {}
    for file_rel_path, file_desc in FILES_TO_MODIFY.items():
        file_path = os.path.join(BASE_DIR, file_rel_path)
        if os.path.exists(file_path):
            backup_path = create_backup(file_path)
            backups[file_rel_path] = backup_path
            print(f"✅ Created backup of {file_desc}: {backup_path}")
        else:
            print(f"❌ File not found: {file_path}")
    
    print("\n🔧 Applying fixes...\n")
    
    # Apply fixes
    results = {}
    
    # Fix SERP API Service
    serp_api_path = os.path.join(BASE_DIR, "app/services/research_generator/serp_api_service.py")
    if os.path.exists(serp_api_path):
        results["SERP API Service"] = fix_serp_api_service(serp_api_path)
        if results["SERP API Service"]:
            print(f"✅ Fixed SERP API Service")
        else:
            print(f"❌ Failed to fix SERP API Service")
    
    # Fix Research Pack Orchestrator
    orchestrator_path = os.path.join(BASE_DIR, "research_pack/ResearchPackOrchestrator.py")
    if os.path.exists(orchestrator_path):
        results["Research Pack Orchestrator"] = fix_research_pack_orchestrator(orchestrator_path)
        if results["Research Pack Orchestrator"]:
            print(f"✅ Fixed Research Pack Orchestrator")
        else:
            print(f"❌ Failed to fix Research Pack Orchestrator")
    
    # Fix Content Extractor
    extractor_path = os.path.join(BASE_DIR, "app/services/research_generator/content_extractor.py")
    if os.path.exists(extractor_path):
        results["Content Extractor"] = fix_content_extractor(extractor_path)
        if results["Content Extractor"]:
            print(f"✅ Fixed Content Extractor")
        else:
            print(f"❌ Failed to fix Content Extractor")
    
    # Print summary
    print("\n📋 Summary:")
    for file_desc, success in results.items():
        if success:
            print(f"✅ {file_desc}: Fixed successfully")
        else:
            print(f"❌ {file_desc}: Fix failed")
    
    print("\n🔍 Next steps:")
    print("1. Restart the server: cd /home/admin/projects/lily_ai && python run.py")
    print("2. Submit a test job and monitor the logs")
    print("3. Verify that academic sources are being extracted correctly")
    print("4. Check that the generated document includes proper citations")
    
    # Print rollback instructions
    print("\n⚠️ If issues arise, you can restore the backups:")
    for file_rel_path, backup_path in backups.items():
        file_path = os.path.join(BASE_DIR, file_rel_path)
        print(f"cp {backup_path} {file_path}")

if __name__ == "__main__":
    main()
