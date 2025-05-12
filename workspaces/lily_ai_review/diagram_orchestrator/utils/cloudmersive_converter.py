"""
Cloudmersive HTML to PNG conversion utility
"""

import os
import logging
import tempfile
from pathlib import Path
from dotenv import load_dotenv

# Set up logging
logger = logging.getLogger(__name__)

def html_to_png(html_content, output_path=None):
    """
    Convert HTML content to PNG using Cloudmersive API

    Args:
        html_content (str): HTML content to convert
        output_path (str, optional): Path to save the PNG file. If None, a temporary file is created.

    Returns:
        str: Path to the generated PNG file or None if conversion fails
    """
    logger.info(f"CLOUDMERSIVE DEBUG: html_to_png called, output_path={output_path}")
    try:
        # Import required libraries
        import requests
        import json

        # Load environment variables from .env file
        env_file = '/home/admin/projects/kdd/app/.env'
        load_dotenv(env_file)

        # Get API key from environment
        api_key = os.environ.get("CLOUDMERSIVE_API_KEY")
        if not api_key:
            logger.error(f"Cloudmersive API key not found in {env_file}")
            return None

        logger.info(f"CLOUDMERSIVE DEBUG: Using Cloudmersive API key: {'*' * 8}")

        # If no output path is provided, create a temporary one
        if output_path is None:
            output_dir = Path(tempfile.gettempdir())
            output_path = str(output_dir / f"diagram_{os.urandom(4).hex()}.png")

        # Create a temporary HTML file
        with tempfile.NamedTemporaryFile(suffix='.html', delete=False) as f:
            f.write(html_content.encode('utf-8'))
            temp_html_path = f.name

        try:
            # API endpoint
            url = "https://api.cloudmersive.com/convert/html/to/png"

            # Request headers
            headers = {
                "Apikey": api_key
            }

            # Make API request
            with open(temp_html_path, 'rb') as file:
                files = {
                    'inputFile': (os.path.basename(temp_html_path), file, 'text/html')
                }
                response = requests.post(url, headers=headers, files=files)

            # Check if request was successful
            if response.status_code == 200:
                try:
                    # Try to parse as JSON (Cloudmersive returns JSON with URL to download the PNG)
                    json_response = json.loads(response.content)

                    # Check if the response contains a URL to download the PNG
                    if json_response.get('Successful') and json_response.get('PngResultPages'):
                        png_url = json_response['PngResultPages'][0].get('URL')
                        if png_url:
                            # Download the PNG from the URL
                            png_response = requests.get(png_url)
                            if png_response.status_code == 200:
                                with open(output_path, 'wb') as f:
                                    f.write(png_response.content)
                                logger.info(f"Successfully downloaded PNG from Cloudmersive URL: {output_path}")
                                return output_path
                            else:
                                logger.error(f"Error downloading PNG: {png_response.status_code}")
                                return None
                        else:
                            logger.error("No PNG URL in Cloudmersive response")
                            return None
                    else:
                        logger.error(f"Unsuccessful Cloudmersive response: {json_response}")
                        return None
                except json.JSONDecodeError:
                    # Not JSON, assume it's binary data
                    with open(output_path, 'wb') as f:
                        f.write(response.content)
                    logger.info(f"Successfully converted HTML to PNG using Cloudmersive: {output_path}")
                    return output_path
            else:
                logger.error(f"Cloudmersive API error: {response.status_code}, {response.text}")
                return None

        except Exception as e:
            logger.error(f"Exception when calling Cloudmersive API: {str(e)}")
            return None
        finally:
            # Clean up temporary file
            try:
                os.unlink(temp_html_path)
            except Exception:
                pass

    except ImportError:
        logger.error("Required libraries not installed")
        return None
    except Exception as e:
        logger.error(f"Error in html_to_png: {str(e)}")
        return None
