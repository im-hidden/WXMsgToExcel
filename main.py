from script.get_wechat_key import Wechat
from script.decrypt import decrypt
from script.merge import merge_databases
from script.merge_table import merge_table
from script.compress_content import file
from export_excel import *
import pymem.process
from pymem import Pymem
import shutil


def check_key():
    file_name = f"key.txt"  # 替换为你希望创建的文件名

    # 检查文件是否存在
    if not os.path.exists(file_name):
        # 如果文件不存在，创建它
        with open(file_name, "w"):
            pass  # 创建空文件
        print(f"文件 {file_name} 已在当前目录下创建。")
    else:
        print(f"文件 {file_name} 已经存在于当前目录。")


def check_dir_file(path, file_path):
    if not os.path.exists(path):  # 检查目录是否存在，不存在则创建
        os.makedirs(path)

    if not os.path.exists(file_path):  # 检查文件是否存在，不存在则创建
        with open(file_path, 'w'):
            # 可以在此处写入一些初始化内容到文件，如果没有内容可写，pass即可
            pass
        print(f"文件 '{file_path}' 已创建。")
    else:
        print(f"文件 '{file_path}' 已经存在。")


def get_key():
    try:
        wechat = Pymem("WeChat.exe")
        key = Wechat(wechat).GetInfo()
        with open("key.txt", "w") as file:
            file.write(key)
    except pymem.exception.ProcessNotFound:
        print("微信未登录")
        input("按任意键退出...")
        exit(0)
    except pymem.exception.CouldNotOpenProcess:
        print("权限不足")
        input("按任意键退出...")
        exit(0)
    except Exception as e:
        print(e)
        input("按任意键退出...")
        exit(0)


def get_wx_location():
    # 获取当前用户名
    users = os.path.expandvars('$HOMEPATH')

    # 找到3ebffe94.ini配置文件
    with open(r'C:' + users + '\\AppData\\Roaming\\Tencent\\WeChat\\All Users\\config\\3ebffe94.ini') as f:
        f = f.read()

    # 读取文件将路径放到wx_location变量里
    if f == 'MyDocument:':
        wx_location = 'C:' + users + '\\Documents\\WeChat Files'
    else:
        wx_location = f + "\\WeChat Files"
    return wx_location


def get_path_decrypt_merge():
    wx_location = get_wx_location()

    # 列出目录下所有文件夹
    for folder_name in os.listdir(wx_location):
        if os.path.isdir(os.path.join(wx_location, folder_name)):
            if 'wxid_' in folder_name:
                contact_path = os.path.join(wx_location, folder_name, 'Msg')
                msg_path = os.path.join(wx_location, folder_name, 'Msg', 'Multi')
                decrypt_db(contact_path, msg_path, folder_name)


def decrypt_db(contact_path, msg_path, user_path):
    with open('key.txt', 'r') as f:
        key = f.read()
    contact_micromsg_path = contact_path + '\\MicroMsg.db'
    dir_path = f'.\\db\\{user_path}'
    dir_micromsg_path = os.path.join(dir_path, 'MicroMsg.db')
    check_dir_file(dir_path, dir_micromsg_path)

    decrypt(key, contact_micromsg_path, dir_micromsg_path)
    for folder_name in os.listdir(msg_path):
        if os.path.isfile(os.path.join(msg_path, folder_name)):
            if len(folder_name) == 7:
                try:
                    msg_db_path = os.path.join(msg_path, folder_name)
                    check_dir_file(dir_path, os.path.join(dir_path, folder_name))
                    decrypt(key, msg_db_path, os.path.join(dir_path, folder_name))
                except Exception as e:
                    print(e)
    try:
        merge_db(user_path)  # 合并数据库
    except Exception as e:
        print('非当前登录微信数据库,无法合并,自动跳过...')


def read_all_files_in_directory(directory_path):
    """
    读取指定目录下的所有文件。
    参数:
    directory_path (str): 要读取的目录的路径。
    返回:
    files_list (list[str]): 目录中所有文件的完整路径列表。
    """
    files_list = []
    for item in os.listdir(directory_path):
        # 构建完整的文件/子目录路径
        full_item_path = os.path.join(directory_path, item)

        # 检查是否为文件（而非目录）
        if os.path.isfile(full_item_path):
            files_list.append(full_item_path)

    return files_list


def merge_db(user_path):
    source_databases = read_all_files_in_directory(f'db\\{user_path}')
    # 源数据库文件列表
    # source_databases = [f"db\\{user_path}\\MSG1.db", f"db\\{user_path}\\MSG2.db", f"db\\{user_path}\\MSG3.db",
    #                     f"db\\{user_path}\\MSG4.db", f"db\\{user_path}\\MSG5.db", f"db\\{user_path}\\MicroMsg.db"]
    # 目标数据库文件
    target_database = f"db\\{user_path}\\MSG.db"

    shutil.copy(f'db\\{user_path}\\MSG0.db', target_database)  # 使用MSG0.db数据库文件作为模板
    merge_databases([item for item in source_databases if 'MicroMsg.db' not in item and 'MSG0.db' not in item],
                    target_database)  # 合并数据库,列表推导式,排除MicroMsg.db、MSG0.db文件
    merge_table(f"db\\{user_path}\\MicroMsg.db", target_database, ['Contact', 'ChatRoom'])  # 将两个库文的表合成一个文件
    remove_db(source_databases)  # 删除文件


def remove_db(file_paths):
    for file_path in file_paths:
        print(f"正在清理 {file_path}...")
        try:
            os.remove(file_path)
            print(f"{file_path} 已清理。")
        except FileNotFoundError:
            print(f"错误：文件 {file_path} 未找到。")
        except PermissionError:
            print(f"错误：没有足够的权限删除 {file_path}。")
        except Exception as e:
            print(f"删除文件时发生错误：{e}")


def remove_dir(dir_paths):
    for dir_path in dir_paths:
        print(f"正在清理 {dir_path}...")
        try:
            shutil.rmtree(dir_path)
            print(f"{dir_path} 已清理。")
        except FileNotFoundError:
            print(f"错误：目录 {dir_path} 未找到。")
        except PermissionError:
            print(f"错误：没有足够的权限删除 {dir_path}。")
        except Exception as e:
            print(f"删除目录时发生错误：{e}")


if __name__ == '__main__':
    check_key()  # 检查存放key文件是否存在
    get_key()  # 获取key
    get_path_decrypt_merge()  # 自动获取路径，解密，合并数据库

    while True:
        is_file = input('是否复制本地文件到当前路径?[复制后可在excel中超链接打开文件](y/n)')
        wxids = get_wxid()
        if is_file == 'n':  # 不复制文件
            # 导出为excel
            for wx in wxids:  # 多个微信号,循环处理
                try:
                    all_data = get_data(wx)
                except Exception as e:
                    print('当前处理数据库非当前登录微信,跳过...')
                    continue
                deal_over_data = deal_data(all_data, wx)
                write_excel(deal_over_data, wx)
            break

        elif is_file == 'y':  # 复制文件
            for wx in wxids:  # 多个微信号,循环处理
                try:
                    all_data = get_data(wx)
                except Exception as e:
                    print('当前处理数据库非当前登录微信,跳过...')
                    continue
                print('正在复制本地文件到 .\\data\\files 目录下...')
                for i in tqdm(range(len(all_data))):

                    if all_data[i][8] == 49 and all_data[i][9] == 6:
                        wx_location = os.path.join(get_wx_location(), wx)  # 已登录微信当前用户路径
                        try:
                            file_path = file(bytes(all_data[i][7]), bytes(all_data[i][10]), '.\\data\\files', wx,
                                             wx_location)
                            if file_path['file_path'] == '':
                                all_data[i][3] = '文件未下载或已删除'
                                continue
                            all_data[i][3] = file_path['file_path']
                        except Exception as e:
                            all_data[i][3] = '文件解析失败'

                deal_over_data = deal_data(all_data, wx)
                write_excel(deal_over_data, wx)
            break

        else:
            pass
    remove_db(['.\\key.txt'])  # 删除db文件夹和key.txt文件
    remove_dir(['.\\db'])
    input('导出完成,按任意建关闭...')
