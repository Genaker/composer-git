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
import urllib
# requires execute: pip3 install termcolor
from termcolor import colored


def main():
    sh = exec

    sh("python34 -V")

    os.system("echo $TEST")

    parser = argparse.ArgumentParser()
    parser.add_argument('-v','--version',type=str)
    # do only composer packages metadata,cache and vendor
    parser.add_argument('-c','--composer', action='store_true')
    # test run argument 
    parser.add_argument('-t','--test',  dest='test', action='store_true')
    parser.set_defaults(test=False)
    args = parser.parse_args()

    version = args.version
    composer = args.composer

    try:
        result_release = exec("gh api /repos/magento/magento2/releases", debug=False)
        releases = json.loads(result_release)
    except json.decoder.JSONDecodeError:
        print("Fetch GitHub API data error. Check Credentials.")
        exit()

    full_generate_command = ""
    magento_versions = []
    for release in releases:
        magento_versions.append(release['tag_name'])
        full_generate_command += "python3 git-composer.py --version " + release['tag_name'] + " -c ; "

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
    composer_only = composer #False#True
    clean_up = True
    do_composer = True
    do_clone = True
    do_msi = False

    if args.test is True:
        do_composer = False
        do_clone = False

    #Define All folder in one place
    magento_source_path = "./magento2-source/"
    msi_source_path = "./magento2-msi/"
    gitCheckoutCommand = "cd " + magento_source_path + " && git checkout tags/"+gitTagVersionBranch
    cache_folder = "./magento-composer-cache"
    composer_cache_folder = "/home/genaker/.cache/composer/files/magento/"
    magento_composer_folder = "./magento2-composer"

    if do_clone == True:
        if clean_up == True:
            os.system("rm -rf " + magento_source_path)
            os.system("mkdir " + magento_source_path)
            os.system("rm -rf " + msi_source_path)
            os.system("mkdir " + msi_source_path)
            os.system("rm -rf "+ cache_folder)
            os.system("mkdir " + cache_folder)

        print("Clone Magento Main Repo")
        exec("git clone  --branch "+gitTagVersionBranch+" --depth 1  --single-branch  https://github.com/magento/magento2.git "+magento_source_path, system=True)

        if do_msi == True:
            print("Clone Magento MSI Repo")
            exec("git clone https://github.com/magento/inventory "+msi_source_path, system=True)

    ret_code = exec(gitCheckoutCommand,return_code=True)
    if ret_code['return_code'] == 1:
        os.system("rm -rf " + magento_source_path)
        exec("git clone  --branch "+gitTagVersionBranch+" --depth 1  --single-branch  https://github.com/magento/magento2.git "+magento_source_path, system=True)
        exec(gitCheckoutCommand,system=True,return_code=True)

    git_tag_chechout_output = exec(gitCheckoutCommand, return_code=True)
    print(git_tag_chechout_output['result_output'])

    if git_tag_chechout_output['return_code'] == 1:
        print("Error: This Tag (release/Version) doesn't exists")
        exit()

    composer_install_cmd = "cd " + magento_source_path + " && composer install --ignore-platform-reqs"


    if do_composer == True:
        #os.system(composer_install_cmd)
        ##os.system("rm -rf " + magento_composer_folder)
        os.system("rm -rf " + magento_composer_folder)
        composer_project = "composer create-project --repository-url=https://repo.magento.com/ magento/project-community-edition=" + gitTagVersionBranch + " "+ magento_composer_folder + " --ignore-platform-reqs --no-dev"
        print("Composer create project. Please wait ...")
        exec(composer_project,debug=False)
        #exit();
        #os.system(composer_project)
        print("check comoser")
        #comp_rslt = exec(composer_install_cmd)
        #if "Nothing to install" not in comp_rslt:
            #print("composer test NOT passed check something")
            #exit()

    folders_keep = ['generated','app/design/frontend/Magento','app/design/adminhtml/Magento','app/etc',
        'lib/web/less','lib/web/knockoutjs','lib/web/jquery','lib/web/images','lib/web/i18n','lib/web/fotorama',
        'lib/web/extjs','lib/web/fonts','lib/web/chartjs','lib/web/css','lib/internal','lib/internal/LinLibertineFont',
        'lib/internal/GnuFreeFont','dev/tests/utils','dev/tests/api-functional/_files',
        # not a folder 'bin/magento',
        'dev/tests/unit','dev/tests/unit/framework','dev/tests/unit/tmp','dev/tests/utils','dev/tools','dev/tests/static',
        'dev/tests/static/tmp','dev/tests/static/testsuite','dev/tests/static/testsuite/Magento','dev/tests/static/framework',
        'dev/tests/setup-integration','dev/tests/js','dev/tests/integration','dev/tests/integration/tmp','dev/tests/integration/_files',
        'dev/tests/integration/bin','dev/tests/integration/etc','dev/tests/integration/framework','dev/tests/acceptance',
        'dev/tests/integration/testsuite','dev/tests/integration/testsuite/Magento',
        'lib/web/lib','lib/web/mage','lib/web/magnifier','lib/web/modernizr','lib/web/prototype','lib/web/requirejs','lib/web/scriptaculous',
        'lib/web/tiny_mce_4','pub/media','pub/media/import','pub/media/sitemap','pub/media/customer_address','pub/media/custom_options',
        'pub/errors','pub/opt','setup','phpserver','lib/web','lib/web/varien','lib/web/css','dev/tools','dev/tests/static']

    lock_data = get_from_composerlock(magento_composer_folder)

    #metapackages
    metapackage_crap = ['magento/product-community-edition','magento/page-builder','magento/security-package']

    # Packages exracted from the composer cache 
    composer_crap = ['project-community-edition','framework-bulk','framework-message-queue', 'framework-amqp', 'composer-root-update-plugin','composer']
    vendor_crap = ['magento/magento-composer-installer', 'magento/magento2-base', 'magento/module-paypal-recaptcha', 'magento/composer-dependency-version-audit-plugin']
    
    page_builder_metapackage_data = []
    security_package_metapackage_data = []

    if 'magento/page-builder' in lock_data:
        page_builder_metapackage_data = lock_data['magento/page-builder']['require'].keys()
    if 'magento/security-package' in lock_data:
        security_package_metapackage_data = lock_data['magento/security-package']['require'].keys()

    vendor_crap = vendor_crap + list(page_builder_metapackage_data)
    vendor_crap = vendor_crap + list(security_package_metapackage_data)
    #ToDo: extract MSI from the magento
    msi_composer_crap = []
    
    packages_magento_repo = packageist_repo_get(metapackage_crap,gitTagVersionBranch,cache_folder,lock_data)
    #p.pprint(lock_data)

    composer_folders = get_from_composer_cache(composer_crap, composer_cache_folder)

    vendor_to_git_folders = get_from_vendor(vendor_crap,magento_composer_folder)

    print("composer test passed")

    clean_up_zend = True
    print("Do Zenf Framework stuff")
    if clean_up_zend == True:
        os.system("rm -rf " + magento_source_path+"/lib/internal/Magento/zendframework")
        os.system("rm -rf /home/genaker/.cache/composer/files/magento/magento-composer-installer/")
    os.system("git clone --depth 1  https://github.com/magento/zf1 "+magento_source_path+"/lib/internal/Magento/zendframework")
    os.system("cd "+magento_source_path+"/lib/internal/Magento/zendframework && git checkout tags/"+zend_version)
    os.system("rm -rf  "+magento_source_path+"/lib/internal/Magento/zendframework/.git")

    print("Change magento branch/tag to version " + gitTagVersionBranch)

    logf.write("cd "+magento_source_path+" && git checkout tags/"+gitTagVersionBranch+"\n")

    path = magento_source_path+"/app/code/Magento/"

    os.system(cache_folder+"/magento/*.zip")
    app_folders = glob.glob(path + '*')
    composer_meta_folder =  glob.glob( cache_folder+"/magento/*")
    frontend_theme_folder = glob.glob(magento_source_path+"/app/design/frontend/Magento/*")
    backend_theme_folder = glob.glob(magento_source_path+"/app/design/adminhtml/Magento/*")
    language_folder = glob.glob(magento_source_path+"/app/i18n/Magento/*")
    magento_framework_folder = glob.glob(magento_source_path+"/lib/internal/Magento/*")
    msi_folder = []
    if do_msi == True:
        msi_folder = glob.glob(msi_source_path+"/*")

    folders = vendor_to_git_folders + composer_folders + composer_meta_folder + msi_folder + app_folders + frontend_theme_folder + magento_framework_folder + language_folder + backend_theme_folder 

    if only_zend is True:
        folders = magento_framework_folder

    if composer_only is True:
        folders = composer_folders + composer_meta_folder + vendor_to_git_folders

    #ToDo: add another folders with the composer packages. Done 
    # etc...
    #print(folders)
    #exit()
    n = 1;

    print("Test gh cli:")
    checkGitHubCli = exec("gh", debug=False)

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
    p.pprint(gitAuthStatus)
    if "Logged in to github.com as" not in gitAuthStatus:
        print("Git Hub Credetials Error!!!")
        exit()


    list_packages_by_organization_url = "https://packagist.org/packages/list.json?vendor="+organisationName
    r = requests.get(list_packages_by_organization_url)
    print("List packages by organization [{organisationName}]".format(organisationName=organisationName))
    packages = r.json()
    packages = packages["packageNames"]

    for package in packages:
        package

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
        
        print("Magento Version/Tag: " + gitTagVersionBranch)
        print("Module Folder: " + folderModuleName)
        buildModuleFolder = buildFolder + "/" + folderModuleName
        print("Build Module Folder: " + buildModuleFolder)
        composerPath = module+"/composer.json"
        print("Composer Module Path: "+composerPath)
        composerExists = os.path.exists(composerPath)
        print("Composer Exists:"+str(composerExists))

        if 'magento-composer-installer' in buildModuleFolder:
            sed(buildModuleFolder+'/src/MagentoHackathon/Composer/Magento/DeployManager.php')

        if 'magento2-base' in buildModuleFolder:

            for folder in folders_keep:
                print(folder)
                os.system("touch "+buildModuleFolder+"/"+folder+"/.gitkeep")

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

            if "version" not in data:
                if moduleName not in lock_data:
                    print("Error no verson")
                    exit()
                data["version"] = lock_data[moduleName]['version']
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
            #p.pprint(data["replace"])
            #replace pakages
            p.pprint(data["require"])
            if "repositories" in data:
                #del data["repositories"]
                data

            replace_require_packages = True
            exclude_from_require_replace = ['magento/composer-dependency-version-audit-plugin', 'sebastian/phpcpd', 'magento/inventory-composer-metapackage','magento/inventory-metapackage','magento/adobe-ims', 'yotpo/magento2-module-yotpo-reviews-bundle', 'magento/adobe-stock-integration', ]
            # only public packages will works 
            left_magento_package = ['magento/security-package', 'magento/google-shopping-ads', 'magento/page-builder']#['magento/composer']
            
            if replace_require_packages == True:
                new_packges = replace_composer_require_packages(data, exclude_from_require_replace, left_magento_package)
                data["require"]=new_packges
                p.pprint(data["require"])
                data["replace"].update({moduleName: "*"}) #"self.version"}) #"*"})
        
            replace_suggest_packages = True

            if replace_suggest_packages == True:
                new_suggest=replace_composer_suggest_packages(data)
                data["suggest"]=new_suggest
            #exit()

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
            print(cdCommand + " && git fetch")
            os.system(cdCommand + " && git fetch -q")

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
            exec(cdCommand+" && git fetch -q")
            #ToDo: Override remote branch 
            overwriteRemote = True

            # Commit to the master the latest version
            # ToDo: check it is id the lates version
            if gitPushToMaster == True:
                print("Push Magento master branch")
                commitCommand = "git checkout -b master; git add . -f; git commit -q -m 'Magento OS Fork version " + gitTagVersionBranch + " commit'; git push  -u origin master "
                print (colored(cdCommand + " && " + commitCommand, 'green'))
                exec(cdCommand + " && " + commitCommand)

            # commit module by magento version  
            ## Magento version tag doesn't work becouse of: Some tags were ignored because of a magento version mismatch module version in composer.json, read more.
            push_magento_version_module_branch = False
            if push_magento_version_module_branch == True:
                print("Push Magento version branch")
                # branches shuldn't intersects with the tags. It is aditional feture 
                branch_name = "m"+gitTagVersionBranch
                checkGitBranchCommand  = "git branch -l " + branch_name
                print(colored(cdCommand + " && " + checkGitBranchCommand, 'blue'))
                output = exec(cdCommand + " && " + checkGitBranchCommand)
                if branch_name not in output or overwriteRemote == True:
                    
                    if overwriteRemote == True:
                        os.system(cdCommand + " && git checkout -b default && git push origin default")
                        os.system("gh api repos/{branch_name} --method PATCH --field 'default_branch=default' >/dev/null".format(branch_name = branch_name))
                        print("Delete Remote Branch for Override")
                        os.system(cdCommand + " && git branch -d "+branch_name+" && git push origin -f --delete "+branch_name)

                    commitCommand = [
                        "git checkout -b " + branch_name,
                        "git add . -f",
                        "git commit -q -m 'Magento OS Fork version'",
                        "git push origin " + gitTagVersionBranch + " -f"
                    ]

                    print (colored(cdCommand + " && " + str.join('+',commitCommand), 'yellow'))
                    exec(commitCommand,cd=buildModuleFolder)
                    logf.write("GitHub magento version branch created:" + branch_name + "\n")
                else:
                    print("Git magento release branch " + branch_name + " already exists")
                    logf.write("Git magento release branch " + branch_name + " already exists\n")

            # commit modile by 
            print("Push module version branch")
            checkGitBranchCommand  = "git branch -l " + moduleVersion
            print(colored(cdCommand + " && " + checkGitBranchCommand, 'blue'))
            output = exec(cdCommand + " && " + checkGitBranchCommand)

            if moduleVersion not in output or overwriteRemote == True:
                push_module_version(moduleNameNew,moduleVersion,cdCommand,buildModuleFolder,overwriteRemote)
                logf.write("GitHub module " + moduleNameNew + " version branch created:" + moduleNameNew + "\n")
            else:
                print("Git module versio branch " + moduleVersion + " already exists")
                logf.write("Git module " + moduleNameNew + " versio branch " + moduleVersion + " already exists\n")

            # commit module by module version with the tags

            #check if Tag already exist
            checkGitTagCommand  = "git tag -l " + moduleVersion
            print(colored(cdCommand + " && " + checkGitTagCommand, 'blue'))
            tagOutput = exec(cdCommand + " && " + checkGitTagCommand)
            if moduleVersion not in tagOutput or overwriteRemote == True:
                commitCommand = "git add . -f; git commit -q -m 'Fork Tag' ; git tag " + moduleVersion + "; pwd; git push origin -f --tags"
                print(colored(cdCommand + " && " + commitCommand, 'yellow'))
                exec(cdCommand + " && " + commitCommand)
                
                # In some cases we need recreate tags: https://gist.github.com/danielestevez/2044589
                if overwriteRemote == True:
                    ghReleaseDeleteCMD = "gh release delete " + moduleVersion + " -y"
                    print (colored("Delete Release: " + ghReleaseDeleteCMD, 'blue'))
                    exec(cdCommand + " && " + ghReleaseDeleteCMD,system=True)
                
                # Create release by module version
                ghReleaseCreateCommand = "gh release create " + moduleVersion + " -t 'Release "+moduleVersion+"' -n ''"
                print (colored("Create release:"+ghReleaseCreateCommand, 'blue'))
                exec(cdCommand + " && " + ghReleaseCreateCommand, system=True)
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
    print("D@ne!!!")
    logf.write("Done!!")
    logf.close();


def get_from_vendor(vendor,magento_composer_folder):
    vendor_to_git_folders = []
    magento_vendoe_folder = magento_composer_folder+'/vendor/'
    for pakage in vendor:
        file_exists = os.path.exists(magento_vendoe_folder+pakage)
        if file_exists == True:
            vendor_to_git_folders.append(magento_vendoe_folder+pakage)
        else:
            print("Vendor ["+pakage+"] doesn't exists")
            #exit()
    return vendor_to_git_folders

def packageist_repo_get(metapackage_crap, gitTagVersionBranch, cache_folder, lock_data):
    Public_Key = "7bb8d7e839355a2542ab3f37619cfa0e"
    Private_Key = "09d781290a5837848a597cee91678d8c"

    message_bytes = Public_Key+":"+Private_Key
    b64 = base64.b64encode(message_bytes.encode('utf-8'))
    print(b64)

    magento_packagist_providers = "curl -s -H 'Authorization: Basic "+str(b64.decode('ascii'))+"'  https://repo.magento.com/packages.json"
    providers_json = exec(magento_packagist_providers)
    providers_json = json.loads(providers_json)

    packages_ce_sha356 = providers_json['provider-includes']['p/provider-ce$%hash%.json']['sha256']
    packages_magento_url = "curl -s -H 'Authorization: Basic "+str(b64.decode('ascii'))+"' https://repo.magento.com/p/provider-ce%24"+packages_ce_sha356+".json"
    packages_json = exec(packages_magento_url, debug=False)
    packages_json = json.loads(str(packages_json))['providers']

    package_url = "https://repo.magento.com/p/{name}%24{sha}.json"
    packages_magento_repo = {}
    for name, value in  packages_json.items():
        #print(name)
        for crap in metapackage_crap:
            if crap == name:
                packages_magento_repo.update({name: value})
                url = package_url.format(name=name,sha=value['sha256'])

                r=requests.get(url, headers={"Authorization": "Basic "+str(b64.decode('ascii'))})
                packages2_json = r.json()['packages']
                print("ALL Packages:")

                #p.pprint(packages2_json[name])
                if name in packages2_json and name in lock_data:
                    if gitTagVersionBranch in packages2_json[name]:
                        package = packages2_json[name][gitTagVersionBranch]
                    else:
                        module_version_from_lock = lock_data[name]['version']
                        package = packages2_json[name][module_version_from_lock]
                        #p.pprint(package)
                else:
                    print(colored("CONTINUE no packages found",'red'))
                    continue
                #for version in package:
                #print(package["dist"]['url'])
                #print(package["name"])
                del package["dist"]
                #p.pprint(package)
                #MSI if in the main metapackage
    
                os.system("mkdir -p "+cache_folder+"/"+name)

                composer_metapackage_save_path = cache_folder+"/"+name+"/composer.json"
                open(composer_metapackage_save_path, "w").write(json.dumps(package))
                # open method to open a file on your system and write the contents

                packages_magento_repo.update({name: {'url':url, 'version': packages2_json}})
    os.system("composer config --global --list | grep cache-dir")
    return packages_magento_repo

    #@alias_param("debug", alias='outpus')
def exec(commands,return_code=False,dev_null=False,system=False,wait=True,cd='',exception=False,debug=True):
    results = []
    if type(commands) == list:
        commands
        print(colored("Multiple commands: " + str.join('; + ', commands), 'yellow'))
    else: commands = [commands]

    if cd != '':
        cd = 'cd ' + cd + ' && '
    
    for command in commands:
        start_time = time.time()
        if dev_null == True:
            dev_null = ' 1> /dev/null '
        else: dev_null = ''
        
        if wait == False:
            wait = ' & '
        else: wait = ''

        command = cd + command + dev_null + wait

        if debug == True:
            print("CMD: " + command)

        if system == True:
            os.system(command)
            return
        
        try:
            result = subprocess.run(command, shell=True, check=True, capture_output=True, text=True)
            #Sometimes Stdout is emty, result code is 0 and stderr has outout
            if result.stdout.strip() == '' and result.stderr.strip() != '':
                result_output = result.stderr.strip()
            else:
                result_output = result.stdout.strip()
            if debug == True:
                print("Out:")
                print(result_output)
                #p.pprint(result)
            cmd_return_code = result.returncode
        except subprocess.CalledProcessError as e:
            if debug == True:
                print("Error: code "+str(e.returncode))
                print(str(e.stderr.strip()))
            if exception == True:
                return e
            result_output = e.stderr.strip()
            cmd_return_code = e.returncode
        if return_code == True:
            results.append({"result_output":str(result_output), "return_code":cmd_return_code})
        else:
            results.append(str(result_output))
        
        if debug == True:
            print(colored("Command Execution Time %s seconds\n----------------" % str(time.time() - start_time), "magenta"))

    #if it is a single cmmand return result not a list 
    if len(commands) == 1:
        return results[0]
    return results

def get_from_composer_cache(composer_crap, composer_cache_folder):
    composer_folders = []

    for i,folder in enumerate(composer_crap):
        file_exists = os.path.exists(composer_cache_folder+folder)
        if file_exists == True:
            composer_folders.append(composer_cache_folder+folder+"/")
            os.system("echo A | unzip " + composer_cache_folder+folder+ "/*.zip -d "+composer_cache_folder+folder+"/  > /dev/null")
            os.system("echo A | rm  " + composer_cache_folder+folder+ "/*.zip")
            if 'magento2-base' in folder:
                print("base")
                # remove stupid tests from magento
                # os.system("echo A | rm " + composer_cache_folder+folder+ "/dev/tests/ ")
        else:
            print("composer package "+folder+" File not found")
            exit()
    return composer_folders

def get_from_composerlock(magento_composer_folder):
    lock_data = {}
    composer_lock = json.loads(open(magento_composer_folder+'/composer.lock', "rt").read())
    for pack in composer_lock["packages"]:
        lock_data.update({pack['name']:{}})
        lock_data[pack['name']].update({'version': pack['version']})
        if "type" in pack:
            lock_data[pack['name']].update({'type': pack['type']})
        if "require" in pack:
            lock_data[pack['name']].update({'require': pack['require']})

    return lock_data

def sed(file,search='',replace=''):
        #input file
        file_exists = os.path.exists(file)
        if file_exists == True:
            source = open(file, "rt")
            file_content = source.read()
            source.close()
            file_content = file_content.replace('magento/magento2-base', 'magenxcommerce/magento2-base')
            source = open(file, "wt")
            source.write(file_content)
            #close input and output files
            source.close()
        else:
            print("File "+file+" read Error -> " + str(e))
            exit()

def get_linux_version():
    LINUX_VERSION=exec('hostnamectl | grep "Operating System"', return_code=True)
    my_version = LINUX_VERSION['result_output'].split(":")[1].strip()
    print ('"' + my_version+'"')
    return my_version

#get_linux_version()

def replace_composer_require_packages(data, exclude_from_require_replace, left_magento_package):
    new_packges = {}
    #replace magento vendor
    for package in data["require"]:
        if package not in exclude_from_require_replace:
            if package not in left_magento_package:
                new_packges.update({package.replace("magento/", "magenxcommerce/"): data["require"][package]})
            else:
                print("As is packages : " + package)
                new_packges.update({package: data["require"][package]})
        else:
            print("Excluded Package: " + package)
        # Not including MSI for now. We don't have fork of this crap 
        # new_packges.update({package: data["require"][package]})
    return new_packges

def replace_composer_suggest_packages(data):
    new_suggest={}
    if 'suggest' in data:
        for sugest in data['suggest']:
            new_suggest.update({sugest.replace("magento/", "magenxcommerce/"): data["suggest"][sugest]})
        #p.pprint(data['suggest'])
    return new_suggest

def push_module_version(moduleNameNew,moduleVersion,cdCommand,buildModuleFolder,overwriteRemote):
    if overwriteRemote == True:
        os.system(cdCommand + " && git checkout -b default && git push origin default")
        os.system("gh api repos/{moduleNameNew} --method PATCH --field 'default_branch=default' >/dev/null".format(moduleNameNew = moduleNameNew))
        print("Delete Remote TAg Override")
        os.system(cdCommand + " && git tag -d "+moduleVersion+" && git push origin :refs/tags/" + moduleVersion)
        print("Delete Remote Branch Override")
        os.system(cdCommand + " && git branch -d "+moduleVersion+" && git push origin -f --delete "+moduleVersion)

    commitCommands = [
            "git checkout -b " + moduleVersion,
            "git add . -f",
            "git commit -q -m 'Magento OS Fork commit'",
            "git push -f -u origin " + moduleVersion
    ]
    print(colored(cdCommand + " && " + str.join('+',commitCommands), 'yellow'))
    exec(commitCommands,cd=buildModuleFolder)


#Main function
main()
