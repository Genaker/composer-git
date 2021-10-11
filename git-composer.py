import os
import subprocess
import glob
import re
import pprint as p
import json
import requests

os.system("python3 -V")
os.system("echo $TEST")

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

gitToken = "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"
gitUser = "Genaker"
ghCreateRepo = "gh repo create {project-name}"
for module in folders:
    print(module)

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
        print("Magento Module Name: " + moduleName)

        #ToDo: Change with organisation name
        moduleNameNew = moduleName.replace("magento/", organisationName + "/")

        data["name"] = moduleNameNew

        with open(buildModuleFolder + "/composer.json", 'w') as f2:
            json.dump(data, f2)
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
        commitCommand = "git checkout -b master; git add . ; git branch -M mastar; git commit -m 'Magento Fork initial commit'; git push -u origin master"
        print(cdCommand + " && " + commitCommand)
        exec(cdCommand + " && " + commitCommand)

        ## Installation of the Git Hub linux packages required :
        # https://github.com/cli/cli/blob/trunk/docs/install_linux.md#fedora-centos-red-hat-enterprise-linux-dnf
        #print(packagistPackagesearch)
        #r = requests.get(packagistPackagesearch)
        #print(r.json())% 
