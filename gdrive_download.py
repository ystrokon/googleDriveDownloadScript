"""
Authenticate and download file(s) from Google Drive with PyDrive.

Usage:
   # download single file:
        python gdrive_download.py --service-account-key SERVICE_ACCOUNT_KEY_FILE --file FILE_TO_DOWNLOAD_NAME --directory-id GDRIVE_FOLDER_ID
   # download all files from the gdrive folder:
        python gdrive_download.py --service-account-key SERVICE_ACCOUNT_KEY_FILE --directory-id GDRIVE_FOLDER_ID

Expected workflow is:
    1. Creating service account and key: https://cloud.google.com/endpoints/docs/openapi/service-account-authentication#create_service_account

    2. Granting access permission for the service account.

    3. Getting gdrive folder id(open the folder and copy it from the url) and file name.

    4. Run the script.

"""

from pydrive.auth import GoogleAuth
from pydrive.drive import GoogleDrive
from oauth2client.service_account import ServiceAccountCredentials

from argparse import ArgumentParser
import os

def parse_args():
    """ Parse arguments """

    parser = ArgumentParser(description="Download local files from Google Drive")
    parser.add_argument('-s', '--service-account-key', type=str,
                        help='Service account JSON key file for GoogleAuth()', required=True)
    parser.add_argument('-d', '--directory-id', type=str, help='Gdrive folder id where the file is located', required=True)
    parser.add_argument('-f', '--file', type=str,
                        help='File name to download (optional). If not specified the whole --directory-id will be downloaded')
    parser.add_argument('-dest', '--destination', type=str, help='Absolute path where file(s) will be downloaded')
    parser.add_argument('--fail-if-nothing-was-downloaded', action='store_true')

    return parser.parse_args()


def auth_with_service_account_key(service_account_key):
    """
        Authentication using service account key(JSON) (https://cloud.google.com/endpoints/docs/openapi/service-account-authentication)
    """

    gauth = GoogleAuth()
    scope = ["https://www.googleapis.com/auth/drive"]
    gauth.credentials = ServiceAccountCredentials.from_json_keyfile_name(service_account_key, scope)
    gauth.Authorize()
    return gauth


def get_file_list(drive, folder_id):
    file_list = drive.ListFile({
        'q': f"'{folder_id}' in parents and trashed=false",
        'supportsAllDrives': True,
        'includeItemsFromAllDrives': True,
    }).GetList()
    return file_list


def download(file_list, file_name=""):
    downloads_counter = 0
    cwd = os.getcwd()
    for file in file_list:
        title = file['title']
        if (not file_name or title == file_name) and file['mimeType'] != "application/vnd.google-apps.folder":
            print(f"Downloading file '{cwd}/{title}'...")
            file.GetContentFile(title)
            downloads_counter += 1

    return downloads_counter


def main():
    """ Main """

    args = parse_args()

    # auth
    gauth = auth_with_service_account_key(args.service_account_key)

    # drive
    drive = GoogleDrive(gauth)
    file_list = get_file_list(drive, args.directory_id)

    # change cwd
    if args.destination:
        if not os.path.isdir(args.destination):
            os.mkdir(args.destination)
        os.chdir(args.destination)

    # download
    downloads_counter = download(file_list, args.file)
    print(f"Downloaded {downloads_counter} file(s).")
    if downloads_counter == 0 and args.fail_if_nothing_was_downloaded:
        raise Exception("Error: Nothing was downloaded")


if __name__ == "__main__":
    main()
