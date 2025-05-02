import os
import uuid
import zipfile
import fnmatch

from json import load
from typing import Optional
from tempfile import TemporaryDirectory
from shutil import rmtree

from .tendie_file import TendieFile
from .template_options import OptionType, TemplateOption, ReplaceOption, RemoveOption, SetOption, PickerOption
from exceptions.posterboard_exceptions import PBTemplateException

CURRENT_FORMAT = 1

class TemplateFile(TendieFile):
    options: list[TemplateOption]
    json_path: str
    tmp_dir: str = None

    # TODO: Move these to custom operations
    description: Optional[str] = None # description to go under the file
    resources: list[str] = [] # list of file paths for embedded resources
    previews: dict[str, str] = {} # list of resources to use as previews
    preview_layout: str = "horizontal" # the direction to lay out the preview images

    banner_text: Optional[str] = None # text to go as a banner
    banner_stylesheet: Optional[str] = None # style sheet of the banner
    format_version: int = CURRENT_FORMAT # format version of config

    def __init__(self, path: str):
        super().__init__(path=path)
        self.options = []
        self.json_path = None

        # find the config.json file
        with zipfile.ZipFile(path, mode="r") as archive:
            for option in archive.namelist():
                if "config.json" in option.lower() and not "descriptor" in option.lower() and not "container" in option.lower():
                    self.json_path = option
                    break
            if self.json_path != None:
                file = archive.open(self.json_path)
                data = load(file)
                # load the options
                if not 'options' in data:
                    raise PBTemplateException(path, "No options were found in the config. Make sure that it is in the correct format.")
                if not 'domain' in data or (data['domain'] != "AppDomain-com.apple.PosterBoard" and data['domain'] != "com.apple.PosterBoard"):
                    # made an oopsie here, only AppDomain-com.apple.PosterBoard should be allowed
                    # I will allow com.apple.PosterBoard to not break support
                    raise PBTemplateException(path, "This config is not for the domain \"AppDomain-com.apple.PosterBoard\". Make sure that it is compatible with your version of Nugget.")
                self.format_version = int(data['format_version'])
                if self.format_version > CURRENT_FORMAT:
                    raise PBTemplateException(path, "This config requires a newer version of Nugget.")
                self.name = f"{data['title']} - by {data['author']}"
                if 'description' in data:
                    self.description = data['description']
                # load the previews
                prevs = []
                if 'previews' in data:
                    prevs = data['previews']
                    if 'preview_layout' in data:
                        self.preview_layout = data['preview_layout']
                # load the banner
                if 'banner_text' in data:
                    self.banner_text = data['banner_text']
                    if 'banner_stylesheet' in data:
                        self.banner_stylesheet = data['banner_stylesheet']
                # load the resources
                if 'resources' in data:
                    self.resources = data['resources']
                    # open the resources and put them in temp files
                    rcs_path = self.json_path.removesuffix("config.json")
                    for resource in self.resources:
                        # handle wildcards
                        rc_pattern = rcs_path + resource
                        for rc_path in fnmatch.filter(archive.namelist(), rc_pattern):
                            rc_data = archive.read(rc_path)
                            if rc_data != None:
                                # write it to a temp file
                                if self.tmp_dir == None:
                                    self.tmp_dir = TemporaryDirectory()
                                rc_full_path = os.path.join(self.tmp_dir.name, rc_path)
                                os.makedirs(os.path.dirname(rc_full_path), exist_ok=True)
                                with open(rc_full_path, "wb") as rc_fp:
                                    rc_fp.write(rc_data)
                                # update the url in the banner stylesheet
                                clean_path = rc_path.replace(rcs_path, "")
                                if self.banner_stylesheet != None:
                                    self.banner_stylesheet = self.banner_stylesheet.replace(f"url({clean_path})", f"url({rc_full_path})")
                                # set the preview images
                                if clean_path in prevs:
                                    self.previews[clean_path] = rc_full_path

                # TODO: Add error handling
                for option in data['options']:
                    opt_type = OptionType[option['type']]
                    if opt_type == OptionType.replace:
                        self.options.append(ReplaceOption(data=option))
                    elif opt_type == OptionType.remove:
                        self.options.append(RemoveOption(data=option))
                    elif opt_type == OptionType.set:
                        self.options.append(SetOption(data=option))
                    elif opt_type == OptionType.picker:
                        self.options.append(PickerOption(data=option))
                    else:
                        raise PBTemplateException(path, "Invalid option type in template")
            else:
                raise PBTemplateException(path, "No config.json found in file!")
    
    def clean_files(self):
        if self.tmp_dir != None:
            try:
                rmtree(self.tmp_dir.name)
            except Exception as e:
                print(f"Error when removing temp dir: {str(e)}")

    def extract(self, output_dir: str):
        zip_output = os.path.join(output_dir, str(uuid.uuid4()))
        os.makedirs(zip_output)
        with zipfile.ZipFile(self.path, 'r') as zip_ref:
            zip_ref.extractall(zip_output)

        # apply the options
        parent_path = os.path.join(zip_output, os.path.dirname(self.json_path))
        for option in self.options:
            option.apply(container_path=parent_path)