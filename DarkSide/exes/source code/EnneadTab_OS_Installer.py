import requests
import zipfile
import os
import shutil
import time



import _Exe_Util

class RepositoryUpdater:
    def __init__(self, repo_url):
        self.repo_url = repo_url
        self.extract_to = _Exe_Util.ESOSYSTEM_FOLDER

        if not os.path.exists(self.extract_to):
            os.makedirs(self.extract_to)
            
        self.final_folder_name = self.extract_repo_name(repo_url)
        self.final_dir = os.path.join(self.extract_to, self.final_folder_name)
    
    def extract_repo_name(self, url):
        if '/archive/' in url:
            parts = url.split('/')
            repo_index = parts.index('archive') - 1
            return parts[repo_index]
        return "Repository"
    
    def run_update(self):
        self.download_zip()
        self.extract_zip()
        self.update_files()
        self.cleanup()

    
    def download_zip(self):
        response = requests.get(self.repo_url, stream=True)
        if response.status_code == 200:
            self.zip_path = os.path.join(self.extract_to, "repo.zip")
            wait = 0
            while wait < 10:
                if os.path.exists(self.zip_path):
                    break
                time.sleep(1)
                wait+= 1
            with open(self.zip_path, "wb") as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)
            print("Zip file downloaded successfully.")
        else:
            raise Exception("Failed to download the repository. Status code: {}".format(response.status_code))
    
    def extract_zip(self):
        self.temp_dir = os.path.join(self.extract_to, "temp_extract")
        
        with zipfile.ZipFile(self.zip_path, 'r') as zip_ref:
            zip_ref.extractall(self.temp_dir)
        self.source_dir = os.path.join(self.temp_dir, os.listdir(self.temp_dir)[0])
        print("Zip file extracted.")
    
    def update_files(self):
        if not os.path.exists(self.final_dir):
            os.makedirs(self.final_dir)
        
        # Force copy everything over
        source_files = {os.path.join(dp, f): os.path.relpath(os.path.join(dp, f), self.source_dir) for dp, dn, filenames in os.walk(self.source_dir) for f in filenames}
        for src_path, rel_path in source_files.items():
            tgt_path = os.path.join(self.final_dir, rel_path)
            os.makedirs(os.path.dirname(tgt_path), exist_ok=True)
            shutil.copy2(src_path, tgt_path)


            
        # Delete files older than 1 days
        now = time.time()
        file_age_threshold = now - 1 * 24 * 60 * 60
        for dp, dn, filenames in os.walk(self.final_dir):
            for f in filenames:
                file_path = os.path.join(dp, f)
                if os.stat(file_path).st_mtime < file_age_threshold:
                    os.remove(file_path)
                    try:
                        os.rmdir(dp)  # Attempt to remove the directory if empty
                    except OSError:
                        pass
        print("Files have been updated.")
    
    def cleanup(self):
        shutil.rmtree(self.temp_dir)
        os.remove(self.zip_path)
        print("Cleanup completed.")


@_Exe_Util.try_catch_error
def main():
    repo_url = "https://github.com/zsenarchitect/EA_Dist/archive/refs/heads/master.zip"

    updater = RepositoryUpdater(repo_url)
    updater.run_update()

if __name__ == '__main__':

    main()

