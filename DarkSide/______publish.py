import os
import shutil
import datetime

import subprocess
import time
import traceback
import winsound
import sys


OS_REPO_FOLDER = os.path.dirname(os.path.dirname(__file__))
sys.path.append(OS_REPO_FOLDER + "\\Apps\\lib\\EnneadTab")



import UNIT_TEST #pyright: ignore
import NOTIFICATION #pyright: ignore
import FOLDER #pyright: ignore
import SOUND # pyright: ignore

class NoGoodSetupException(Exception):
    def __init__(self):
        super().__init__("The setup is not complete or you are working on a new computer.")
        

# Specify the absolute path to the git executable
locations = [
    "{}\\Local\\Programs\\Git\\cmd\\git.exe".format(FOLDER.get_appdata_folder()),
    "C:\Program Files\Git\cmd\git.exe"
]
for location in locations:
    if os.path.exists(location):
        GIT_LOCATION = location
        break
else:
    raise NoGoodSetupException()

def time_it(func):
    def wrapper(*args, **kwargs):
        start_time = time.time()
        result = func(*args, **kwargs)
        end_time = time.time()
        elapsed_time = end_time - start_time
        # ANSI escape codes for blue text with a white background
        blue_text = "\033[34m"
        reset_color = "\033[0m"
        
        # Print the formatted message with color
        print("{}Publish took {:.1f} seconds to complete.{}".format(blue_text, elapsed_time, reset_color))
        NOTIFICATION.duck_pop("Publish took {:.1f} seconds to complete.".format(elapsed_time))
        SOUND.play_sound("sound_effect_spring")

        return result
    return wrapper


def update_exes():
    sys.path.append(os.path.dirname(__file__) + "\\exes")
    from ExeMaker import recompile_exe # pyright: ignore
    recompile_exe()
 
def copy_to_EA_Dist_and_commit():
    # locate the EA_Dist repo folder and current repo folder
    # the current repo folder is 3 parent folder up
    EA_dist_repo_folder = os.path.join(os.path.dirname(OS_REPO_FOLDER), "EA_Dist")

    # process those two folders "Apps" and "Installation"
    # in EA_Dist folder, delete folder, then copy folder from current repo to EA_dist repo
    for folder in ["Apps", "Installation"]:
        # delete folder in EA_dist repo if exist
        try_remove_content(os.path.join(EA_dist_repo_folder, folder))

        # copy folder from current repo to EA_dist repo
        shutil.copytree(os.path.join(OS_REPO_FOLDER, folder), os.path.join(EA_dist_repo_folder, folder))

    
    # pull the latest changes from remote
    pull_changes_from_main(EA_dist_repo_folder)
    
    # push EA_dist to update branch, try max 3 times
    for attemp in range(3):
        if push_changes_to_main(EA_dist_repo_folder):
            break

    # Play Windows built-in notification sound
    winsound.MessageBeep(winsound.MB_ICONEXCLAMATION)

def try_remove_content(folder_path):
    if os.path.exists(folder_path):
        if os.path.isfile(folder_path):
            os.remove(folder_path)
        else:
            shutil.rmtree(folder_path)



def get_nth_commit_number():
    # Count the number of commits made today
    result = subprocess.Popen([GIT_LOCATION, "log", "--since=midnight", "--oneline"], stdout=subprocess.PIPE)
    commits = result.stdout.readlines()
    return len(commits) + 1

def pull_changes_from_main(repository_path):
    try:
        # # Print the current PATH environment variable
        # print("Current PATH:", os.environ['PATH'])
        


        # Change to the Git repository directory
        print("Changing directory to:", repository_path)
        os.chdir(repository_path)

        # Stash local changes
        print("Running git stash")
        stash_result = subprocess.call([GIT_LOCATION, "stash"])
        if stash_result != 0:
            raise Exception("Git stash command failed with return code {}".format(stash_result))

        # Pull the latest changes from the main branch
        print("Running git pull origin main")
        pull_result = subprocess.call([GIT_LOCATION, "pull", "origin", "main"])
        if pull_result != 0:
            raise Exception("Git pull command failed with return code {}".format(pull_result))

        # Apply stashed changes
        print("Running git stash pop")
        pop_result = subprocess.call([GIT_LOCATION, "stash", "pop"])
        if pop_result != 0:
            raise Exception("Git stash pop command failed with return code {}".format(pop_result))

    except FileNotFoundError as e:
        print("FileNotFoundError: Ensure Git is installed and available in PATH")
        print(traceback.format_exc())
        raise e
    except Exception as e:
        print("An error occurred while pulling changes from the main branch")
        print(traceback.format_exc())
        raise e

def push_changes_to_main(repository_path):


    # Change to the Git repository directory
    print("Changing directory to:", repository_path)
    os.chdir(repository_path)

    # Stage all changes
    print("Running git add .")
    add_result = subprocess.call([GIT_LOCATION, "add", "."])
    if add_result != 0:
        raise Exception("Git add command failed with return code {}".format(add_result))

    commit_number = get_nth_commit_number()

    # Commit with today's date
    current_date = datetime.datetime.now().strftime('%Y-%m-%d')
    commit_message = "Auto push changes committed on {}...{}".format(current_date, commit_number)
    print("Running git commit -m")
    commit_result = subprocess.call([GIT_LOCATION, "commit", "-m", commit_message])
    if commit_result != 0:
        raise Exception("Git commit command failed with return code {}".format(commit_result))

    # Push to the main branch
    print("Running git push origin main")
    push_result = subprocess.call([GIT_LOCATION, "push", "origin", "main"])
    if push_result != 0:
        raise Exception("Git push command failed with return code {}".format(push_result))

    return True


def update_installer_folder():
    # locate the EA_Dist repo folder and current repo folder
    # the current repo folder is 3 parent folder up

    installation_folder = os.path.join(OS_REPO_FOLDER, "Installation")
    if os.path.exists(installation_folder):
        shutil.rmtree(installation_folder)
    os.makedirs(installation_folder)


    # copy folder from current repo to EA_dist repo
    for file in ["EnneadTab_OS_Installer.exe",
                 "EnneadTab_For_Revit(Legacy)_Installer.exe",
                 "EnneadTab_For_Revit_UnInstaller.exe"]:
        shutil.copy(os.path.join(OS_REPO_FOLDER, "Apps", "lib", "ExeProducts", file), 
                    os.path.join(OS_REPO_FOLDER, "Installation", file))

@time_it
def publish_duck():


    if manual_confirm_should_compile_exe():
        print_title ("\n\nBegin compiling all exes...")
        NOTIFICATION.messenger("Recompiling all exes...kill VScode if you want to cancel..")
        update_exes()
    else:
        NOTIFICATION.messenger("NOT compiling exes today...")
    print_title ("\n\nBegin updating installation folder for public easy install...")
    update_installer_folder()


    # recompile the rui layout for rhino
    import RuiWriter
    RuiWriter.run()

    print_title("Start testing all moudle.")
    UNIT_TEST.test_core_module()
        
    print_title ("\n\npush uptdate to EA dist folder")
    copy_to_EA_Dist_and_commit()


def manual_confirm_should_compile_exe():
    """manua change date to see if I should recompile exe
    so each recompile is more intentional"""
    return str(datetime.date.today()) == "2024-07-03"
    

def print_title(text):
    # ANSI escape code for larger text
    large_text = "\033[1m" + text + "\033[0m"
    print(large_text)


if __name__ == '__main__':
    publish_duck()