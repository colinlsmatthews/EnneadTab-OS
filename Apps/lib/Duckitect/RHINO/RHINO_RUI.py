
import ENVIRONMENT
import FOLDER


try:
    import rhinoscriptsyntax as rs
except:
    pass



def update_my_rui():
    rs.CloseToolbarCollection("EnneadTab_For_Rhino_Installer", prompt=False)
    my_local_version = FOLDER.copy_file_to_local_dump_folder(ENVIRONMENT.RHINO_FOLDER + "\\EnneadTab_For_Rhino.rui")
    rs.OpenToolbarCollection(my_local_version)


  
    
def unit_test():
    pass

    
if __name__ == "__main__":

    update_my_rui()