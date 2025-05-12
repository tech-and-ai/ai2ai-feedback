import os
import sys
import requests
from auth.service import AuthService
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("test_oauth")

def test_google_oauth():
    """Test the Google OAuth flow and report the response."""
    # Create auth service and get OAuth URL
    auth_service = AuthService()
    oauth_url = auth_service.get_oauth_url("google")
    
    logger.info(f"Generated OAuth URL: {oauth_url}")
    
    # Try to access the URL with requests
    try:
        response = requests.get(oauth_url, allow_redirects=False)
        logger.info(f"Status code: {response.status_code}")
        logger.info(f"Response headers: {dict(response.headers)}")
        
        # If we got redirected, follow the redirect once
        if response.status_code in (301, 302, 303, 307, 308) and 'location' in response.headers:
            redirect_url = response.headers['location']
            logger.info(f"Redirected to: {redirect_url}")
            
            # Follow the redirect
            redirect_response = requests.get(redirect_url, allow_redirects=False)
            logger.info(f"Redirect status code: {redirect_response.status_code}")
            logger.info(f"Redirect headers: {dict(redirect_response.headers)}")
            
            if 'location' in redirect_response.headers:
                logger.info(f"Second redirect to: {redirect_response.headers['location']}")
                
            # Check if there's an error in the redirect URL
            if 'error=' in redirect_url:
                error_part = redirect_url.split('error=')[1].split('&')[0]
                logger.error(f"Error in redirect: {error_part}")
            
    except Exception as e:
        logger.error(f"Error accessing OAuth URL: {str(e)}")

if __name__ == "__main__":
    test_google_oauth() 