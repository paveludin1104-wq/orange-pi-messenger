import socket
import threading
import tkinter as tk
from tkinter import scrolledtext, messagebox
import winsound
from datetime import datetime

class MessengerGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Orange Pi Messenger")
        self.root.geometry("700x600")
        self.root.configure(bg='#1e1e2e')
        
        self.sock = None
        self.connected = False
        self.username = ""
        
        self.create_login_screen()
    
    def create_login_screen(self):
        """Экран входа"""
        self.login_frame = tk.Frame(self.root, bg='#1e1e2e')
        self.login_frame.pack(fill='both', expand=True, padx=20, pady=20)
        
        title = tk.Label(self.login_frame, text="💬 Orange Pi Messenger", 
                        font=("Arial", 24, "bold"), bg='#1e1e2e', fg='#fff')
        title.pack(pady=30)
        
        tk.Label(self.login_frame, text="IP сервера:", font=("Arial", 12), 
                bg='#1e1e2e', fg='#aaa').pack(pady=5)
        self.ip_entry = tk.Entry(self.login_frame, font=("Arial", 12), width=30)
        self.ip_entry.insert(0, "100.98.67.5")
        self.ip_entry.pack(pady=5)
        
        tk.Label(self.login_frame, text="Порт:", font=("Arial", 12), 
                bg='#1e1e2e', fg='#aaa').pack(pady=5)
        self.port_entry = tk.Entry(self.login_frame, font=("Arial", 12), width=30)
        self.port_entry.insert(0, "8888")
        self.port_entry.pack(pady=5)
        
        tk.Label(self.login_frame, text="Ваш логин:", font=("Arial", 12), 
                bg='#1e1e2e', fg='#aaa').pack(pady=5)
        self.username_entry = tk.Entry(self.login_frame, font=("Arial", 12), width=30)
        self.username_entry.pack(pady=5)
        
        self.connect_btn = tk.Button(self.login_frame, text="Подключиться", 
                                    font=("Arial", 14, "bold"), bg='#4CAF50', fg='white',
                                    cursor='hand2', command=self.connect_to_server)
        self.connect_btn.pack(pady=30, ipadx=20, ipady=10)
        
        self.status_label = tk.Label(self.login_frame, text="", font=("Arial", 10), 
                                    bg='#1e1e2e', fg='#888')
        self.status_label.pack(pady=10)
    
    def create_chat_screen(self):
        """Экран чата"""
        self.chat_frame = tk.Frame(self.root, bg='#1e1e2e')
        self.chat_frame.pack(fill='both', expand=True)
        
        header = tk.Frame(self.chat_frame, bg='#2d2d44', height=60)
        header.pack(fill='x')
        header.pack_propagate(False)
        
        tk.Label(header, text=f"💬 Чат ({self.username})", font=("Arial", 16, "bold"), 
                bg='#2d2d44', fg='#fff').pack(pady=15, padx=15, anchor='w')
        
        self.messages_area = scrolledtext.ScrolledText(self.chat_frame, 
                                                      wrap=tk.WORD, 
                                                      font=("Consolas", 11),
                                                      bg='#2d2d44', 
                                                      fg='#fff',
                                                      insertbackground='white')
        self.messages_area.pack(fill='both', expand=True, padx=10, pady=10)
        
        # ✅ ЦВЕТА:
        self.messages_area.tag_config('my_message', foreground='#7E57C2')  # ✅ Фиолетовый (исходящие)
        self.messages_area.tag_config('system_message', foreground='#FFA726')  # Оранжевый (системные)
        self.messages_area.tag_config('other_message', foreground='#00E676')  # ✅ Зелёный (входящие)
        
        self.messages_area.config(state='disabled')
        
        input_frame = tk.Frame(self.chat_frame, bg='#1e1e2e')
        input_frame.pack(fill='x', padx=10, pady=10)
        
        self.message_entry = tk.Entry(input_frame, font=("Arial", 12), bg='#2d2d44', 
                                     fg='#fff', insertbackground='white')
        self.message_entry.pack(side='left', fill='x', expand=True, padx=(0, 10))
        self.message_entry.bind('<Return>', lambda e: self.send_message())
        
        send_btn = tk.Button(input_frame, text="Отправить", font=("Arial", 12, "bold"),
                           bg='#2196F3', fg='white', cursor='hand2',
                           command=self.send_message)
        send_btn.pack(side='right', ipadx=15, ipady=5)
        
        disconnect_btn = tk.Button(input_frame, text="Выйти", font=("Arial", 10),
                                  bg='#f44336', fg='white', cursor='hand2',
                                  command=self.disconnect)
        disconnect_btn.pack(side='right', padx=10, ipadx=10, ipady=5)
    
    def connect_to_server(self):
        """Подключение к серверу"""
        server_ip = self.ip_entry.get().strip()
        try:
            port = int(self.port_entry.get().strip())
        except:
            messagebox.showerror("Ошибка", "Неверный порт!")
            return
        
        username = self.username_entry.get().strip()
        if not username:
            messagebox.showerror("Ошибка", "Введите логин!")
            return
        
        self.status_label.config(text="Подключение...", fg='#FF9800')
        self.connect_btn.config(state='disabled')
        
        def try_connect():
            try:
                self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                self.sock.settimeout(10)
                self.sock.connect((server_ip, port))
                self.sock.settimeout(None)
                
                self.sock.send((username + "\n").encode())
                self.username = username
                self.connected = True
                
                self.root.after(0, self.on_connected)
                
                recv_thread = threading.Thread(target=self.receive_messages)
                recv_thread.daemon = True
                recv_thread.start()
                
            except Exception as e:
                self.root.after(0, lambda: self.on_connection_error(str(e)))
        
        thread = threading.Thread(target=try_connect)
        thread.daemon = True
        thread.start()
    
    def on_connected(self):
        """После успешного подключения"""
        self.login_frame.pack_forget()
        self.create_chat_screen()
        self.add_message(f"✅ Подключено к серверу!", 'system_message')
    
    def on_connection_error(self, error):
        """Ошибка подключения"""
        self.status_label.config(text=f"Ошибка: {error}", fg='#f44336')
        self.connect_btn.config(state='normal')
        messagebox.showerror("Ошибка подключения", f"Не удалось подключиться:\n{error}")
    
    def receive_messages(self):
        """Получение сообщений"""
        try:
            while self.connected:
                data = self.sock.recv(1024)
                if not data:
                    self.root.after(0, lambda: self.add_message("\n⚠️ Отключено от сервера", 'system_message'))
                    break
                
                message = data.decode('utf-8').strip()
                
                # Определяем тип сообщения
                tag = 'other_message'
                is_incoming = False
                
                if any(x in message for x in ['присоединился', 'покинул', 'Подключено', 'История', 'Добро пожаловать']):
                    tag = 'system_message'
                elif message.startswith(f"[{self.username}]"):
                    tag = 'my_message'
                else:
                    tag = 'other_message'
                    is_incoming = True
                
                if is_incoming:
                    self.root.after(0, self.play_sound)
                
                self.root.after(0, lambda m=message, t=tag: self.add_message(m, t))
                
        except Exception as e:
            self.root.after(0, lambda: self.add_message(f"❌ Ошибка: {e}", 'system_message'))
    
    def add_message(self, message, tag):
        """Добавление сообщения"""
        self.messages_area.config(state='normal')
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.messages_area.insert(tk.END, f"[{timestamp}] {message}\n", tag)
        self.messages_area.see(tk.END)
        self.messages_area.config(state='disabled')
    
    def send_message(self):
        """Отправка сообщения"""
        message = self.message_entry.get().strip()
        if message and self.connected:
            try:
                self.sock.send((message + "\n").encode())
                self.message_entry.delete(0, tk.END)
            except:
                messagebox.showerror("Ошибка", "Не удалось отправить сообщение")
    
    def play_sound(self):
        """Звук уведомления для входящих сообщений"""
        try:
            winsound.Beep(800, 150)
            winsound.Beep(1000, 100)
        except:
            pass
    
    def disconnect(self):
        """Отключение"""
        if self.sock:
            self.sock.close()
        self.connected = False
        self.root.destroy()

def main():
    root = tk.Tk()
    app = MessengerGUI(root)
    root.mainloop()

if __name__ == "__main__":
    main()