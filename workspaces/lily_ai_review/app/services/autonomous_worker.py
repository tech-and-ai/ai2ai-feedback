"""
Autonomous Worker for Lily AI

This module provides an autonomous worker that can process code files,
generate documentation, and store it in the database.
"""
import os
import json
import glob
import logging
import sys
import time
from pathlib import Path
import subprocess
from typing import Dict, List, Any, Optional, Union

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("autonomous_worker.log"),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger("autonomous_worker")

# Fix imports by adding the project root to sys.path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))
sys.path.insert(0, project_root)

# Now we can import the OllamaService
try:
    from app.services.ollama_service import OllamaService
except ImportError:
    # Define a local version for standalone operation
    logger.warning("Could not import OllamaService, using local implementation")
    
    class OllamaService:
        """
        Local implementation of OllamaService for standalone operation.
        """
        def __init__(self, base_url: str = "http://localhost:11434"):
            """
            Initialize the Ollama service.

            Args:
                base_url: Base URL for the Ollama API
            """
            self.base_url = base_url
            logger.info(f"Ollama service initialized with base URL: {base_url}")

        def generate(self,
                    model: str,
                    prompt: str,
                    system: Optional[str] = None,
                    temperature: float = 0.7,
                    max_tokens: int = 2000) -> Dict[str, Any]:
            """Mock implementation of generate"""
            logger.info(f"Mock generate called with model: {model}")
            return {"response": "Generated documentation would appear here in online mode."}

        def analyze_code(self,
                        model: str,
                        code: str,
                        language: Optional[str] = None,
                        task: str = "document") -> Dict[str, Any]:
            """Mock implementation of analyze_code"""
            logger.info(f"Mock analyze_code called with model: {model}, language: {language}")
            result = f"# Documentation for code\n\n"
            result += "## 1. Purpose and Overview\n\n"
            result += "This code appears to be a Python script that performs various functions.\n\n"
            
            # Extract simple information about the code
            if "class " in code:
                result += "The code contains class definitions.\n\n"
            if "def " in code:
                result += "The code contains function definitions.\n\n"
            if "import " in code:
                result += "The code imports other modules.\n\n"
                
            result += "## 2. Components\n\n"
            
            # Extract some basic components
            for line in code.split("\n"):
                line = line.strip()
                if line.startswith("class "):
                    class_name = line[6:].split("(")[0].strip()
                    result += f"### {class_name} (class)\n\n"
                    result += f"A class defined in the code.\n\n"
                elif line.startswith("def "):
                    func_name = line[4:].split("(")[0].strip()
                    result += f"### {func_name} (function)\n\n"
                    result += f"A function defined in the code.\n\n"
                    
            result += "## 3. Dependencies and Relationships\n\n"
            result += "No detailed analysis available in offline mode.\n\n"
            
            result += "## 4. Usage Examples\n\n"
            result += "Examples cannot be generated in offline mode.\n\n"
            
            result += "## 5. Additional Notes\n\n"
            result += "This documentation was generated in offline mode with limited analysis capabilities.\n"
            
            return {"result": result}

class AutonomousWorker:
    """
    Autonomous worker for code documentation and analysis.
    """
    def __init__(self, config_path: str = "config.json"):
        """
        Initialize the autonomous worker.

        Args:
            config_path: Path to the configuration file
        """
        self.config = self._load_config(config_path)
        self.inbound_dir = os.path.join(os.path.dirname(__file__), "../../agent_worker/inbound")
        self.outbound_dir = os.path.join(os.path.dirname(__file__), "../../agent_worker/outbound")
        self.processed_files = []
        self.context_entries = []
        self.relationships = []

        # Initialize AI service (Ollama)
        if "ai_providers" in self.config:
            providers = self.config["ai_providers"]
            default_provider = self.config.get("default_provider", "ollama")

            if default_provider == "ollama" and "ollama" in providers and providers["ollama"]["enabled"]:
                # Initialize Ollama service
                ollama_config = providers["ollama"]
                base_url = ollama_config.get("base_url", "http://localhost:11434")
                model = ollama_config.get("model", "gemma3:4b")

                self.ai_service = OllamaService(base_url=base_url)
                self.ai_model = model
                self.ai_temperature = ollama_config.get("temperature", 0.2)
                self.ai_max_tokens = ollama_config.get("max_tokens", 4000)
                logger.info(f"Using Ollama service with model: {self.ai_model} at {base_url}")
            elif default_provider == "openrouter" and "openrouter" in providers and providers["openrouter"]["enabled"]:
                # Initialize OpenRouter service (using the OllamaService as a placeholder)
                openrouter_config = providers["openrouter"]
                base_url = openrouter_config.get("base_url", "https://openrouter.ai/api/v1")
                model = openrouter_config.get("model", "google/gemini-flash-2.5")

                self.ai_service = OllamaService(base_url=base_url)  # Using OllamaService as a placeholder
                self.ai_model = model
                self.ai_temperature = openrouter_config.get("temperature", 0.3)
                self.ai_max_tokens = openrouter_config.get("max_tokens", 8000)
                logger.info(f"Using OpenRouter service with model: {self.ai_model}")
            else:
                logger.warning(f"Default AI provider '{default_provider}' not configured or disabled")
                self.ai_service = OllamaService(base_url="http://localhost:11434")
                self.ai_model = "mock-model"
                self.ai_temperature = 0.2
                self.ai_max_tokens = 4000
                logger.info("Using fallback OllamaService for offline operation")
        elif "ollama" in self.config:
            # Legacy support for older config format
            ollama_config = self.config["ollama"]
            self.ai_service = OllamaService(base_url=ollama_config.get("base_url", "http://localhost:11434"))
            self.ai_model = ollama_config.get("model", "gemma3:4b")
            self.ai_temperature = ollama_config.get("temperature", 0.2)
            self.ai_max_tokens = ollama_config.get("max_tokens", 4000)
            logger.info(f"Using Ollama service with model: {self.ai_model} (legacy config)")
        else:
            # Fallback to local implementation
            self.ai_service = OllamaService(base_url="http://localhost:11434")
            self.ai_model = "mock-model"
            self.ai_temperature = 0.2
            self.ai_max_tokens = 4000
            logger.info("Using fallback OllamaService for offline operation")

        # Ensure directories exist
        os.makedirs(self.inbound_dir, exist_ok=True)
        os.makedirs(self.outbound_dir, exist_ok=True)

        logger.info("Autonomous worker initialized")
        logger.info(f"Inbound directory: {self.inbound_dir}")
        logger.info(f"Outbound directory: {self.outbound_dir}")
        
    def _load_config(self, config_path: str) -> Dict[str, Any]:
        """
        Load the configuration file.

        Args:
            config_path: Path to the configuration file

        Returns:
            The configuration as a dictionary
        """
        try:
            config_path = os.path.join(os.path.dirname(__file__), "../../agent_worker", config_path)
            with open(config_path, 'r') as f:
                config = json.load(f)
            logger.info(f"Configuration loaded from {config_path}")
            return config
        except Exception as e:
            logger.error(f"Error loading configuration: {str(e)}")
            # Create default config
            return {
                "include_patterns": ["*.py", "*.js", "*.ts", "*.html", "*.css"],
                "exclude_patterns": ["node_modules", "__pycache__", "*.pyc", "*.map"],
                "ai_providers": {
                    "ollama": {
                        "enabled": True,
                        "base_url": "http://localhost:11434",
                        "model": "gemma3:4b"
                    }
                }
            }

    def scan_inbound_folder(self) -> List[str]:
        """
        Scan the inbound folder for files to process.

        Returns:
            List of file paths to process
        """
        files_to_process = []

        # Use os.walk to recursively scan the inbound directory
        for root, _, files in os.walk(self.inbound_dir):
            for file in files:
                file_path = os.path.join(root, file)
                file_extension = os.path.splitext(file)[1]
                
                # Check if file matches include patterns
                should_include = False
                for pattern in self.config["include_patterns"]:
                    # Convert glob pattern to extension check
                    if pattern.startswith("*.") and file_extension == pattern[1:]:
                        should_include = True
                        break
                
                # Check if file matches exclude patterns
                should_exclude = False
                if should_include:
                    for exclude in self.config["exclude_patterns"]:
                        if exclude in file_path:
                            should_exclude = True
                            break
                
                # Add file to processing list if it passes all checks
                if should_include and not should_exclude:
                    files_to_process.append(file_path)

        logger.info(f"Found {len(files_to_process)} files to process in {self.inbound_dir}")
        for file_path in files_to_process:
            logger.info(f"  Will process: {file_path}")
            
        return files_to_process

    def process_file(self, file_path: str) -> Dict[str, Any]:
        """
        Process a single file, extracting key information.

        Args:
            file_path: Path to the file

        Returns:
            Dictionary with file information
        """
        try:
            # Extract file information
            file_name = os.path.basename(file_path)
            extension = os.path.splitext(file_name)[1]
            
            # Read file content
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
                
            # Create file info dictionary
            file_info = {
                "path": file_path,
                "name": file_name,
                "extension": extension,
                "content": content,
                "size": len(content),
                "last_modified": os.path.getmtime(file_path),
                "created": os.path.getctime(file_path)
            }
            
            logger.info(f"Processed file: {file_path}")
            return file_info
        except Exception as e:
            logger.error(f"Error processing file {file_path}: {str(e)}")
            return {
                "path": file_path,
                "error": str(e)
            }

    def analyze_code(self, file_info: Dict[str, Any]) -> Dict[str, Any]:
        """
        Analyze code from a source file, enriching the file_info dictionary
        with additional information.

        Args:
            file_info: Dictionary containing file information, including source code

        Returns:
            Enriched dictionary with analysis results
        """
        try:
            filename = file_info.get("path", "unknown")
            extension = file_info.get("extension", "")
            source = file_info.get("source", "")
            
            logger.info(f"Analyzing {os.path.basename(filename)} ({extension})")
            
            # Initialize analysis results
            analysis_results = {}
            
            # Always include the path and filename in the results
            analysis_results["path"] = filename
            analysis_results["filename"] = os.path.basename(filename)
            
            # Run language-specific analysis
            if extension == ".py":
                language_analysis = self._analyze_python_file(file_info["content"], filename)
                analysis_results.update(language_analysis)
            elif extension in [".js", ".ts", ".jsx", ".tsx"]:
                language_analysis = self._analyze_javascript_file(file_info["content"], filename)
                analysis_results.update(language_analysis)
            elif extension == ".html":
                language_analysis = self._analyze_html_file(file_info["content"], filename)
                analysis_results.update(language_analysis)
            elif extension == ".css":
                language_analysis = self._analyze_css_file(file_info["content"], filename)
                analysis_results.update(language_analysis)
            else:
                # For other file types, create a generic file component
                analysis_results["components"] = [{
                    "type": "file",
                    "name": os.path.basename(filename),
                    "file": filename,
                    "description": f"File with extension {extension}"
                }]

            # Then, if AI service is available, enhance the analysis with AI
            if self.ai_service:
                try:
                    # Determine the language based on extension
                    language = None
                    if extension == ".py":
                        language = "python"
                    elif extension in [".js", ".jsx"]:
                        language = "javascript"
                    elif extension in [".ts", ".tsx"]:
                        language = "typescript"
                    elif extension == ".html":
                        language = "html"
                    elif extension == ".css":
                        language = "css"
                    else:
                        language = "unknown"

                    logger.info(f"Using AI to analyze {filename} (language: {language})")

                    # Check if file is too large and needs chunking
                    content = file_info["content"]
                    max_chunk_tokens = 3500  # Approximate max tokens per chunk
                    
                    if len(content) > max_chunk_tokens * 4:  # Rough approximation of token count
                        # File is large, chunk it
                        logger.info(f"File is large, chunking for analysis: {len(content)} characters")
                        chunked_analysis = self._analyze_large_file(content, language, filename)
                        analysis_results["ai_summary"] = chunked_analysis
                    else:
                        # Use AI to analyze the full code in one go
                        ai_analysis = self.ai_service.analyze_code(
                            model=self.ai_model,
                            code=content,
                            language=language,
                            task="document"
                        )

                        # Extract AI-generated documentation
                        if "result" in ai_analysis and ai_analysis["result"]:
                            # Add AI-generated summary
                            analysis_results["ai_summary"] = ai_analysis["result"]

                    # Extract purpose from AI summary if available
                    purpose = self._extract_purpose_from_ai_summary(analysis_results.get("ai_summary", ""))
                    if purpose:
                        analysis_results["purpose"] = purpose
                    
                    # Make sure components exist before enhancing
                    if "components" not in analysis_results:
                        analysis_results["components"] = []
                    
                    # Try to match AI descriptions with components
                    self._enhance_components_with_ai(analysis_results["components"], analysis_results.get("ai_summary", ""))
                    
                    # Try to extract additional components that basic analysis might have missed
                    additional_components = self._extract_additional_components(analysis_results.get("ai_summary", ""), filename)
                    if additional_components:
                        analysis_results["components"].extend(additional_components)
                        
                    # Add section-based documentation
                    analysis_results["documentation_sections"] = self._extract_sections_from_ai_summary(analysis_results.get("ai_summary", ""))

                    logger.info(f"Enhanced analysis of {filename} with AI")
                except Exception as e:
                    logger.error(f"Error using AI to analyze {filename}: {str(e)}")
                    import traceback
                    logger.error(traceback.format_exc())

            return analysis_results
        except Exception as e:
            logger.error(f"Error analyzing code: {str(e)}")
            return {"path": filename, "error": str(e)}

    def _analyze_python_file(self, content: str, filename: str) -> Dict[str, Any]:
        """
        Analyze a Python file.

        Args:
            content: Content of the file
            filename: Name of the file

        Returns:
            Dictionary with analysis results
        """
        # This is a simplified implementation
        # In a real implementation, you would use the ast module to parse the Python code

        components = []
        relationships = []
        imports = set()

        # Extract classes with a more robust approach
        lines = content.split("\n")
        i = 0
        while i < len(lines):
            line = lines[i].strip()
            
            # Extract classes
            if line.startswith("class "):
                class_def = line
                
                # Check for multiline class definition
                j = i + 1
                while j < len(lines) and ":" not in class_def:
                    class_def += " " + lines[j].strip()
                    j += 1
                
                # Parse class name and inheritance
                try:
                    class_name = class_def.split("class ")[1].split("(")[0].strip()
                    components.append({
                        "type": "class",
                        "name": class_name,
                        "file": filename
                    })
                    
                    # Extract inheritance relationships
                    if "(" in class_def and not class_def.split("(")[1].split(")")[0].strip() == "":
                        parent_classes = class_def.split("(")[1].split(")")[0].split(",")
                        for parent in parent_classes:
                            parent = parent.strip()
                            if parent and parent != "object":
                                relationships.append({
                                    "type": "inherits",
                                    "source": class_name,
                                    "target": parent
                                })
                except Exception as e:
                    logger.error(f"Error parsing class definition: {class_def}, {str(e)}")
            
            # Extract functions and methods with docstrings
            elif line.startswith("def "):
                func_name = line.split("def ")[1].split("(")[0].strip()
                
                # Determine if this is a method or a function
                if i > 0 and (lines[i-1].strip().startswith("class ") or 
                              lines[i-1].strip().startswith("    ") or
                              lines[i-1].strip().startswith("\t")):
                    comp_type = "method"
                    # Extract the class it belongs to, if possible
                    class_indent = 0
                    for j in range(i-1, -1, -1):
                        if lines[j].strip().startswith("class "):
                            try:
                                class_name = lines[j].strip().split("class ")[1].split("(")[0].strip()
                                relationships.append({
                                    "type": "defines",
                                    "source": class_name,
                                    "target": func_name
                                })
                                break
                            except:
                                pass
                else:
                    comp_type = "function"
                
                components.append({
                    "type": comp_type,
                    "name": func_name,
                    "file": filename
                })
                
                # Extract docstring if available
                docstring = ""
                j = i + 1
                doc_start = False
                while j < len(lines) and j < i + 20:  # Look for docstring within next 20 lines
                    if '"""' in lines[j] or "'''" in lines[j]:
                        if not doc_start:
                            doc_start = True
                            docstring += lines[j].strip().replace('"""', '').replace("'''", '')
                            # If the docstring ends on the same line
                            if lines[j].strip().endswith('"""') or lines[j].strip().endswith("'''"):
                                break
                        else:
                            docstring += " " + lines[j].strip().replace('"""', '').replace("'''", '')
                            break
                    elif doc_start:
                        docstring += " " + lines[j].strip()
                    j += 1
                
                if docstring:
                    for comp in components:
                        if comp["name"] == func_name:
                            comp["description"] = docstring.strip()
            
            # Extract imports
            elif line.startswith("import ") or line.startswith("from "):
                if line.startswith("import "):
                    for module in line[7:].split(","):
                        module_name = module.strip().split(" as ")[0].strip()
                        if module_name:
                            imports.add(module_name)
                            relationships.append({
                                "type": "imports",
                                "source": filename,
                                "target": module_name
                            })
                elif line.startswith("from "):
                    parts = line.split("import")
                    if len(parts) > 1:
                        module_name = parts[0][5:].strip()
                        if module_name:
                            imports.add(module_name)
                            relationships.append({
                                "type": "imports",
                                "source": filename,
                                "target": module_name
                            })
                            
                            # Also track what's being imported from the module
                            for item in parts[1].split(","):
                                item_name = item.strip().split(" as ")[0].strip()
                                if item_name and item_name != "*":
                                    full_name = f"{module_name}.{item_name}"
                                    relationships.append({
                                        "type": "imports",
                                        "source": filename,
                                        "target": full_name
                                    })
            
            i += 1

        # Look for function calls and object instantiations
        for i, line in enumerate(lines):
            # Look for function calls
            for component in components:
                if component["type"] in ["function", "method"] and component["name"] in line:
                    # Skip the function definition line
                    if f"def {component['name']}" not in line:
                        # Find what's calling this function
                        for caller in components:
                            if caller["type"] in ["function", "method", "class"] and caller != component:
                                # Check if this is within the caller's definition
                                in_caller = False
                                j = i - 1
                                while j >= 0:
                                    if lines[j].strip().startswith(f"def {caller['name']}") or lines[j].strip().startswith(f"class {caller['name']}"):
                                        in_caller = True
                                        break
                                    j -= 1
                                
                                if in_caller:
                                    relationships.append({
                                        "type": "calls",
                                        "source": caller["name"],
                                        "target": component["name"]
                                    })
                                    break
            
            # Look for object instantiations
            for component in components:
                if component["type"] == "class" and f"{component['name']}(" in line:
                    # Find what's creating this object
                    for caller in components:
                        if caller["type"] in ["function", "method", "class"] and caller != component:
                            # Check if this is within the caller's definition
                            in_caller = False
                            j = i - 1
                            while j >= 0:
                                if lines[j].strip().startswith(f"def {caller['name']}") or lines[j].strip().startswith(f"class {caller['name']}"):
                                    in_caller = True
                                    break
                                j -= 1
                            
                            if in_caller:
                                relationships.append({
                                    "type": "creates",
                                    "source": caller["name"],
                                    "target": component["name"]
                                })
                                break

        # Generate summary
        summary = f"Python file {filename} contains {len(components)} components and {len(relationships)} relationships."

        return {
            "components": components,
            "relationships": relationships,
            "summary": summary,
            "imports": list(imports)
        }

    def _analyze_javascript_file(self, content: str, filename: str) -> Dict[str, Any]:
        """
        Analyze a JavaScript/TypeScript file.

        Args:
            content: Content of the file
            filename: Name of the file

        Returns:
            Dictionary with analysis results
        """
        # Simplified implementation with enhancements
        components = []
        relationships = []
        imports = set()
        
        # Split by lines for analysis
        lines = content.split("\n")

        # Extract components and relationships
        i = 0
        while i < len(lines):
            line = lines[i].strip()
            
            # Look for class definitions
            if (line.startswith("class ") or 
                line.startswith("export class ") or 
                line.startswith("export default class ")):
                
                # Get the class name
                class_parts = line.split("class ")[1].split("{")[0].split("extends")
                class_name = class_parts[0].strip()
                
                components.append({
                    "type": "class",
                    "name": class_name,
                    "file": filename
                })
                
                # Check for inheritance
                if len(class_parts) > 1:
                    parent_class = class_parts[1].strip()
                    relationships.append({
                        "type": "extends",
                        "source": class_name,
                        "target": parent_class
                    })
            
            # Look for function definitions
            elif (("function " in line and line.startswith("function ")) or 
                  line.startswith("export function ") or
                  line.startswith("export default function ")):
                
                function_name = line.split("function ")[1].split("(")[0].strip()
                components.append({
                    "type": "function",
                    "name": function_name,
                    "file": filename
                })
            
            # Look for arrow function components (like React components)
            elif (" = (" in line or " => {" in line) and (
                  line.startswith("const ") or 
                  line.startswith("let ") or 
                  line.startswith("var ") or
                  line.startswith("export const ") or
                  line.startswith("export default const ")):
                
                # Handle component definitions like "const MyComponent = () => {" or "export const MyComponent = ({ prop }) => {"
                if " = (" in line:
                    component_name = line.split(" = (")[0].split("const ").pop().split("let ").pop().split("var ").pop().strip()
                else:
                    component_name = line.split(" => {")[0].split("=>").pop().strip()
                
                component_name = component_name.replace("export ", "").replace("default ", "").replace("const ", "").replace("let ", "").replace("var ", "").strip()
                
                # Check if this is likely a React component (uppercase first letter is a convention)
                if component_name and component_name[0].isupper():
                    components.append({
                        "type": "component",
                        "name": component_name,
                        "file": filename
                    })
                else:
                    components.append({
                        "type": "function",
                        "name": component_name,
                        "file": filename
                    })
            
            # Look for imports
            elif line.startswith("import "):
                if "from " in line:
                    module_name = line.split("from ")[1].replace(";", "").replace("'", "").replace('"', '').strip()
                    imports.add(module_name)
                    relationships.append({
                        "type": "imports",
                        "source": filename,
                        "target": module_name
                    })
                    
                    # Try to extract what's being imported
                    if "{" in line and "}" in line:
                        imported_parts = line.split("{")[1].split("}")[0].split(",")
                        for part in imported_parts:
                            item_name = part.strip().split(" as ")[0].strip()
                            if item_name:
                                relationships.append({
                                    "type": "imports",
                                    "source": filename,
                                    "target": f"{module_name}.{item_name}"
                                })
            
            # Look for require statements
            elif "require(" in line:
                if "=" in line and "require(" in line.split("=")[1]:
                    module_name = line.split("require(")[1].split(")")[0].replace("'", "").replace('"', '').strip()
                    imports.add(module_name)
                    relationships.append({
                        "type": "imports",
                        "source": filename,
                        "target": module_name
                    })
            
            i += 1
        
        # Look for component usage (for React components)
        for component in components:
            if component["type"] == "component":
                # Check if the component is used in JSX
                for line in lines:
                    if f"<{component['name']}" in line:
                        # Try to determine which component is using this component
                        for using_component in components:
                            if using_component != component and using_component["type"] == "component":
                                # Simplistic approach - check if this line appears after the definition of the using component
                                # A more robust approach would use an AST parser
                                if lines.index(line) > lines.index(f"const {using_component['name']} = "):
                                    relationships.append({
                                        "type": "uses",
                                        "source": using_component["name"],
                                        "target": component["name"]
                                    })
                                    break

        # Generate summary
        summary = f"JavaScript/TypeScript file {filename} contains {len(components)} components and {len(relationships)} relationships."

        return {
            "components": components,
            "relationships": relationships,
            "summary": summary,
            "imports": list(imports)
        }

    def _analyze_html_file(self, content: str, filename: str) -> Dict[str, Any]:
        """
        Analyze an HTML file.

        Args:
            content: Content of the file
            filename: Name of the file

        Returns:
            Dictionary with analysis results
        """
        # Simplified implementation
        components = []
        relationships = []

        # Extract components (simplified)
        components.append({
            "type": "html_document",
            "name": filename,
            "file": filename
        })

        # Extract relationships (e.g., CSS and JS includes)
        link_lines = [line for line in content.split("\n") if "<link" in line]
        for line in link_lines:
            if "href=" in line:
                href = line.split("href=")[1].split('"')[1]
                relationships.append({
                    "type": "includes",
                    "source": filename,
                    "target": href
                })

        script_lines = [line for line in content.split("\n") if "<script" in line]
        for line in script_lines:
            if "src=" in line:
                src = line.split("src=")[1].split('"')[1]
                relationships.append({
                    "type": "includes",
                    "source": filename,
                    "target": src
                })

        # Generate summary
        summary = f"HTML file {filename} contains {len(components)} components and {len(relationships)} relationships."

        return {
            "components": components,
            "relationships": relationships,
            "summary": summary
        }

    def _analyze_css_file(self, content: str, filename: str) -> Dict[str, Any]:
        """
        Analyze a CSS file.

        Args:
            content: Content of the file
            filename: Name of the file

        Returns:
            Dictionary with analysis results
        """
        # Simplified implementation
        components = []
        relationships = []

        # Extract selectors (simplified)
        selector_lines = [line for line in content.split("\n") if "{" in line]
        for line in selector_lines:
            selector = line.split("{")[0].strip()
            if selector:
                components.append({
                    "type": "css_selector",
                    "name": selector,
                    "file": filename
                })

        # Generate summary
        summary = f"CSS file {filename} contains {len(components)} selectors."

        return {
            "components": components,
            "relationships": relationships,
            "summary": summary
        }

    def _extract_purpose_from_ai_summary(self, ai_summary: str) -> Optional[str]:
        """
        Extract the purpose from an AI-generated summary.
        
        Args:
            ai_summary: AI-generated summary
            
        Returns:
            Extracted purpose or None
        """
        try:
            # Look for purpose section
            if "## 1. Purpose and Overview" in ai_summary:
                sections = ai_summary.split("##")
                for section in sections:
                    if section.strip().startswith("1. Purpose and Overview"):
                        # Extract the first paragraph after the heading
                        paragraphs = section.strip().split("\n\n")
                        if len(paragraphs) > 1:
                            return paragraphs[1].strip()
            return None
        except Exception as e:
            logger.error(f"Error extracting purpose: {str(e)}")
            return None
            
    def _enhance_components_with_ai(self, components: List[Dict[str, Any]], ai_summary: str) -> None:
        """
        Enhance component information with AI-generated descriptions.
        
        Args:
            components: List of components to enhance
            ai_summary: AI-generated summary
        """
        try:
            # For each component, try to find a matching description
            for component in components:
                component_name = component["name"]
                
                # Check for component name in AI summary
                if component_name in ai_summary:
                    # Find paragraphs containing the component name
                    lines = ai_summary.split("\n")
                    component_lines = []
                    recording = False
                    
                    for line in lines:
                        if component_name in line and ("###" in line or "- " + component_name in line):
                            recording = True
                            component_lines.append(line)
                        elif recording and line.strip() and not line.startswith("###"):
                            component_lines.append(line)
                        elif recording and (line.startswith("###") or line.startswith("##")):
                            recording = False
                    
                    if component_lines:
                        component["description"] = "\n".join(component_lines).strip()
        except Exception as e:
            logger.error(f"Error enhancing components with AI: {str(e)}")
            
    def _extract_additional_components(self, ai_summary: str, filename: str) -> List[Dict[str, Any]]:
        """
        Extract additional components from an AI-generated summary.
        
        Args:
            ai_summary: AI-generated summary
            filename: Name of the file
            
        Returns:
            List of additional components
        """
        additional_components = []
        try:
            # Look for component names in the Components section
            if "## 2. Components" in ai_summary:
                components_section = ai_summary.split("## 2. Components")[1].split("##")[0]
                
                # Extract component names from headings
                lines = components_section.split("\n")
                for line in lines:
                    if line.strip().startswith("### "):
                        component_name = line.strip()[4:].strip()
                        
                        # Check if this component is already in our list
                        is_new = True
                        for component in additional_components:
                            if component["name"] == component_name:
                                is_new = False
                                break
                                
                        if is_new:
                            # Try to determine component type
                            component_type = "unknown"
                            if "class" in line.lower():
                                component_type = "class"
                            elif "function" in line.lower():
                                component_type = "function"
                            elif "method" in line.lower():
                                component_type = "method"
                                
                            # Extract description
                            description = ""
                            start_idx = components_section.find(line)
                            if start_idx >= 0:
                                end_idx = components_section.find("###", start_idx + len(line))
                                if end_idx >= 0:
                                    description = components_section[start_idx:end_idx].strip()
                                else:
                                    description = components_section[start_idx:].strip()
                            
                            additional_components.append({
                                "type": component_type,
                                "name": component_name,
                                "file": filename,
                                "description": description,
                                "source": "ai_analysis"
                            })
            
            return additional_components
        except Exception as e:
            logger.error(f"Error extracting additional components: {str(e)}")
            return []
            
    def _extract_sections_from_ai_summary(self, ai_summary: str) -> Dict[str, str]:
        """
        Extract documented sections from an AI-generated summary.
        
        Args:
            ai_summary: AI-generated summary
            
        Returns:
            Dictionary mapping section names to their content
        """
        sections = {}
        try:
            # Split by major sections
            if "##" in ai_summary:
                parts = ai_summary.split("##")
                
                for part in parts:
                    if not part.strip():
                        continue
                        
                    # Get section title
                    lines = part.strip().split("\n")
                    if lines:
                        title = lines[0].strip()
                        content = "\n".join(lines[1:]).strip()
                        
                        sections[title] = content
            
            return sections
        except Exception as e:
            logger.error(f"Error extracting sections: {str(e)}")
            return {}

    def store_documentation(self, analysis_results: List[Dict[str, Any]]):
        """
        Store the generated documentation in the output files.
        No database storage in this version.

        Args:
            analysis_results: List of analysis results for each file
        """
        # Simply log that we're skipping database storage
        logger.info("Skipping database storage - operating in standalone mode")
        # Documentation will be generated in the output files instead

    def generate_output_files(self, analysis_results: List[Dict[str, Any]]):
        """
        Generate output files in the outbound folder.

        Args:
            analysis_results: List of analysis results for each file
        """
        try:
            # Ensure outbound directory exists
            os.makedirs(self.outbound_dir, exist_ok=True)
            
            # Generate HTML documentation with chart.js - this is the only output we'll generate
            self._generate_html_documentation(analysis_results)

            logger.info("Generated output files in outbound folder")

        except Exception as e:
            logger.error(f"Error generating output files: {str(e)}")
            import traceback
            logger.error(traceback.format_exc())

    def _generate_html_documentation(self, analysis_results: List[Dict[str, Any]]):
        """
        Generate HTML documentation with Chart.js diagrams.
        
        Args:
            analysis_results: List of analysis results for each file
        """
        try:
            # Ensure outbound directory exists
            os.makedirs(self.outbound_dir, exist_ok=True)
            
            # Create an HTML file for each analyzed file
            for result in analysis_results:
                # Make sure we have a filename to work with
                if "filename" not in result and "path" not in result:
                    logger.warning("Skipping result with no filename or path")
                    continue
                    
                # Get the original filename
                if "path" in result:
                    full_path = result.get("path", "")
                    filename = os.path.basename(full_path)
                else:
                    filename = result.get("filename", "unknown")
                
                # Create HTML file with same base name
                filename_base = os.path.splitext(filename)[0]
                html_path = os.path.join(self.outbound_dir, f"{filename_base}.html")
                
                # Log the file being created for debugging
                logger.info(f"Creating HTML documentation for {filename} at {html_path}")
                
                # Extract AI summary
                ai_summary = result.get("ai_summary", "No analysis available.")
                components = result.get("components", [])
                
                # Generate HTML content
                html_content = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Documentation for {filename}</title>
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/highlight.js/11.7.0/styles/github.min.css">
    <script src="https://cdnjs.cloudflare.com/ajax/libs/highlight.js/11.7.0/highlight.min.js"></script>
    <script src="https://cdn.jsdelivr.net/npm/mermaid/dist/mermaid.min.js"></script>
    <style>
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, 'Open Sans', 'Helvetica Neue', sans-serif;
            line-height: 1.6;
            color: #333;
            max-width: 1200px;
            margin: 0 auto;
            padding: 20px;
            font-size: 14px;
        }}
        h1, h2, h3, h4 {{
            color: #2c3e50;
        }}
        h1 {{ font-size: 24px; }}
        h2 {{ font-size: 20px; }}
        h3 {{ font-size: 18px; }}
        p, li, code {{ font-size: 14px; }}
        .chart-container {{
            position: relative;
            height: 400px;
            width: 100%;
            margin: 20px 0;
        }}
        .tab {{
            overflow: hidden;
            border: 1px solid #ccc;
            background-color: #f1f1f1;
            border-radius: 4px 4px 0 0;
        }}
        .tab button {{
            background-color: inherit;
            float: left;
            border: none;
            outline: none;
            cursor: pointer;
            padding: 12px 14px;
            transition: 0.3s;
            font-size: 14px;
        }}
        .tab button:hover {{
            background-color: #ddd;
        }}
        .tab button.active {{
            background-color: #fff;
            border-bottom: 2px solid #3498db;
        }}
        .tabcontent {{
            display: none;
            padding: 20px;
            border: 1px solid #ccc;
            border-top: none;
            border-radius: 0 0 4px 4px;
            animation: fadeEffect 1s;
        }}
        pre {{
            background: #f8f9fa;
            border: 1px solid #ddd;
            border-radius: 4px;
            padding: 15px;
            overflow: auto;
            font-size: 13px;
        }}
        code {{
            font-family: Consolas, Monaco, 'Andale Mono', 'Ubuntu Mono', monospace;
            font-size: 13px;
        }}
        @keyframes fadeEffect {{
            from {{opacity: 0;}}
            to {{opacity: 1;}}
        }}
        .component-card {{
            border: 1px solid #ddd;
            border-radius: 4px;
            padding: 15px;
            margin: 10px 0;
            background-color: #fff;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }}
        .mermaid {{
            margin: 20px 0;
            background-color: #f9f9f9;
            padding: 15px;
            border-radius: 4px;
        }}
    </style>
</head>
<body>
    <h1>Documentation for {filename}</h1>
    
    <div class="tab">
        <button class="tablinks active" onclick="openTab(event, 'Overview')">Overview</button>
        <button class="tablinks" onclick="openTab(event, 'Components')">Components</button>
        <button class="tablinks" onclick="openTab(event, 'Documentation')">Full Documentation</button>
        <button class="tablinks" onclick="openTab(event, 'DataFlow')">Data Flow</button>
    </div>
    
    <div id="Overview" class="tabcontent" style="display: block;">
        <h2>File Overview</h2>
        <div class="component-card">
            {self._extract_overview_section(ai_summary)}
        </div>
    </div>
    
    <div id="Components" class="tabcontent">
        <h2>Components</h2>
        {self._generate_components_html(components)}
    </div>
    
    <div id="Documentation" class="tabcontent">
        <h2>Full Documentation</h2>
        <div class="markdown-content">
            {self._convert_markdown_to_html(ai_summary)}
        </div>
    </div>
    
    <div id="DataFlow" class="tabcontent">
        <h2>Data Flow Diagram</h2>
        <div class="mermaid">
        graph TD
            A[Input: {filename}] --> B[Parse Code]
            B --> C[Extract Components]
            C --> D[Analyze Relationships]
            D --> E[Generate Documentation]
            
            subgraph Processing Flow
            F[Raw Source] --> G[Structured Components]
            G --> H[Component Relationships]
            H --> I[HTML Documentation]
            end
            
            style A fill:#d4f1f9,stroke:#333,stroke-width:1px
            style E fill:#d5f5e3,stroke:#333,stroke-width:1px
            style I fill:#d5f5e3,stroke:#333,stroke-width:1px
        </div>
    </div>
    
    <script>
        // Tab functionality
        function openTab(evt, tabName) {{
            var i, tabcontent, tablinks;
            tabcontent = document.getElementsByClassName("tabcontent");
            for (i = 0; i < tabcontent.length; i++) {{
                tabcontent[i].style.display = "none";
            }}
            tablinks = document.getElementsByClassName("tablinks");
            for (i = 0; i < tablinks.length; i++) {{
                tablinks[i].className = tablinks[i].className.replace(" active", "");
            }}
            document.getElementById(tabName).style.display = "block";
            evt.currentTarget.className += " active";
        }}
        
        // Initialize syntax highlighting
        document.addEventListener('DOMContentLoaded', function() {{
            document.querySelectorAll('pre code').forEach((block) => {{
                hljs.highlightBlock(block);
            }});
            
            // Initialize Mermaid diagrams
            mermaid.initialize({{ startOnLoad: true }});
        }});
    </script>
</body>
</html>"""
                    
                # Write content to file
                with open(html_path, 'w') as f:
                    f.write(html_content)
                
                logger.info(f"Created HTML file at: {html_path}")
                
            logger.info("Generated HTML documentation with Chart.js diagrams")

        except Exception as e:
            logger.error(f"Error generating HTML documentation: {str(e)}")
            import traceback
            logger.error(traceback.format_exc())
            
    def _extract_overview_section(self, ai_summary: str) -> str:
        """Extract the overview section from AI summary."""
        overview = ""
        if not ai_summary:
            return "<p>No overview available.</p>"
            
        # Extract purpose/overview section from markdown
        if "## 1. PURPOSE OVERVIEW" in ai_summary:
            start = ai_summary.find("## 1. PURPOSE OVERVIEW")
            end = ai_summary.find("## 2.", start)
            if end == -1:
                end = len(ai_summary)
            overview = ai_summary[start:end].strip()
        elif "## 1. Purpose and Overview" in ai_summary:
            start = ai_summary.find("## 1. Purpose and Overview")
            end = ai_summary.find("## 2.", start)
            if end == -1:
                end = len(ai_summary)
            overview = ai_summary[start:end].strip()
            
        return self._convert_markdown_to_html(overview)
        
    def _generate_components_html(self, components: List[Dict[str, Any]]) -> str:
        """Generate HTML for components section."""
        if not components:
            return "<p>No components found.</p>"
            
        html = ""
        for component in components:
            component_type = component.get("type", "unknown")
            component_name = component.get("name", "Unnamed")
            description = component.get("description", "No description available.")
            
            html += f"""
            <div class="component-card">
                <h3>{component_name} <small>({component_type})</small></h3>
                <p>{description}</p>
            </div>
            """
            
        return html
        
    def _convert_markdown_to_html(self, markdown: str) -> str:
        """Simple markdown to HTML conversion."""
        if not markdown:
            return "<p>No content available.</p>"
            
        # Convert headers
        html = markdown.replace("# ", "<h1>").replace(" #", "</h1>")
        html = html.replace("## ", "<h2>").replace(" ##", "</h2>")
        html = html.replace("### ", "<h3>").replace(" ###", "</h3>")
        
        # Convert lists
        html = html.replace("- ", "<li>").replace("\n- ", "</li>\n<li>")
        if "<li>" in html:
            html = html.replace("<li>", "<ul>\n<li>", 1)
            html = html + "</li>\n</ul>"
            
        # Convert code blocks
        while "```" in html:
            start = html.find("```")
            end = html.find("```", start + 3)
            if end != -1:
                code_block = html[start+3:end]
                language = ""
                if "\n" in code_block:
                    language = code_block.split("\n")[0].strip()
                    if language:
                        code_block = code_block[len(language):].strip()
                html = html[:start] + f'<pre><code class="language-{language}">{code_block}</code></pre>' + html[end+3:]
            else:
                break
                
        # Convert paragraphs
        paragraphs = html.split("\n\n")
        for i, para in enumerate(paragraphs):
            if not para.startswith("<h") and not para.startswith("<ul") and not para.startswith("<pre"):
                paragraphs[i] = f"<p>{para}</p>"
        html = "\n".join(paragraphs)
        
        return html

    def _analyze_large_file(self, content: str, language: str, filename: str) -> str:
        """
        Analyze a large file by breaking it into chunks and then combining the analysis.
        
        Args:
            content: The file content
            language: The programming language
            filename: The name of the file
            
        Returns:
            Combined AI analysis
        """
        # Split the file into lines
        lines = content.split("\n")
        
        # Use fixed chunk size - 400 lines per chunk with 30 lines overlap
        lines_per_chunk = 400
        overlap_lines = 30
        
        # Initialize result
        chunks_results = []
        chunk_summaries = []
        
        # File header for context in each chunk
        file_header = f"File: {filename}\nLanguage: {language}\n\n"
        
        # Clear log message for debugging
        logger.info(f"Processing large file with {len(lines)} lines using chunk size of {lines_per_chunk} lines")
        
        # Calculate number of chunks needed
        total_chunks = (len(lines) + lines_per_chunk - overlap_lines - 1) // (lines_per_chunk - overlap_lines)
        logger.info(f"Will process file in approximately {total_chunks} chunks")
        
        # First pass: analyze each chunk
        chunk_number = 1
        for i in range(0, len(lines), lines_per_chunk - overlap_lines):
            end = min(i + lines_per_chunk, len(lines))
            chunk = "\n".join(lines[i:end])
            
            # Add context about which part of the file this is
            context = f"{file_header}This is chunk {chunk_number} of ~{total_chunks} for the file, lines {i+1}-{end}:\n\n"
            chunk_with_context = context + chunk
            
            # Log with consistent format
            logger.info(f"Analyzing chunk {chunk_number} of ~{total_chunks} (lines {i+1}-{end})")
            
            # Get analysis of this chunk
            try:
                result = self.ai_service.analyze_code(
                    model=self.ai_model,
                    code=chunk_with_context,
                    language=language,
                    task="document"
                )
                
                # Log the raw response structure to debug
                logger.info(f"Received Ollama response for chunk {chunk_number}, response keys: {list(result.keys() if result else [])}")
                
                if "result" in result and result["result"]:
                    # Log the first 100 characters of the result to verify content
                    result_sample = result["result"][:100] + "..." if len(result["result"]) > 100 else result["result"]
                    logger.info(f"Result sample for chunk {chunk_number}: {result_sample}")
                    
                    chunks_results.append(result["result"])
                    # Extract a brief summary from this chunk for the final synthesis
                    summary_prompt = f"""
Provide a 2-3 sentence summary of the key functionality and components in this code snippet:

```{language}
{chunk}
```
"""
                    summary_result = self.ai_service.generate(
                        model=self.ai_model,
                        prompt=summary_prompt,
                        temperature=0.1,
                        max_tokens=200
                    )
                    
                    # Log the summary response structure
                    logger.info(f"Received summary response for chunk {chunk_number}, response keys: {list(summary_result.keys() if summary_result else [])}")
                    
                    if "response" in summary_result:
                        # Log the first part of the summary response
                        summary_sample = summary_result["response"][:100] + "..." if len(summary_result["response"]) > 100 else summary_result["response"]
                        logger.info(f"Summary sample for chunk {chunk_number}: {summary_sample}")
                        chunk_summaries.append(summary_result["response"])
                else:
                    # Log error if no result found
                    logger.error(f"No 'result' key in response for chunk {chunk_number}: {result}")
            except Exception as e:
                logger.error(f"Error analyzing chunk {chunk_number}: {str(e)}")
                import traceback
                logger.error(traceback.format_exc())
            
            # Increment chunk number
            chunk_number += 1
        
        # Second pass: synthesize the analysis
        synthesis_prompt = f"""
I need to create a comprehensive documentation for a large file named {filename}.
The file has been analyzed in chunks, and I need you to synthesize the analysis into a cohesive documentation.

Here are brief summaries of each chunk:
"""
        
        for i, summary in enumerate(chunk_summaries):
            synthesis_prompt += f"\nChunk {i+1}:\n{summary}\n"
            
        synthesis_prompt += """
Based on these summaries, please create a comprehensive documentation that follows this structure:

## 1. PURPOSE OVERVIEW
- Main purpose of the entire file
- Problem it solves
- How it fits into the larger system

## 2. COMPONENTS
- Major classes, functions, and methods across all chunks
- For key components, include purpose, parameters, and return values

## 3. DEPENDENCIES
- External libraries/modules used throughout the file
- Internal relationships between components

## 4. USAGE EXAMPLES
- How the main functionality would be used

## 5. EDGE CASES & CONSIDERATIONS
- Performance, security, and other implications

Focus on providing a cohesive overview rather than detailed documentation of every function.
"""
        
        try:
            synthesis_result = self.ai_service.generate(
                model=self.ai_model,
                prompt=synthesis_prompt,
                temperature=0.1,
                max_tokens=2000
            )
            
            if "response" in synthesis_result:
                full_documentation = synthesis_result["response"]
                
                # Add detailed components section based on chunks
                component_details = "\n\n## DETAILED COMPONENTS\n\n"
                for i, chunk_result in enumerate(chunks_results):
                    # Extract just the components section from each chunk
                    components_section = ""
                    if "## 2. COMPONENTS" in chunk_result:
                        start = chunk_result.find("## 2. COMPONENTS")
                        end = chunk_result.find("## 3.", start)
                        if end > 0:
                            components_section = chunk_result[start:end].strip()
                            component_details += f"### Chunk {i+1} Components\n\n"
                            component_details += components_section + "\n\n"
                
                # Append the detailed components section to the full documentation
                full_documentation += "\n\n" + component_details
                
                return full_documentation
            else:
                return "Failed to synthesize analysis of large file."
        except Exception as e:
            logger.error(f"Error synthesizing analysis: {str(e)}")
            # If synthesis fails, return concatenation of individual analyses
            return "\n\n".join([f"## CHUNK {i+1}\n\n{result}" for i, result in enumerate(chunks_results)])

    def run(self):
        """
        Run the autonomous worker.
        """
        logger.info("Starting autonomous worker")

        try:
            # Step 1: Scan inbound folder
            files = self.scan_inbound_folder()
            
            if not files:
                logger.warning("No files found to process in the inbound directory")
                logger.info("Please place code files in the inbound directory and run the worker again")
                return

            # Step 2: Process and analyze files
            analysis_results = []
            for file_path in files:
                file_info = self.process_file(file_path)
                analysis = self.analyze_code(file_info)
                analysis_results.append(analysis)

            # Step 3: Skip database storage (standalone mode)
            # self.store_documentation(analysis_results)  # No-op in standalone mode

            # Step 4: Generate output files
            self.generate_output_files(analysis_results)

            logger.info("Autonomous worker completed successfully")
            logger.info(f"Generated documentation can be found in: {self.outbound_dir}")

        except Exception as e:
            logger.error(f"Error running autonomous worker: {str(e)}")
            import traceback
            logger.error(traceback.format_exc())

if __name__ == "__main__":
    worker = AutonomousWorker()
    worker.run()
