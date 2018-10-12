__author__  = 'Yaseen Ali'


import os
import re
import csv

cwd = os.getcwd()

version_file_name  = os.path.join(cwd,"version_file.txt")

def filestoprocess(path):
    file_list = set()
    file_names_list = []
    for root, dirs, files in os.walk(p):
        file_list.update([os.path.join(root, f) for f in files if f.endswith('.L5K')])
        file_names_list.append(f)
    return file_list

def openfile(filename):
    #file_data = []
    with open(filename,'r') as file:
        if file.mode == 'r':
            file_data = file.readlines()
            #print(file_data)
        else:
            print("Error: File mode is not read")
            exit()
    return file_data

def module_capture(file):
    modules = []
    module_list = []
    flag = False
    for line in file:
        if '\tMODULE' in line or flag:
            flag = True
            #print(line)
            module_list.append(line)
            if r'END_MODULE' in line:
                flag = False
                if module_list:
                    modules.append(module_list)
                module_list = []
        #break
    #[print(line) for line in modules[0]]
    #print(modules[1])
    #print(len(modules))
    return modules

def module_characterizer(module):
    '''
    This Function returns a 1 if the module is a PLC and a 2 is its an Ethernet Communications card
    '''

    #Test for PLC. If the parent name is the same as the module name, the module is a PLC
    search_string = module[0] #the name info is in the first line

    pattern = re.compile(r'\"\w*\"')
    #[print(line) for line in module] #for debugging
    result = re.search(pattern,search_string)
    if result:
        modulename = result.group(0)[1:-1]

        #print(modulename)
        if search_string.count(modulename) >1:
            return 1

        for line in module:
            if 'NodeAddress :=' in line:
                return 2

def slot_number(module):
    slot_pattern = re.compile(r'Slot\s\:=\s\d*')
    slot_search = [re.search(slot_pattern,line) for line in module if re.search(slot_pattern,line)]
    if slot_search:
        slot = re.split('\W',slot_search[0].group(0))[-1]
        return slot

    else:
        return "-"


def version_number(ctrl_module):
    #regex Patterns
    major_version_pattern = re.compile(r'Major\s\:=\s\d*')
    minor_version_pattern = re.compile(r'Minor\s\:=\s\d*')

    major_version_search = [re.search(major_version_pattern,line) for line in ctrl_module if re.search(major_version_pattern,line)]
    if major_version_search:
        major_version = re.split('\W',major_version_search[0].group(0))[-1]

    minor_version_search = [re.search(minor_version_pattern,line) for line in ctrl_module if re.search(minor_version_pattern,line)]
    if minor_version_search:
        minor_version = re.split('\W',minor_version_search[0].group(0))[-1]

    if major_version is not None and minor_version is not None:
        return major_version + '.' + minor_version
    else:
        return 'None'

def node_address(module):
    for line in module:
            if 'NodeAddress :=' in line:
                #print(re.split('\s',line))
                try:
                    if line[1] is '"':
                        return re.split('\s',line)[-2][1:-2]
                    else:
                        return re.split('\s',line)[-2][:-2]
                except IndexError:
                    return "No IP Specified"
                break
    return "No IP"

def catalog_num(module):
    for line in module:
            if 'CatalogNumber :=' in line:
                #print(re.split('\s',line))
                try:
                    if float(version_number(module)) < 16:
                        return re.split('=',line)[1][:-1]
                    else:
                        return re.split('"',line)[-2][:]
                except IndexError:
                    return "None"
                break
    return "No IP"

def main():
    eth_data = []
    csv_data = []
    files_toprocess = set()
    files_not_precessed = []
    path = os.getcwd() + "\L5K_files"
    #print(path + '\n')
    for root, dirs, files in os.walk(path):
        files_toprocess.update([os.path.join(root, f) for f in files if f.endswith('.L5K')])
    #print(files_toprocess)
    #filename = "wrapper3.L5K"
    for filename in files_toprocess:
        try:
            file = openfile(filename)

        #Getting comm path if it exists
            comm_path_str = re.compile(r'CommPath\s\:=\s\".*Backplane\\\d.*\,') #Pattern
            comm_path = [(re.search(comm_path_str,line),file.index(line)) for line in file if re.search(comm_path_str,line)] #search

            if comm_path:
                path = comm_path[0][0].group(0)[:-1]
            else:
                path = 'No Comm path specified'

            print('\n' + filename.split("\\")[-1])

        #getting all the modules from the file

            all_modules = module_capture(file)
            plc_version = version_number(all_modules[0]) #first module in the list is always the controller module


            #[print(module_characterizer(module)) for module in all_modules if module_characterizer(module)]

            for module in all_modules:
                #if module_characterizer(module) and int(module_characterizer(module)) == 2:
                if all_modules.index(module) == 0:
                    print(str(all_modules.index(module)) + " " + version_number(module) + " PLC ")
                    line = [ version_number(module),"PLC: " + filename.split("\\")[-1] ,slot_number(module), catalog_num(module)]
                    eth_data.append(line)
                elif node_address(module) == "No IP" or '.' not in node_address(module):
                    pass
                else:
                    print(str(all_modules.index(module)) + " " + version_number(module) + " " + node_address(module) + " Slot Number:" + slot_number(module) + " Catalog Num: " + catalog_num(module))
                    line = [version_number(module), node_address(module), slot_number(module), catalog_num(module)]
                    eth_data.append(line)



            filename_without_path = filename.split("\\")[-1]

            #print(filename_without_path)
            line_in_file = [filename_without_path,path,plc_version]
            csv_data.append(line_in_file)
    #
        except UnicodeDecodeError:
            filename_without_path = filename.split("\\")[-1]
            files_not_precessed.append(filename_without_path + " - Unicode Decode Error")
        #except:
            filename_without_path = filename.split("\\")[-1]
            files_not_precessed.append(filename_without_path)
    #
    #
    print(files_not_precessed)
    #Writing to controller CSV File
    csv_file = open("controller_versions.csv", 'w', newline='')
    csv_writer = csv.writer(csv_file)
    top_row = ['Filename', ' communication path', 'controller version']
    csv_writer.writerow(top_row)
    [csv_writer.writerow(row) for row in csv_data]

    #Writing to ethernet CSV File
    csv_file = open("ethernet_versions.csv", 'w', newline='')
    csv_writer = csv.writer(csv_file)
    top_row = ['Version', 'IP','  Slot', 'Catalog']
    csv_writer.writerow(top_row)
    [csv_writer.writerow(row) for row in eth_data]

    #
    #Writing to CSV File Unprocessed
    csv_file = open("UnprocessedFiles.csv", 'w', newline='')
    csv_writer = csv.writer(csv_file)
    top_row = ['Unprocessed Files']
    csv_writer.writerow(top_row)
    [csv_writer.writerow([row])for row in files_not_precessed]

if __name__=='__main__':
    main()
