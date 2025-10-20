import os
from linkbio_client import LinkBioClient

def main():
    """
    Tests the LinkBioClient by fetching user info and adding a link.
    """
    if not os.getenv('LINKBIO_CLIENT_ID') or not os.getenv('LINKBIO_CLIENT_SECRET'):
        print("Please set the LINKBIO_CLIENT_ID and LINKBIO_CLIENT_SECRET environment variables.")
        return

    client = LinkBioClient()

    print("Testing get_user_info...")
    user_info = client.get_user_info()

    if user_info:
        print("Successfully fetched user info:")
        print(user_info)
    else:
        print("Failed to fetch user info.")
        return

    print("\nTesting add_link...")
    # You can change the URL and title here
    test_url = "https://example.com/test-from-script"
    test_title = "Test Link from Script"
    
    if client.add_link(test_url, test_title):
        print(f"Successfully added link: {test_title} ({test_url})")
    else:
        print("Failed to add link.")

if __name__ == "__main__":
    main()

