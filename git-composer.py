import os
import subprocess
import glob
import re
import pprint as p
import json
import requests
from termcolor import colored

os.system("python3 -V")
os.system("echo $TEST")

#Magento Release tag version
gitTagVersionBranch = "2.4.2"
gitCheckoutCommand = "cd ./magento2/ && git checkout tags/"+gitTagVersionBranch

os.system(gitCheckoutCommand)
path = "./magento2/app/code/Magento/"

folders = glob.glob(path + '*')
#ToDo: add another folders with the composer packages
# ./magento2/app/design/adminhtml/Magento/*
# ./magento2/app/design/frontend/Magento
# ./magento2/app/i18n/Magento
# ./magento2/lib/internal/Magento/
# etc...

def exec(command, return_code_output=False, output=True):
    try:
        result_output = subprocess.check_output(command, shell=True, stderr=subprocess.STDOUT)
        if output == True:
            print("Out:")
            print(str(result_output))
        return_code = 0
    except subprocess.CalledProcessError as e:
        if output == True:
            print("Error:")
            print(str(e.output))
        result_output = e.output
        return_code = e.returncode
    if return_code_output == True:
        return {"result_output":result_output, "return_code":return_code}
    else:
        return str(result_output.decode())

result = exec("sfsdfds")

print(folders)
# Folder to copy modules to
buildFolder = "magento-modules-separate"
# Name of the gitHub organisation or account
# (account is not tested by doc it shuld be empty but baybe it will works)
organisationName = "test-magenx"
exec("mkdir " + buildFolder)

#set your keys and users
#toDo: use Env and inpit
packagistAPIToken = "M7WSvqj*******"
packagistUser = "genaker"
gitToken = "ghp_NXN********"
gitUser = "Genaker"

for module in folders:

    # module actualy is a magento folder like :./magento2/app/code/Magento/Paypal
    print(colored("\n=====[" + module + "]========>", 'red'))

    # Copy a single module to separate build folder
    exec("cp -r " + module + " " + buildFolder + "/")
    #get the last part of the module name 
    folderModuleName = module.split("/")[-1]
    print("Module Folser: " + folderModuleName)
    buildModuleFolder = buildFolder + "/" + folderModuleName
    print("Build Module Folder: " + buildModuleFolder)
    composerPath = module+"/composer.json"
    print("Composer Module Path: "+composerPath)
    composerExists = os.path.exists(composerPath)
    print("Composer Exists:"+str(composerExists))
    if composerExists == True:
        # composer JSON file
        f = open (composerPath, "r")
        data = json.loads(f.read())
        f.close()

        moduleName = data["name"]
        moduleVersion = data["version"]
        print("Magento Module Name: " + moduleName)
        print("Magento Module Version: " + moduleVersion)

        #Change Magento name with organisation name
        moduleNameNew = moduleName.replace("magento/", organisationName + "/")
        print("Magento Fork Module Name: " + moduleNameNew)
        data["name"] = moduleNameNew

        # save new composer name to buid module folder composer.json
        with open(buildModuleFolder + "/composer.json", 'w') as f2:
            json.dump(data, f2, indent=4)
        # potentially we can check if the package exists.
        packagistPackagesearch = 'https://repo.packagist.org/p2/' +  moduleName + '.json'
        f2.close()

        # cd to the masgento buildModuleFolder shuld be appended to the all commands 
        cdCommand = "cd " + buildModuleFolder
        exec(cdCommand)
        print("CurentFolder:" + exec(cdCommand + " && pwd"))
        
        #init git repo in the magento module build folder
        print(cdCommand + " && git init ")
        exec(cdCommand + " && git init ")

        #Create gitHub repo. If it is exist it will return error. 
        ghCreateRepo = "gh repo create " + moduleNameNew + " --public --confirm"
        print(cdCommand + " && " + ghCreateRepo)
        exec(cdCommand + " && " + ghCreateRepo)

        # add new remote origin to the magento module git local repo 
        addRemoteOriginCommand = "git remote add origin https://"+gitUser+":"+gitToken+"@github.com/" + moduleNameNew + ".git"
        print(cdCommand + " && " + addRemoteOriginCommand)
        exec(cdCommand + " && " + addRemoteOriginCommand)

        # Commit to the master the latest version
        # ToDo: check it is id the lates version
        print("Push Magento master branch")
        commitCommand = "git checkout -b master; git add . ; git commit -m 'Magento Fork initial commit'; git push -u origin master"
        print (colored(cdCommand + " && " + commitCommand, 'green'))
        exec(cdCommand + " && " + commitCommand)

        # commit module by magento version  
        ## Magento version tag doesn't work becouse of: Some tags were ignored because of a magento version mismatch module version in composer.json, read more.
        print("Push Magento version branch")
        commitCommand = "git checkout -b " + gitTagVersionBranch + "; git add . ; git commit -m 'Magento Fork initial commit'; git push -u origin " + gitTagVersionBranch
        print (colored(cdCommand + " && " + commitCommand, 'yellow'))
        exec(cdCommand + " && " + commitCommand)

        # commit module by module version with the tags
        commitCommand = "git checkout -b " + moduleVersion + "; git add . ; git commit -m 'Magento Fork initial commit'; git push -u origin " + moduleVersion + "; git tag " + moduleVersion + "; git push origin --tags"
        print(colored(cdCommand + " && " + commitCommand, 'yellow'))
        exec(cdCommand + " && " + commitCommand)

        # Create release by module version
        ghReleaseCreateCommand = "gh release create " + moduleVersion
        print (colored(ghReleaseCreateCommand, 'blue'))
        exec(cdCommand + " && " + ghReleaseCreateCommand)

        # Create a package
        # This endpoint creates a package for a specific repo. Parameters username and apiToken are required. Only POST method is allowed.
        #POST https://packagist.org/api/create-package?username=[username]&apiToken=[apiToken] -d '{"repository":{"url":"[url]"}}'

        #Create new package: 
        createPackageCommand = "curl -X POST 'https://packagist.org/api/create-package?username=" + packagistUser + "&apiToken=" + packagistAPIToken + "' -d '{\"repository\":{\"url\":\"https://github.com/" + moduleNameNew + "\"}}'"
        print (colored(createPackageCommand, 'green'))
        exec(createPackageCommand)
        
        # Packagist update package: 
        #https://packagist.org/api/update-package?username=genaker&apiToken=API_TOKEN 
        # with a request body looking like this: {"repository":{"url":"PACKAGIST_PACKAGE_URL"}}
        updatePackageCommand  =  "curl -XPOST -H'content-type:application/json' 'https://packagist.org/api/update-package?username="+ packagistUser + "&apiToken=" + packagistAPIToken + "' -d'{\"repository\":{\"url\":\"https://github.com/" + moduleNameNew + "\"}}'"
        print(colored(updatePackageCommand, 'blue'))
        exec(updatePackageCommand)
        
        ## Installation of the Git Hub linux packages required :
        # https://github.com/cli/cli/blob/trunk/docs/install_linux.md#fedora-centos-red-hat-enterprise-linux-dnf
        #print(packagistPackagesearch)
        #r = requests.get(packagistPackagesearch)
        #print(r.json())
