import os
import threading
import socket
from typing import Optional, Mapping
import tkinter as tk
from tkinter import ttk
from tkinter import filedialog


SETTINGS: Mapping[str, Optional[str]] = {
    'remote_ip': None,  # 远程主机地址
    'remote_port': None,  # 远程主机端口
    'dir_path': None,  # 保存文件夹路径
    'file_name': None,  # 保存文件名
}

WITHOUT_CONNECT_WORD = '连接服务端'
CONNECTED_WORD = '断开服务端连接'
FONT_STYLE = ('宋体', 12)


# 客户端套接字
client_socket: Optional[socket.socket] = None

window = tk.Tk()
window.title("TCP Client")
window.geometry("600x600")


def try_disconnect():
    """
    尝试断开与服务端的连接
    """
    global client_socket
    if client_socket is not None:
        client_socket.close()
        client_socket = None
        connect_var.set(WITHOUT_CONNECT_WORD)


def try_connect():
    """
    尝试与服务端建立连接， 并开始接收服务端发送的数据
    """
    global client_socket
    remote_ip, remote_port = remote_ip_var.get(), int(remote_port_var.get())
    try_disconnect()
    client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    client_socket.settimeout(30)

    try:
        client_socket.connect((remote_ip, remote_port))
        connect_var.set(CONNECTED_WORD)
        output_var.set('建立连接成功，等待服务端发送数据')
        receive_thread = threading.Thread(target=receive_message, daemon=True)
        receive_thread.start()
    except OSError as e:
        output_var.set(f'{e.strerror}\n连接失败，请检查主机地址和端口是否正确')


def click_button():
    cur_state = connect_var.get()
    assert cur_state in (WITHOUT_CONNECT_WORD, CONNECTED_WORD)

    if cur_state == WITHOUT_CONNECT_WORD:
        try_connect()
    else:
        try_disconnect()


def file_name_validate(file_name: str) -> str:
    """
    文件名验证, 确保文件名不会已经存在
    """
    if os.path.exists(file_name):
        idx = 0
        while True:
            new_name = f'{file_name}({idx})'
            if not os.path.exists(new_name):
                return new_name
            idx += 1
    else:
        return file_name


def get_file_name() -> str:
    """
    获取文件名
    """
    folder_path = os.path.abspath(path_var.get())
    file_name = file_name_var.get()
    return file_name_validate(os.path.join(folder_path, file_name))


def receive_message():
    """
    接收服务端发送的数据并保存到本地文件中

    客户端会不断接收服务端的数据，直到服务端断开连接或发生异常
    """
    try:
        path = get_file_name()
        with open(path, mode='wb') as f:
            cnt, size = 0, 0
            while True:
                data = client_socket.recv(4096)
                if not data:
                    break
                f.write(data)
                size += len(data)
                cnt += 1
                output_var.set(f'第{cnt}次接收\n当前接收 {len(data)} 字节数据\n总共接收 {size} 字节数据')

        output_var.set(f'数据接收完成,已自动断开连接,所有数据保存至{path}')
    except ConnectionError as e:
        output_var.set(f'ConnectionError: {e.strerror}\n在数据传输过程中断开连接')
    except TimeoutError as e:
        output_var.set(f'TimeoutError: {e.strerror}\n在数据传输过程中断开连接')
    except OSError as e:
        output_var.set(f'OSError: {e.strerror}\n在数据传输过程中断开连接')
    finally:
        try_disconnect()


def browse_folder():
    if connect_var.get() == CONNECTED_WORD:
        output_var.set('请先断开连接')
        return

    # 打开一个文件夹选择对话框
    folder_selected = filedialog.askdirectory()

    # 打印用户选择的文件夹路径
    if folder_selected:
        path_var.set(folder_selected)


protocol_type_label = tk.Label(window, text='协议类型', font=FONT_STYLE)
protocol_type = ttk.Combobox(window, values=['TCP'], font=FONT_STYLE)
protocol_type.current(0)


remote_ip_label = tk.Label(window, text='远程主机地址', font=FONT_STYLE)
remote_ip_var = tk.StringVar(value=SETTINGS.get('remote_ip', None))
remote_ip_entry = tk.Entry(window, textvariable=remote_ip_var, font=FONT_STYLE)

remote_port_label = tk.Label(window, text='远程主机端口', font=FONT_STYLE)
remote_port_var = tk.StringVar(value=SETTINGS.get('remote_port', None))
remote_port_entry = tk.Entry(window, textvariable=remote_port_var, font=FONT_STYLE)

path_label = tk.Label(window, text='接收文件保存路径', font=FONT_STYLE)
path_var = tk.StringVar(value=SETTINGS.get('dir_path', None))
path_entry = tk.Entry(window, textvariable=path_var, font=FONT_STYLE)
path_button = tk.Button(window, text='浏览本地', command=browse_folder, font=FONT_STYLE)

file_name_label = tk.Label(window, text='保存文件名', font=FONT_STYLE)
file_name_var = tk.StringVar(value=SETTINGS.get('file_name', None))
file_name_entry = tk.Entry(window, textvariable=file_name_var, font=FONT_STYLE)

connect_var = tk.StringVar(value=WITHOUT_CONNECT_WORD)
connect_button = tk.Button(window, textvariable=connect_var, command=click_button, width=20, font=FONT_STYLE)

output_var = tk.StringVar()
output_label = tk.Label(window, width=80, height=10, textvariable=output_var, wraplength=300, justify=tk.CENTER, font=FONT_STYLE)

protocol_type_label.grid(row=0, column=0, padx=5, pady=5)
protocol_type.grid(row=0, column=1, padx=5, pady=5)
remote_ip_label.grid(row=1, column=0, padx=5, pady=5)
remote_ip_entry.grid(row=1, column=1, padx=5, pady=5)
remote_port_label.grid(row=2, column=0, padx=5, pady=5)
remote_port_entry.grid(row=2, column=1, padx=5, pady=5)
path_label.grid(row=3, column=0, padx=5, pady=5)
path_entry.grid(row=3, column=1, padx=5, pady=5)
path_button.grid(row=3, column=2, padx=5, pady=5)
file_name_label.grid(row=4, column=0, padx=5, pady=5)
file_name_entry.grid(row=4, column=1, padx=5, pady=5)
connect_button.grid(row=5, column=1, padx=5, pady=5)
output_label.grid(row=6, column=0, columnspan=5, padx=5, pady=5)
window.mainloop()
