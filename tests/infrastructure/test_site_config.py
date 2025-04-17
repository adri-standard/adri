import os
import yaml

# Read site_config.yml
with open('site_config.yml', 'r') as file:
    config = yaml.safe_load(file)

# Extract site_base_url
site_base_url = config.get('site_base_url')
print(f"URL from config: {site_base_url}")

# Set environment variable
os.environ['SITE_BASE_URL'] = site_base_url
print(f"Environment variable set: SITE_BASE_URL={os.environ.get('SITE_BASE_URL')}")

print("\nThis script demonstrates that the GitHub Actions workflow will:")
print("1. Read the site_config.yml file")
print("2. Extract the site_base_url value")
print("3. Set it as an environment variable for the mkdocs build")
print("4. The site will be built with the correct URL")
