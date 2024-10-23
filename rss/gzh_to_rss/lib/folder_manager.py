import requests as rq
import os
from typing import Dict, List
from lib.request_client import RequestClient
from lib.tools import get_override_param


class FolderManager:
    def __init__(self) -> None:
        self.api_url = os.getenv("api_url")
        self.headers = {}
        self.token = ""

    @RequestClient.login
    def create_folder(self, remote_folder_path: str) -> bool:
        """Create remote folder on the FileBrowser

        Args:
            remote_folder_path (str): Remote relative folder path on the FileBrowser

        Returns:
            bool: Successful or Failed
        """
        res = rq.post(
            url=f"{self.api_url}/resources/{remote_folder_path}/",  # ! Must ends with slash!
            headers=self.headers,
            verify=True,
        )
        if res.ok:
            print(f"Successfully create folder at {remote_folder_path}")
        else:
            print(f"Failed to create folder at {remote_folder_path}")
        return res.ok


    @RequestClient.login
    def list_dir(self, remote_folder_path = "") -> List:
        """List all the files and folders on the remote folder path

        Args:
            remote_folder_path (str, optional): Remote relative folder path on the FileBrowser. Defaults to "", which means the root directory.

        Returns:
            List: Existed files and folders
        """
        res = rq.get(
            url=f"{self.api_url}/resources/{remote_folder_path}",
            headers=self.headers,
            verify=True,
        )
        if res.ok:
            return res.json()
        else:
            print(res.text)
            return []
        

    @RequestClient.login
    def delete_folder(self, remote_folder_path: str) -> bool:
        """Delete remote folder on the FileBrowser

        Args:
            remote_folder_path (str): Remote relative folder path on the FileBrowser

        Returns:
            bool: Successful or Failed
        """
        res = rq.delete(
            url=f"{self.api_url}/resources/{remote_folder_path}/", # ! Must ends with slash!
            headers=self.headers,
            verify=True,
        )
        if res.ok:
            print(f"Successfully delete folder at {remote_folder_path}")
        else:
            print(res.text)
            print(f"Failed to delete folder at {remote_folder_path}")
        return res.ok

    
    @RequestClient.login
    def upload_folder(self, remote_folder_path: str, local_folder_path: str, should_override = False) -> bool:
        """Upload local folder to FileBrowser

        Args:
            remote_folder_path (str): Remote relative folder path on the FileBrowser
            local_folder_path (str): Local folder path
            should_override (bool, optional): Should override the existed folder or not. Defaults to False.

        Returns:
            bool: Successful or Failed
        """
        for filename in os.listdir(local_folder_path):
            filepath = os.path.join(local_folder_path, filename)
           
            # Only upload the files, not child directory
            if os.path.isdir(filepath):
                continue

            res = rq.post(
                url=f"{self.api_url}/resources/{remote_folder_path}/{filename}",
                params=get_override_param(should_override),
                headers=self.headers,
                verify=True,
                data=open(filepath, "rb")
            )
            if not res.ok:
                print(f"Failed to upload file {filename}")
                return res.ok
            
        print(f"Successfully uploading folder")
        return res.ok
