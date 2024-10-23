import requests as rq
import os
from typing import Dict, List
from lib.request_client import RequestClient
from lib.tools import get_override_param


class FileManager:
    def __init__(self) -> None:
        self.api_url = os.getenv("api_url")
        self.headers = {}
        self.token = ""

    @RequestClient.login
    def create_file(self, remote_file_path: str, should_override = False) -> bool:
        """Create empty remote file

        Args:
            remote_file_path (str): Remote relative file path on the FileBrowser
            should_override (bool, optional): Should override the existed file or not. Defaults to False.

        Returns:
            bool: Successful or Failed
        """
        res = rq.post(
            url=f"{self.api_url}/resources/{remote_file_path}",
            params=get_override_param(should_override),
            headers=self.headers,
            verify=True,
        )
        if res.ok:
            print(f"Successfully create file at {remote_file_path}")
        else:
            print(f"Failed to create file at {remote_file_path}")
        return res.ok

    
    @RequestClient.login
    def get_file_info(self, remote_file_path: str) -> Dict:
        """Get the remote file information

        Args:
            remote_file_path (str): Remote relative file path on the FileBrowser 

        Returns:
            Dict: File information
        """
        res = rq.get(
            url=f"{self.api_url}/resources/{remote_file_path}",
            headers=self.headers,
            verify=True,
        )
        if res.ok:
            return res.json()
        else:
            print(res.text)
            return {}


    @RequestClient.login
    def upload_file(self, remote_file_path: str, local_file_path: str, should_override = False) -> bool:
        """Upload the local file to FileBrowser

        Args:
            remote_file_path (str): Remote relative file path on the FileBrowser 
            local_file_path (str): Local file path
            should_override (bool, optional): Should override the existed file or not. Defaults to False.

        Returns:
            bool: Successful or Failed
        """
        res = rq.post(
            url=f"{self.api_url}/resources/{remote_file_path}",
            params=get_override_param(should_override),
            headers=self.headers,
            verify=True,
            data=open(local_file_path, "rb")
        )
        if res.ok:
            print(f"Successfully upload file from {local_file_path} to {remote_file_path}")
        else:
            print(res.text)
            print("Failed to upload file")
        return res.ok


    @RequestClient.login
    def update_file_content(self, remote_file_path: str, content: str) -> bool:
        """Update the remote file content on the FileBrowser

        Args:
            remote_file_path (str): Remote relative file path on the FileBrowser 
            content (str): To be added content, be careful that it will replace the existed file content

        Returns:
            bool: Successful or Failed
        """
        res = rq.put(
            url=f"{self.api_url}/resources/{remote_file_path}",
            headers=self.headers,
            data=content,
            verify=True,
        )
        if res.ok:
            print(f"Successfully update file at {remote_file_path}")
        else:
            print(f"Failed to update file at {remote_file_path}")
        return res.ok


    @RequestClient.login
    def download_file(self, remote_file_path: str, local_file_path: str) -> bool:
        """Download the remote file from FileBrowser

        Args:
            remote_file_path (str): Remote relative file path on the FileBrowser 
            local_file_path (str): Local file path

        Returns:
            bool: Successful or Failed
        """
        res = rq.get(
            url=f"{self.api_url}/raw/{remote_file_path}?auth={self.token}",
            verify=True,
        )
        if res.ok:
            with open(local_file_path, "wb") as f:
                f.write(res.content)
            print(f"Successfully download file at {local_file_path}")
        else:
            print(f"Failed to download file at {local_file_path}")
        return res.ok


    @RequestClient.login
    def zip_files(self, remote_file_paths: List[str], local_file_path: str) -> bool:
        """Package multiple remote files and download the zip file

        Args:
            remote_file_paths (List[str]): Remote relative file paths on the FileBrowser 
            local_file_path (str): Local file path

        Returns:
            bool: Successful or Failed
        """
        files_query_params = ",".join(remote_file_paths)
        res = rq.get(
            url=f"{self.api_url}/raw/?files={files_query_params}&algo=zip&auth={self.token}",
            verify=True,
        )
        if res.ok:
            with open(local_file_path, "wb") as f:
                f.write(res.content)
            print(f"Successfully download files")
        else:
            print(res.text)
            print(f"Failed to download files")
        return res.ok


    @RequestClient.login
    def delete_file(self, remote_file_path: str) -> bool:
        """Delete a remote file on the FileBrowser

        Args:
            remote_file_path (str): Remote relative file path on the FileBrowser 

        Returns:
            bool: Successful or Failed
        """
        res = rq.delete(
            url=f"{self.api_url}/resources/{remote_file_path}",
            headers=self.headers,
            verify=True,
        )
        if res.ok:
            print(f"Successfully delete file at {remote_file_path}")
        else:
            print(res.text)
            print(f"Failed to delete file at {remote_file_path}")
        return res.ok