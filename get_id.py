from pydrive.auth import GoogleAuth
from pydrive.drive import GoogleDrive


def get_id():
    """
    This function updates files with ids of works from google drive
    """
    gauth = GoogleAuth()
    gauth.LocalWebserverAuth()
    drive = GoogleDrive(gauth)
    file_list = drive.ListFile({'q': "'1ymVpvovK1jfTNSom1PPTI2MDFmeJLb1y' in parents and trashed=false"}).GetList()
    for number_of_task in range(1, 7):
        with open(str(number_of_task) + '_idToFilesGoogleDrive.txt', 'w') as file:
            for file1 in file_list:
                if file1['title'][0] == str(number_of_task):
                    file.write(file1['id'] + "\t" + file1['title'] + "\n")


if __name__ == '__main__':
    get_id()
