import os
import zipfile
import uuid
import re
from random import randint
from PySide6 import QtWidgets, QtCore, QtGui

from .tweak_classes import Tweak
from Sparserestore.restore import FileToRestore
from controllers.plist_handler import set_plist_value
from qt.ui_mainwindow import Ui_Nugget

class TendieFile:
    path: str
    name: str
    descriptor_cnt: int
    is_container: bool
    unsafe_container: bool
    loaded: bool

    def __init__(self, path: str):
        self.path = path
        self.name = os.path.basename(path)
        self.descriptor_cnt = 0
        self.is_container = False
        self.unsafe_container = False
        self.loaded = False

        # read the contents
        with zipfile.ZipFile(path, mode="r") as archive:
            for option in archive.namelist():
                if "__macosx/" in option.lower():
                    continue
                if "container" in option.lower():
                    self.is_container = True
                    # check for the unsafe file that requires prb reset
                    if "PBFPosterExtensionDataStoreSQLiteDatabase.sqlite3" in option:
                        self.unsafe_container = True
                if "descriptor/" in option.lower():
                    item = option.lower().split("descriptor/")[1]
                    if item.count('/') == 1 and item.endswith('/'):
                        self.descriptor_cnt += 1
                elif "descriptors/" in option.lower():
                    item = option.lower().split("descriptors/")[1]
                    if item.count('/') == 1 and item.endswith('/'):
                        self.descriptor_cnt += 1

    def get_icon(self):
        if self.is_container:
            # container
            return ":/icon/shippingbox.svg"
        elif self.descriptor_cnt == 1:
            # single descriptor
            return ":/icon/photo.svg"
        else:
            # multiple descriptors
            return ":/icon/photo-stack.svg"

class PosterboardTweak(Tweak):
    def __init__(self):
        super().__init__(key=None)
        self.tendies: list[TendieFile] = []
        self.bundle_id = "com.apple.PosterBoard"
        self.resetting = False
        self.resetType = 0 # 0 for descriptor 1 for prb

    def add_tendie(self, file: str):
        new_tendie = TendieFile(path=file)
        if new_tendie.descriptor_cnt + self.get_descriptor_count() <= 10:
            self.tendies.append(new_tendie)
            # alert if prb reset is needed
            if new_tendie.unsafe_container:
                detailsBox = QtWidgets.QMessageBox()
                detailsBox.setIcon(QtWidgets.QMessageBox.Critical)
                detailsBox.setWindowTitle("Warning")
                detailsBox.setText("NOTE: You may need to reset all wallpapers (enable Risky Options in settings) and then re-apply for this file to work.")
                detailsBox.exec()
            return True
        return False

    def get_descriptor_count(self):
        cnt = 0
        for tendie in self.tendies:
            cnt += tendie.descriptor_cnt
        return cnt

    def update_plist_id(self, file_path: str, file_name: str, randomizedID: int):
        if file_name == "com.apple.posterkit.provider.descriptor.identifier":
            return str(randomizedID).encode()
        elif file_name == "com.apple.posterkit.provider.contents.userInfo":
            return set_plist_value(file=os.path.join(file_path, file_name), key="wallpaperRepresentingIdentifier", value=randomizedID)
        elif file_name == "Wallpaper.plist":
            return set_plist_value(file=os.path.join(file_path, file_name), key="identifier", value=randomizedID)
        return None
    

    def clean_path_name(self, path: str):
        return path# re.sub('[^a-zA-Z0-9\.\/\-_ ]', '', path)
        

    def recursive_add(self,
                      files_to_restore: list[FileToRestore],
                      curr_path: str, restore_path: str = "",
                      isAdding: bool = False,
                      randomizeUUID: bool = False, randomizedID: int = None
        ):
        for folder in sorted(os.listdir(curr_path)):
            if folder.startswith('.') or folder == "__MACOSX":
                continue
            if isAdding:
                # randomize uuid
                folder_name = folder
                curr_randomized_id = randomizedID
                if randomizeUUID:
                    folder_name = str(uuid.uuid4()).upper()
                    curr_randomized_id = randint(9999, 99999)
                # if file then add it, otherwise recursively call again
                if os.path.isfile(os.path.join(curr_path, folder)):
                    try:
                        # update plist ids if needed
                        new_contents = None
                        contents_path = os.path.join(curr_path, folder)
                        if curr_randomized_id != None:
                            new_contents = self.update_plist_id(curr_path, folder, curr_randomized_id)
                            if new_contents != None:
                                contents_path = None
                        files_to_restore.append(FileToRestore(
                            contents=new_contents,
                            contents_path=contents_path,
                            restore_path=self.clean_path_name(f"{restore_path}/{folder_name}"),
                            domain=f"AppDomain-{self.bundle_id}"
                        ))
                    except IOError:
                        print(f"Failed to open file: {folder}") # TODO: Add QDebug equivalent
                else:
                    self.recursive_add(files_to_restore, os.path.join(curr_path, folder), f"{restore_path}/{folder_name}", isAdding, randomizedID=curr_randomized_id)
            else:
                # look for container folder
                name = folder.lower()
                if name == "container":
                    self.recursive_add(files_to_restore, os.path.join(curr_path, folder), restore_path="/", isAdding=True)
                    return
                elif name == "descriptor" or name == "descriptors":
                    self.recursive_add(
                        files_to_restore,
                        os.path.join(curr_path, folder),
                        restore_path="/Library/Application Support/PRBPosterExtensionDataStore/61/Extensions/com.apple.WallpaperKit.CollectionsPoster/descriptors",
                        isAdding=True,
                        randomizeUUID=True
                    )
                else:
                    self.recursive_add(files_to_restore, os.path.join(curr_path, folder), isAdding=False)

    def apply_tweak(self, files_to_restore: list[FileToRestore], output_dir: str, windows_path_fix: bool):
        # unzip the file
        if not self.enabled:
            return
        if self.resetting:
            # null out the folder
            file_paths = []
            if self.resetType == 0:
                # resetting descriptors
                file_paths.append("/61/Extensions/com.apple.WallpaperKit.CollectionsPoster/descriptors")
                file_paths.append("/61/Extensions/com.apple.MercuryPoster/descriptors")
            else:
                file_paths.append("")
            for file_path in file_paths:
                files_to_restore.append(FileToRestore(
                    contents=b"",
                    restore_path=f"/Library/Application Support/PRBPosterExtensionDataStore{file_path}",
                    domain=f"AppDomain-{self.bundle_id}"
                ))
            return
        elif self.tendies == None or len(self.tendies) == 0:
            return
        if os.name == "nt" and windows_path_fix:
            # try to get past directory name limit on windows
            output_dir = "\\\\?\\" + output_dir
        for tendie in self.tendies:
            zip_output = os.path.join(output_dir, str(uuid.uuid4()))
            os.makedirs(zip_output)
            with zipfile.ZipFile(tendie.path, 'r') as zip_ref:
                zip_ref.extractall(zip_output)
        # add the files
        self.recursive_add(files_to_restore, curr_path=output_dir)
