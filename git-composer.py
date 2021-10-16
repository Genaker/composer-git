import os
import subprocess
import glob
import re
import pprint as p
import json
import requests
import time
import argparse
import base64

# requires execute: pip3 install termcolor
from termcolor import colored

def exec(command, return_code_output=False, output=True):
    start_time = time.time()
    try:
        print("CMD: " + command)
        result_output = subprocess.check_output(command, shell=True, stderr=subprocess.STDOUT)
        if output == True:
            print("Out:")
            print(str(result_output.decode()))
        return_code = 0
    except subprocess.CalledProcessError as e:
        if output == True:
            print("Error:")
            print(str(e.output.decode()))
        result_output = e.output
        return_code = e.returncode
    if return_code_output == True:
        ret = {"result_output":result_output, "return_code":return_code}
        print(ret)
        print(colored("Command Execution Time %s seconds" % str(time.time() - start_time), "magenta"))
        return ret
    else:
        print(colored("Command Execution Time %s seconds" % str(time.time() - start_time), "magenta"))
        return str(result_output.decode())

os.system("python3 -V")
os.system("echo $TEST")

parser = argparse.ArgumentParser()
parser.add_argument('-v','--version',type=str)
args = parser.parse_args()
version = args.version


result_release = exec("gh api /repos/magento/magento2/releases", output=False)
releases = json.loads(result_release)
full_generate_command = ""
magento_versions = []
for release in releases:
    magento_versions.append(release['tag_name'])
    full_generate_command += "python3 git-composer.py --version " + release['tag_name'] + "; "

print(magento_versions)
print(full_generate_command)
#exit();

if version == None:
    #Magento Release tag version
    gitTagVersionBranch = "All"
else:
    gitTagVersionBranch = version
    print("Using input version: " + version)

logf = open("./log-"+version.replace(".","_")+".txt", 'w')

logf.write("Version:" + gitTagVersionBranch + "\n")

os.system("git config core.filemode false")

# Clone Zend Framework
zend_version = "1.14.5"
only_zend = False
composer_only = False#True
clean_up = True
do_composer = True#False#True
do_clone = True#False#True


magento_source_path = "./magento2-source/"
gitCheckoutCommand = "cd " + magento_source_path + " && git checkout tags/"+gitTagVersionBranch


if do_clone == True:
    if clean_up == True:
        os.system("rm -rf " + magento_source_path)
        os.system("mkdir " + magento_source_path)
    os.system("git clone https://github.com/magento/magento2.git "+magento_source_path)
    os.system(gitCheckoutCommand)

git_tag_chechout_output = exec(gitCheckoutCommand, return_code_output=True)
print(git_tag_chechout_output['result_output'])

if git_tag_chechout_output['return_code'] == 1:
    print("This Tag (release/Version) doesn't exists")
    exit()

composer_install_cmd = "cd " + magento_source_path + " && composer install --ignore-platform-reqs"

magento_composer_folder = "magento2-composer"
if do_composer == True:
    #os.system(composer_install_cmd)

    os.system("rm -rf " + magento_composer_folder)
    composer_project = "composer create-project --repository-url=https://repo.magento.com/ magento/project-community-edition=" + gitTagVersionBranch + " "+ magento_composer_folder + " --ignore-platform-reqs --no-dev"
    os.system(composer_project)
    print("check comoser")
    #comp_rslt = exec(composer_install_cmd)
    #if "Nothing to install" not in comp_rslt:
        #print("composer test NOT passed check something")
        #exit()


Public_Key = "7bb8d7e839355a2542ab3f37619cfa0e"
Private_Key = "09d781290a5837848a597cee91678d8c"

message_bytes = Public_Key+":"+Private_Key
base64 = base64.b64encode(message_bytes.encode('utf-8'))
print(base64)

magento_packagist_providers = "curl -s -H 'Authorization: Basic "+str(base64.decode('ascii'))+"'  https://repo.magento.com/packages.json"
providers_json = exec(magento_packagist_providers)
providers_json = json.loads(providers_json)

packages_ce_sha356 = providers_json['provider-includes']['p/provider-ce$%hash%.json']['sha256']
packages_magento_url = "curl -s -H 'Authorization: Basic "+str(base64.decode('ascii'))+"' https://repo.magento.com/p/provider-ce%24"+packages_ce_sha356+".json"
packages_json = exec(packages_magento_url, output=False)
packages_json = json.loads(str(packages_json))['providers']


metapackage_crap = ['magento/product-community-edition']

package_url = "https://repo.magento.com/p/{name}%24{sha}.json"
packages_magento_repo = {}
for name, value in  packages_json.items():
    #print(name)
    for crap in metapackage_crap:
        if crap == name:
            packages_magento_repo.update({name: value})
            url = package_url.format(name=name,sha=value['sha256'])

            r=requests.get(url, headers={"Authorization": "Basic "+str(base64.decode('ascii'))})
            packages2_json = r.json()['packages']
            print("ALL")
            package = packages2_json[name][gitTagVersionBranch]
           #for version in package:
            print(package["dist"]['url'])
            print(package["name"])
            del package["dist"]
            p.pprint(package)

    

            cache_folder = "./magento-composer-cache"
            os.system("mkdir -p "+cache_folder+"/"+name)

            # download the file contents in binary format
            #r = requests.get(package["dist"]['url'], headers={"Authorization": "Basic "+str(base64.decode('ascii'))})

            #zip_file = cache_folder+"/"+name+"/module.zip"
            #download = "curl  -H 'Authorization: Basic "+ str(base64.decode('ascii'))+"' " + package["dist"]['url'] + " --output " + zip_file 
            
            #print(download)

            #exec(download)
            composer_metapackage_save_path = cache_folder+"/"+name+"/composer.json"
            open(composer_metapackage_save_path, "w").write(json.dumps(package))
            # open method to open a file on your system and write the contents

            #packages3_json = r
            packages_magento_repo.update({name: {'url':url, 'version': packages2_json}})
       #packages_magento_repo.update(packages_json)

os.system("composer config --global --list | grep cache-dir")

composer_crap = ['magento2-base','project-community-edition', 'composer-root-update-plugin']

composer_cache_folder = "/home/genaker/.cache/composer/files/magento/"
composer_folders = []

for folder in composer_crap:
    composer_folders.append(composer_cache_folder+folder+"/")
    os.system("echo A | unzip " + composer_cache_folder+folder+ "/*.zip -d "+composer_cache_folder+folder+"/")
    os.system("echo A | rm  " + composer_cache_folder+folder+ "/*.zip")

print("composer test passed")

clean_up_zend = False
if clean_up_zend == True:
    os.system("rm -rf "  + magento_source_path+"/lib/internal/Magento/zendframework")
os.system("git clone https://github.com/magento/zf1 "+magento_source_path+"/lib/internal/Magento/zendframework")
os.system("cd "+magento_source_path+"/lib/internal/Magento/zendframework && git checkout tags/"+zend_version)
os.system("rm -rf  "+magento_source_path+"/lib/internal/Magento/zendframework/.git")


logf.write("cd "+magento_source_path+" && git checkout tags/"+gitTagVersionBranch+"\n")

path = magento_source_path+"/app/code/Magento/"

os.system(cache_folder+"/magento/*.zip")
app_folders = glob.glob(path + '*')
composer_meta_folder =  glob.glob( cache_folder+"/magento/*")
frontend_theme_folder = glob.glob(magento_source_path+"/app/design/frontend/Magento/*")
backend_theme_folder = glob.glob(magento_source_path+"/app/design/adminhtml/Magento/*")
language_folder = glob.glob(magento_source_path+"/app/i18n/Magento/*")
magento_framework_folder = glob.glob(magento_source_path+"/lib/internal/Magento/*")

folders = app_folders + frontend_theme_folder + magento_framework_folder + language_folder + backend_theme_folder + composer_folders

if only_zend is True:
    folders = magento_framework_folder

if composer_only is True:
    folders = composer_folders + composer_meta_folder

#ToDo: add another folders with the composer packages. Done 
# etc...
print(folders)
#exit()
n = 1;

print("Test gh cli:")
checkGitHubCli = exec("gh")

if "not found" in checkGitHubCli:
    print("Command 'gh' is required and not found!!!")
    print("Visit: to instll: https://cli.github.com/manual/installation")
    exit()

print(folders)
# Folder to copy modules to
buildFolder = "magento-modules-separate"
# Name of the gitHub organisation or account
# (account is not tested by doc it shuld be empty but baybe it will works)
organisationName = "magenxcommerce"
exec("rm -rf " + buildFolder)
exec("mkdir -p " + buildFolder)

#set your keys and users
# set cretentials: export PACKAGIST_TOKEN=M7W** && export PACKAGIST_USER=genaker && export GITHUB_TOKEN="****" && export GITHUB_USER="Genaker"

if "PACKAGIST_TOKEN" in os.environ:
    packagistAPIToken = os.environ.get("PACKAGIST_TOKEN")
else:
    packagistAPIToken = "M7W**"
if "PACKAGIST_USER" in os.environ:
    packagistUser = os.environ.get("PACKAGIST_USER")
else:
    packagistUser = "genaker"
if "GITHUB_TOKEN" in os.environ:
    gitToken = os.environ.get("GITHUB_TOKEN")
else:
    gitToken = "ghp_UHA4aDn**"
if "GITHUB_USER" in os.environ:
    gitUser = os.environ.get("GITHUB_USER")
else:
    gitUser = "Genaker"

#The value of the GITHUB_TOKEN environment variable is being used for authentication.
os.system("echo "+ gitToken +" | gh auth login --with-token")
print("Check GitHub Auth")
gitAuthStatus = exec("gh auth status")
if "Logged in to github.com as" not in gitAuthStatus:
    print("Git Hub Credetials Error!!!")
    exit()


list_packages_by_organization_url = "https://packagist.org/packages/list.json?vendor="+organisationName
r = requests.get(list_packages_by_organization_url)
print("List packages by organization [{organisationName}]".format(organisationName=organisationName))
packages = r.json()
packages = packages["packageNames"]

for package in packages:
    print(package)

organisationForAPI = "orgs/" + organisationName
#Check if it is user and not org
#organisationForAPI="user"
gitAuthHaeder = {gitUser: gitToken}
list_git_organization_repositories_url = "https://api.github.com/" +organisationForAPI+"/repos?per_page=1000"
r = requests.get(list_git_organization_repositories_url, gitAuthHaeder)
repos = r.json()
#print(repos)

print(colored("Repos of the organisation["+organisationName+"]","green"))
gitReposetories = []
for reposetory in repos:
    print(reposetory["full_name"])
    gitReposetories.append(reposetory["full_name"])

#operation is slow for test it is better not to use it 
updatePackagistPackage = True;
gitPushToMaster = False;
modules_count = str(len(folders))

for module in folders:
    module_start_time = time.time()
    module = module.replace("//","/")
    # module actualy is a magento folder like :./magento2/app/code/Magento/Paypal
    moduleStartStr = "\n=====[" + module + "]("+str(n)+"/"+modules_count+")========>\n"
    print(colored(moduleStartStr, 'red'))
    logf.write(moduleStartStr)
    n+=1

    # Copy a single module to separate build folder
    exec("cp -r " + module + " " + buildFolder + "/")
    #get the last part of the module name 
    #if "/.cache/composer/" in module:
    #else:
    folderModuleName = module.split("/")[-1]
    if folderModuleName == "":
        folderModuleName = module.split("/")[-2]
    print("Module Folder: " + folderModuleName)
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

        if "version" not in data:
            print("composer version is not set try to use release version")
            
            # set Hardcoded version for Zend framework
            if "zendframework" in folderModuleName:
                data["version"] = zend_version
        
        moduleVersion = data["version"]


        print("Magento Module Name: " + moduleName)
        print("Magento Module Version: " + moduleVersion)

        #Change Magento name with organisation name
        moduleNameNew = moduleName.replace("magento/", organisationName + "/")
        print("Magento Fork Module Name: " + moduleNameNew)
        data["name"] = moduleNameNew

        print("Print composer data")
        if "replace" not in data:
            data["replace"] = {}
        p.pprint(data["replace"])
        #replace pakages
        for package in  data["require"]:
            p.pprint(package)
        data["replace"].update({moduleName: "*"}) #"self.version"}) #"*"})
        p.pprint(data["replace"])
        ##exit()

        logf.write(module +" ----> "+moduleNameNew+"\n")
        # save new composer name to buid module folder composer.json
        with open(buildModuleFolder + "/composer.json", 'w') as f2:
            json.dump(data, f2, indent=4)
        # potentially we can check if the package exists.
        packagistPackageCheck = 'https://repo.packagist.org/p2/' +  moduleNameNew + '.json'
        f2.close()

        # cd to the masgento buildModuleFolder shuld be appended to the all commands 
        cdCommand = "cd " + buildModuleFolder
        exec(cdCommand)
        print("CurrentFolder:" + exec(cdCommand + " && pwd"))
        
        #init git repo in the magento module build folder
        print(cdCommand + " && git init ")
        exec(cdCommand + " && git init ")

        # fetch remote
        print(cdCommand + " && git fetch ")
        os.system(cdCommand + " && git fetch ")

        # outdated now we are cheking gitReposetories list 
        #Check if repo exists
        #ghAPIURL = "https://api.github.com/repos/" + moduleNameNew
        #print("Check if repo " + ghAPIURL + " exists")
        #r = requests.get(ghAPIURL, gitAuthHaeder)
        #print(r.json())

        if moduleNameNew in gitReposetories:
            print("Repo " + moduleNameNew + " Exists")

        # Create a package operation is slow
        # This endpoint creates a package for a specific repo. Parameters username and apiToken are required. Only POST method is allowed.
        #POST https://packagist.org/api/create-package?username=[username]&apiToken=[apiToken] -d '{"repository":{"url":"[url]"}}'

        if moduleNameNew not in gitReposetories:
            #Create gitHub repo. If it is exist it will return error. 
            ghCreateRepo = "gh repo create " + moduleNameNew + " --public --confirm"
            print(cdCommand + " && " + ghCreateRepo)
            exec(cdCommand + " && " + ghCreateRepo)
            logf.write("GitHub reposetory created:" + moduleNameNew + "\n")

        # add new remote origin to the magento module git local repo 
        addRemoteOriginCommand = "git remote add origin https://"+gitUser+":"+gitToken+"@github.com/" + moduleNameNew + ".git"
        print(cdCommand + " && " + addRemoteOriginCommand)
        exec(cdCommand + " && " + addRemoteOriginCommand)
        
        #ToDo: Override remote branch 
        overwriteRemote = True

        # Commit to the master the latest version
        # ToDo: check it is id the lates version
        if gitPushToMaster == True:
            print("Push Magento master branch")
            commitCommand = "git checkout -b master; git add . ; git commit -m 'Magento OS Fork version " + gitTagVersionBranch + " commit'; git push  -u origin master"
            print (colored(cdCommand + " && " + commitCommand, 'green'))
            exec(cdCommand + " && " + commitCommand)

        # commit module by magento version  
        ## Magento version tag doesn't work becouse of: Some tags were ignored because of a magento version mismatch module version in composer.json, read more.
        print("Push Magento version branch")
        checkGitBranchCommand  = "git branch -l " + gitTagVersionBranch
        print(colored(cdCommand + " && " + checkGitBranchCommand, 'blue'))
        output = exec(cdCommand + " && " + checkGitBranchCommand)
        if gitTagVersionBranch not in output:
            commitCommand = "git checkout -b " + gitTagVersionBranch + "; git add . ; git commit -m 'Magento Fork initial commit'; git push -u origin " + gitTagVersionBranch
            print (colored(cdCommand + " && " + commitCommand, 'yellow'))
            exec(cdCommand + " && " + commitCommand)
            logf.write("GitHub magento version branch created:" + gitTagVersionBranch + "\n")
        else:
            print("Git magento release branch " + gitTagVersionBranch + " already exists")
            logf.write("Git magento release branch " + gitTagVersionBranch + " already exists\n")

        # commit modile by 
        print("Push module version branch")
        checkGitBranchCommand  = "git branch -l " + moduleVersion
        print(colored(cdCommand + " && " + checkGitBranchCommand, 'blue'))
        output = exec(cdCommand + " && " + checkGitBranchCommand)

        if moduleVersion not in output or overwriteRemote == True:
            
            if overwriteRemote == True:
                os.system(cdCommand + " && git checkout -b placeholder && git push origin placeholder")
                os.system("gh api repos/{moduleNameNew} --method PATCH --field 'default_branch=placeholder'".format(moduleNameNew = moduleNameNew))
                print("Delete Remote TAg Override")
                os.system(cdCommand + " && git tag -d "+moduleVersion+" && git push origin :refs/tags/" + moduleVersion)
                print("Delete Remote Branch Override")
                os.system(cdCommand + " && git branch -d "+moduleVersion+" && git push origin -f --delete "+moduleVersion)

            commitCommand = "git checkout -b " + moduleVersion + "; git add . ; git commit -m 'Magento OS Fork commit'; git push -f -u origin " + moduleVersion
            print(colored(cdCommand + " && " + commitCommand, 'yellow'))
            exec(cdCommand + " && " + commitCommand)
            logf.write("GitHub module " + moduleNameNew + " version branch created:" + moduleNameNew + "\n")
        else:
            print("Git module versio branch " + moduleVersion + " already exists")
            logf.write("Git module " + moduleNameNew + " versio branch " + moduleVersion + " already exists\n")

        # commit module by module version with the tags

        #check if Tag already exist
        checkGitTagCommand  = "git tag -l " + moduleVersion
        print(colored(cdCommand + " && " + checkGitTagCommand, 'blue'))
        tagOutput = exec(cdCommand + " && " + checkGitTagCommand)
        if moduleVersion not in tagOutput  or overwriteRemote == True:
            commitCommand = "git tag " + moduleVersion + "; git push origin -f --tags"
            print(colored(cdCommand + " && " + commitCommand, 'yellow'))
            exec(cdCommand + " && " + commitCommand)

            # In some cases we need recreate tags: https://gist.github.com/danielestevez/2044589

            # Create release by module version
            ghReleaseCreateCommand = "gh release create " + moduleVersion
            print (colored(ghReleaseCreateCommand, 'blue'))
            exec(cdCommand + " && " + ghReleaseCreateCommand)
        else:
            print("Tag " + moduleVersion + " already exists")


        #Old code we have better one now -> check packages list
        print("Check if package exists")
        #r = requests.get(packagistPackageCheck)
        #print(r.json())

        # Create a package operation is slow
        # This endpoint creates a package for a specific repo. Parameters username and apiToken are required. Only POST method is allowed.
        #POST https://packagist.org/api/create-package?username=[username]&apiToken=[apiToken] -d '{"repository":{"url":"[url]"}}'

        if moduleNameNew not in packages: #r.status_code == 404:
            #Create new package: 
            createPackageCommand = "curl -X POST 'https://packagist.org/api/create-package?username=" + packagistUser + "&apiToken=" + packagistAPIToken + "' -d '{\"repository\":{\"url\":\"https://github.com/" + moduleNameNew + "\"}}'"
            print (colored(createPackageCommand, 'green'))
            exec(createPackageCommand)
            logf.write("Pakage " + moduleNameNew + " created: https://packagist.org/" + moduleNameNew + " \n")
        else:
            logf.write("Pakage " + moduleNameNew + " already exist \n")

            
        # Packagist update package: 
        #https://packagist.org/api/update-package?username=genaker&apiToken=API_TOKEN 
        # with a request body looking like this: {"repository":{"url":"PACKAGIST_PACKAGE_URL"}}
        if updatePackagistPackage == True:
            updatePackageCommand  =  "curl -XPOST -H'content-type:application/json' 'https://packagist.org/api/update-package?username="+ packagistUser + "&apiToken=" + packagistAPIToken + "' -d'{\"repository\":{\"url\":\"https://github.com/" + moduleNameNew + "\"}}'"
            print(colored(updatePackageCommand, 'blue'))
            update_output = exec(updatePackageCommand)
            logf.write("Pakage " + moduleNameNew + " updated \n")
        
        print(colored("\nModule Processing Time %s seconds" % str(time.time() - module_start_time), "magenta"))
        
        ## Installation of the Git Hub linux packages required :
        # https://github.com/cli/cli/blob/trunk/docs/install_linux.md#fedora-centos-red-hat-enterprise-linux-dnf
        #print(packagistPackagesearch)
        #r = requests.get(packagistPackagesearch)
        #print(r.json())
    else:
        print("Crytical Error: folder " + module + " doen't have Composer.json file")
        exit()
logf.write("Done!!")
logf.close();
