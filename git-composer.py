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

gitTagVersionBranch = "2.4.2"
gitCheckoutCommand = "cd ./magento2/ && git checkout tags/"+gitTagVersionBranch

os.system(gitCheckoutCommand)
path = "./magento2/app/code/Magento/"

folders = glob.glob(path + '*')

def exec(command, return_code_output=False):
    try:
        result_output = subprocess.check_output(command, shell=True, stderr=subprocess.STDOUT)
        print("Out:")
        print(str(result_output))
        return_code = 0
    except subprocess.CalledProcessError as e:
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
buildFolder = "magento-modules-separate"
organisationName = "test-magenx"
exec("mkdir " + buildFolder)

#set your keys and users
#toDo: use Env and inpit
packagistAPIToken = "M7WSvqjk***"
packagistUser = "genaker"
gitToken = "ghp_NXNjyRjk5ij***"
gitUser = "Genaker"

ghCreateRepo = "gh repo create {project-name}"

for module in folders:

    print(colored("\n=====[" + module + "]========>", 'red'))

    # Copy to separate folder
    exec("cp -r " + module + " " + buildFolder + "/")
    folderModuleName = module.split("/")[-1]
    print("Module Folser: " + folderModuleName)
    buildModuleFolder = buildFolder + "/" + folderModuleName
    print("Build Module Folder: " + buildModuleFolder)
    composerPath = module+"/composer.json"
    print(composerPath)
    composerExists = os.path.exists(composerPath)
    print(composerExists)
    if composerExists == True:
        # JSON file
        f = open (composerPath, "r")
        # Reading from file
        data = json.loads(f.read())
        moduleName = data["name"]
        moduleVersion = data["version"]
        print("Magento Module Name: " + moduleName)
        print("Magento Module Version: " + moduleVersion)

        #ToDo: Change with organisation name
        moduleNameNew = moduleName.replace("magento/", organisationName + "/")
        print("Magento Fork Module Name: " + moduleNameNew)
        data["name"] = moduleNameNew

        with open(buildModuleFolder + "/composer.json", 'w') as f2:
            json.dump(data, f2, indent=4)
        packagistPackagesearch = 'https://repo.packagist.org/p2/' +  moduleName + '.json'
        f.close()

        cdCommand = "cd " + buildModuleFolder
        exec(cdCommand)
        print("CurentFolder:" + exec(cdCommand + " && pwd"))
        print(cdCommand + " && git init ")
        exec(cdCommand + " && git init ")
        ghCreateRepo = "gh repo create " + moduleNameNew + " --public --confirm"
        print(cdCommand + " && " + ghCreateRepo)
        exec(cdCommand + " && " + ghCreateRepo)

        addRemoteOriginCommand = "git remote add origin https://"+gitUser+":"+gitToken+"@github.com/" + moduleNameNew + ".git"
        print(cdCommand + " && " + addRemoteOriginCommand)
        exec(cdCommand + " && " + addRemoteOriginCommand)

        #ToDo: replace with version branch add tags 
        commitCommand = "git checkout -b master; git add . ; git commit -m 'Magento Fork initial commit'; git push -u origin master"
        print (colored(cdCommand + " && " + commitCommand, 'green'))
        exec(cdCommand + " && " + commitCommand)

        # commit module by magento version  
        ## This doesn't work becouse : Some tags were ignored because of a magento version mismatch module version in composer.json, read more.
        # commitCommand = "git checkout -b " + gitTagVersionBranch + "; git add . ; git commit -m 'Magento Fork initial commit'; git push -u origin " + gitTagVersionBranch + "; git tag " + gitTagVersionBranch + "; git push origin --tags"
        # print (colored(cdCommand + " && " + commitCommand, 'yellow'))
        # exec(cdCommand + " && " + commitCommand)

        # commit module by magento module version 
        commitCommand = "git checkout -b " + moduleVersion + "; git add . ; git commit -m 'Magento Fork initial commit'; git push -u origin " + moduleVersion + "; git tag " + moduleVersion + "; git push origin --tags"
        print(colored(cdCommand + " && " + commitCommand, 'yellow'))
        exec(cdCommand + " && " + commitCommand)

        # Create release by module version
        ghReleaseCreateCommand = "gh release create " + moduleVersion
        print (colored(ghReleaseCreateCommand, 'blue'))
        exec(cdCommand + " && " + ghReleaseCreateCommand)


        #toDo:Create new Pacakage
        # Create a package
        # This endpoint creates a package for a specific repo. Parameters username and apiToken are required. Only POST method is allowed.
        #POST https://packagist.org/api/create-package?username=[username]&apiToken=[apiToken] -d '{"repository":{"url":"[url]"}}'

        #Working example: 
        createPackageCommand = "curl -X POST 'https://packagist.org/api/create-package?username=" + packagistUser + "&apiToken=" + packagistAPIToken + "' -d '{\"repository\":{\"url\":\"https://github.com/" + moduleNameNew + "\"}}'"
        print (colored(createPackageCommand, 'green'))
        exec(createPackageCommand)
        #ToDo: Packagist update package: 
        #https://packagist.org/api/update-package?username=genaker&apiToken=API_TOKEN 
        # with a request body looking like this: {"repository":{"url":"PACKAGIST_PACKAGE_URL"}}
        
        #You can do this using curl for example:
        updatePackageCommand  =  "curl -XPOST -H'content-type:application/json' 'https://packagist.org/api/update-package?username="+ packagistUser + "&apiToken=" + packagistAPIToken + "' -d'{\"repository\":{\"url\":\"https://github.com/" + moduleNameNew + "\"}}'"
        print(colored(updatePackageCommand, 'blue'))
        exec(updatePackageCommand)
        
        ## Installation of the Git Hub linux packages required :
        # https://github.com/cli/cli/blob/trunk/docs/install_linux.md#fedora-centos-red-hat-enterprise-linux-dnf
        #print(packagistPackagesearch)
        #r = requests.get(packagistPackagesearch)
        #print(r.json())
