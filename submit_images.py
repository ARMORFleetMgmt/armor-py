import os
import sys
import argparse
from client import ArmorClient

"""
Script to submit images to the models-manager/finder/submit API.

This script iterates through a directory structure containing manufacturer directories,
model directories, and image files, and submits each image to the models-manager/finder/submit API.

The expected directory structure is:
- Root directory (specified by the 'directory' argument)
  - Manufacturer directories (e.g., taski-by-diversey, tennant)
    - Model directories (e.g., swingo-1650, fm-17-ss)
      - Image files (e.g., image1.jpg, image2.png)

The manufacturer ID is extracted from the manufacturer directory name,
and the model ID is extracted from the model directory name.

Usage examples:
  # Using token authentication
  python submit_images.py /path/to/images --token YOUR_API_TOKEN

  # Using username/password authentication
  python submit_images.py /path/to/images --user YOUR_USERNAME --password YOUR_PASSWORD

  # Specifying a custom API URL
  python submit_images.py /path/to/images --url https://custom-api-url.com/api/v1/ --token YOUR_API_TOKEN

  # Enabling debug output
  python submit_images.py /path/to/images --token YOUR_API_TOKEN --debug
"""

def submit_images(client, directory_path):
    """
    Iterate through a directory structure and submit images to the models-manager/finder/submit API.

    The directory structure is expected to be:
    - Root directory (directory_path)
      - Manufacturer directories (e.g., taski-by-diversey, tennant)
        - Model directories (e.g., swingo-1650, fm-17-ss)
          - Image files (e.g., image1.jpg, image2.png)

    Args:
        client (ArmorClient): The ArmorClient instance to use for API calls
        directory_path (str): The path to the root directory containing manufacturer directories
    """
    # Check if the directory exists
    if not os.path.isdir(directory_path):
        print(f"Error: Directory '{directory_path}' does not exist.")
        return

    # Initialize counters
    total_images = 0
    successful_submissions = 0
    failed_submissions = 0

    # Iterate through manufacturer directories
    for manufacturer_id in os.listdir(directory_path):
        manufacturer_path = os.path.join(directory_path, manufacturer_id)

        # Skip if not a directory
        if not os.path.isdir(manufacturer_path):
            continue

        print(f"Processing manufacturer: {manufacturer_id}")

        # Iterate through model directories in the manufacturer directory
        for model_id in os.listdir(manufacturer_path):
            model_path = os.path.join(manufacturer_path, model_id)

            # Skip if not a directory
            if not os.path.isdir(model_path):
                continue

            print(f"  Processing model: {model_id}")

            # Iterate through image files in the model directory
            for filename in os.listdir(model_path):
                file_path = os.path.join(model_path, filename)

                # Skip if not a file or not an image file
                if not os.path.isfile(file_path) or not filename.lower().endswith(('.jpg', '.jpeg', '.png')):
                    continue

                print(f"    Submitting image: {filename} (Manufacturer: {manufacturer_id}, Model: {model_id})")

                try:
                    # Read the image file
                    with open(file_path, 'rb') as f:
                        image_data = f.read()

                    # Determine Content-Type based on file extension
                    ext = filename.lower().split('.')[-1]
                    if ext in ['jpg', 'jpeg']:
                        content_type = 'image/jpeg'
                    elif ext == 'png':
                        content_type = 'image/png'
                    else:
                        content_type = 'application/octet-stream'

                    # Submit the image to the API
                    response = client.request(
                        method="POST",
                        uri="models-manager/finder/submit",
                        query={"manufacturerId": manufacturer_id, "modelId": model_id},
                        body=image_data,
                        headers={
                            "Content-Type": content_type,
                            "Content-Disposition": filename
                        }
                    )

                    # Check the response
                    if response.status == 200:
                        print(f"      Success: {response.bodyText()}")
                        successful_submissions += 1
                    else:
                        print(f"      Error: {response.status} - {response.bodyText()}")
                        failed_submissions += 1

                    total_images += 1

                except Exception as e:
                    print(f"      Error: {str(e)}")
                    failed_submissions += 1
                    total_images += 1

    # Print summary
    print("\nSummary:")
    print(f"Total images processed: {total_images}")
    print(f"Successful submissions: {successful_submissions}")
    print(f"Failed submissions: {failed_submissions}")

def main():
    # Parse command line arguments
    parser = argparse.ArgumentParser(description='Submit images to the models-manager/finder/submit API.')
    parser.add_argument('directory', help='Path to the directory containing manufacturer directories with images')
    parser.add_argument('--url', default='https://app.armordata.io/api/v1/', help='API URL')
    parser.add_argument('--token', help='API token')
    parser.add_argument('--user', help='API username')
    parser.add_argument('--password', help='API password')
    parser.add_argument('--debug', action='store_true', help='Enable debug output')

    args = parser.parse_args()

    # Create ArmorClient instance
    if args.token:
        client = ArmorClient(args.url, token=args.token, debug=args.debug)
    elif args.user and args.password:
        client = ArmorClient(args.url, user=args.user, password=args.password, debug=args.debug)
    else:
        print("Error: Either token or user/password must be provided.")
        parser.print_help()
        return 1

    # Submit images
    submit_images(client, args.directory)

    return 0

if __name__ == "__main__":
    sys.exit(main())
