import tkinter as tk
from tkinter import ttk, scrolledtext
import serial
import serial.tools.list_ports
import threading
import time
import queue
import sys
import os
from datetime import datetime

def resource_path(relative_path):
    if hasattr(sys, '_MEIPASS'):
        return os.path.join(sys._MEIPASS, relative_path)
    return os.path.join(os.path.dirname(os.path.abspath(__file__)), relative_path)

COLORS = {
    'bg': '#0c0c0c',
    'bg_secondary': '#111111',
    'bg_input': '#0a0a0a',
    'border': '#1e1e1e',
    'text': '#e0e0e0',
    'text_dim': '#64748b',
    'accent': '#22d3ee',
    'success': '#4ade80',
    'warning': '#fbbf24',
    'error': '#f472b6',
    'tx': '#a78bfa',
}


class SerialMonitor:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Serial Monitor")
        self.root.geometry("950x650")
        self.root.configure(bg=COLORS['bg'])
        self.root.minsize(700, 400)

        try:
            self.root.iconbitmap(resource_path('icon.ico'))
        except:
            pass

        self.default_port = "COM3"
        self.default_baud = 115200

        self.serial_port = None
        self.connected = False
        self.running = True
        self.auto_reconnect = tk.BooleanVar(value=True)
        self.auto_scroll = tk.BooleanVar(value=True)
        self.show_timestamp = tk.BooleanVar(value=False)

        self.rx_queue = queue.Queue()

        self.setup_ui()

        self.root.after(100, self.auto_connect)
        self.root.after(50, self.process_rx_queue)

        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)

    def setup_ui(self):
        header = tk.Frame(self.root, bg=COLORS['bg'], pady=15, padx=20)
        header.pack(fill=tk.X)

        title_frame = tk.Frame(header, bg=COLORS['bg'])
        title_frame.pack(side=tk.LEFT)

        tk.Label(
            title_frame,
            text="SERIAL",
            font=('Consolas', 16, 'bold'),
            fg=COLORS['accent'],
            bg=COLORS['bg']
        ).pack(side=tk.LEFT)

        tk.Label(
            title_frame,
            text="_",
            font=('Consolas', 16, 'bold'),
            fg=COLORS['text_dim'],
            bg=COLORS['bg']
        ).pack(side=tk.LEFT)

        tk.Label(
            title_frame,
            text="MONITOR",
            font=('Consolas', 16, 'bold'),
            fg=COLORS['text'],
            bg=COLORS['bg']
        ).pack(side=tk.LEFT)

        self.cursor_label = tk.Label(
            title_frame,
            text="█",
            font=('Consolas', 16, 'bold'),
            fg=COLORS['accent'],
            bg=COLORS['bg']
        )
        self.cursor_label.pack(side=tk.LEFT, padx=(2, 0))
        self.blink_cursor()

        status_frame = tk.Frame(header, bg=COLORS['bg'])
        status_frame.pack(side=tk.RIGHT)

        self.status_dot = tk.Canvas(
            status_frame,
            width=12,
            height=12,
            bg=COLORS['bg'],
            highlightthickness=0
        )
        self.status_dot.pack(side=tk.LEFT, padx=(0, 8))
        self.draw_status_dot('offline')

        self.status_label = tk.Label(
            status_frame,
            text="OFFLINE",
            font=('Consolas', 10),
            fg=COLORS['text_dim'],
            bg=COLORS['bg']
        )
        self.status_label.pack(side=tk.LEFT)

        tk.Frame(self.root, bg=COLORS['border'], height=1).pack(fill=tk.X)

        controls = tk.Frame(self.root, bg=COLORS['bg_secondary'], pady=12, padx=20)
        controls.pack(fill=tk.X)

        port_frame = tk.Frame(controls, bg=COLORS['bg_secondary'])
        port_frame.pack(side=tk.LEFT)

        tk.Label(
            port_frame,
            text="PORT",
            font=('Consolas', 9),
            fg=COLORS['text_dim'],
            bg=COLORS['bg_secondary']
        ).pack(anchor=tk.W)

        self.port_var = tk.StringVar(value=self.default_port)
        self.port_entry = tk.Entry(
            port_frame,
            textvariable=self.port_var,
            font=('Consolas', 11),
            bg=COLORS['bg_input'],
            fg=COLORS['text'],
            insertbackground=COLORS['accent'],
            relief=tk.FLAT,
            width=10,
            highlightthickness=1,
            highlightbackground=COLORS['border'],
            highlightcolor=COLORS['accent']
        )
        self.port_entry.pack(pady=(3, 0))

        baud_frame = tk.Frame(controls, bg=COLORS['bg_secondary'])
        baud_frame.pack(side=tk.LEFT, padx=(20, 0))

        tk.Label(
            baud_frame,
            text="BAUD",
            font=('Consolas', 9),
            fg=COLORS['text_dim'],
            bg=COLORS['bg_secondary']
        ).pack(anchor=tk.W)

        self.baud_var = tk.StringVar(value=str(self.default_baud))
        self.baud_entry = tk.Entry(
            baud_frame,
            textvariable=self.baud_var,
            font=('Consolas', 11),
            bg=COLORS['bg_input'],
            fg=COLORS['text'],
            insertbackground=COLORS['accent'],
            relief=tk.FLAT,
            width=10,
            highlightthickness=1,
            highlightbackground=COLORS['border'],
            highlightcolor=COLORS['accent']
        )
        self.baud_entry.pack(pady=(3, 0))

        self.connect_btn = tk.Button(
            controls,
            text="CONNECT",
            font=('Consolas', 10, 'bold'),
            bg=COLORS['bg_input'],
            fg=COLORS['accent'],
            activebackground=COLORS['bg_secondary'],
            activeforeground=COLORS['accent'],
            relief=tk.FLAT,
            cursor='hand2',
            padx=20,
            pady=8,
            highlightthickness=1,
            highlightbackground=COLORS['accent'],
            command=self.toggle_connection
        )
        self.connect_btn.pack(side=tk.LEFT, padx=(20, 0), pady=(12, 0))

        options_frame = tk.Frame(controls, bg=COLORS['bg_secondary'])
        options_frame.pack(side=tk.RIGHT)

        self.create_checkbox(options_frame, "Auto-Reconnect", self.auto_reconnect)
        self.create_checkbox(options_frame, "Auto-Scroll", self.auto_scroll)
        self.create_checkbox(options_frame, "Timestamp", self.show_timestamp)

        clear_btn = tk.Button(
            controls,
            text="CLEAR",
            font=('Consolas', 9),
            bg=COLORS['bg_input'],
            fg=COLORS['text_dim'],
            activebackground=COLORS['bg_secondary'],
            activeforeground=COLORS['text'],
            relief=tk.FLAT,
            cursor='hand2',
            padx=12,
            pady=5,
            command=self.clear_output
        )
        clear_btn.pack(side=tk.RIGHT, padx=(0, 20), pady=(12, 0))

        tk.Frame(self.root, bg=COLORS['border'], height=1).pack(fill=tk.X)

        output_frame = tk.Frame(self.root, bg=COLORS['bg'], padx=20, pady=15)
        output_frame.pack(fill=tk.BOTH, expand=True)

        output_container = tk.Frame(
            output_frame,
            bg=COLORS['border'],
            padx=1,
            pady=1
        )
        output_container.pack(fill=tk.BOTH, expand=True)

        self.output_text = tk.Text(
            output_container,
            bg=COLORS['bg_input'],
            fg=COLORS['text'],
            font=('Consolas', 10),
            insertbackground=COLORS['accent'],
            selectbackground=COLORS['accent'],
            selectforeground=COLORS['bg'],
            relief=tk.FLAT,
            wrap=tk.WORD,
            padx=15,
            pady=15
        )
        self.output_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        scrollbar = tk.Scrollbar(
            output_container,
            orient=tk.VERTICAL,
            command=self.output_text.yview,
            bg=COLORS['bg_input'],
            troughcolor=COLORS['bg_input'],
            activebackground=COLORS['text_dim'],
            highlightthickness=0,
            bd=0
        )
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.output_text.configure(yscrollcommand=scrollbar.set)

        self.output_text.tag_configure('rx', foreground=COLORS['success'])
        self.output_text.tag_configure('tx', foreground=COLORS['tx'])
        self.output_text.tag_configure('info', foreground=COLORS['text_dim'])
        self.output_text.tag_configure('error', foreground=COLORS['error'])
        self.output_text.tag_configure('warning', foreground=COLORS['warning'])
        self.output_text.tag_configure('accent', foreground=COLORS['accent'])
        self.output_text.tag_configure('timestamp', foreground=COLORS['text_dim'])

        self.output_text.configure(state=tk.DISABLED)

        tk.Frame(self.root, bg=COLORS['border'], height=1).pack(fill=tk.X)

        input_frame = tk.Frame(self.root, bg=COLORS['bg_secondary'], pady=12, padx=20)
        input_frame.pack(fill=tk.X)

        tk.Label(
            input_frame,
            text=">",
            font=('Consolas', 14, 'bold'),
            fg=COLORS['accent'],
            bg=COLORS['bg_secondary']
        ).pack(side=tk.LEFT)

        self.input_entry = tk.Entry(
            input_frame,
            font=('Consolas', 11),
            bg=COLORS['bg_input'],
            fg=COLORS['text'],
            insertbackground=COLORS['accent'],
            relief=tk.FLAT,
            highlightthickness=1,
            highlightbackground=COLORS['border'],
            highlightcolor=COLORS['accent']
        )
        self.input_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(10, 15))
        self.input_entry.bind('<Return>', self.send_data)

        tk.Label(
            input_frame,
            text="END",
            font=('Consolas', 9),
            fg=COLORS['text_dim'],
            bg=COLORS['bg_secondary']
        ).pack(side=tk.LEFT, padx=(0, 5))

        self.line_ending_var = tk.StringVar(value="CRLF")
        endings = ["NONE", "LF", "CR", "CRLF"]
        self.ending_btn = tk.Button(
            input_frame,
            textvariable=self.line_ending_var,
            font=('Consolas', 9),
            bg=COLORS['bg_input'],
            fg=COLORS['accent'],
            activebackground=COLORS['bg_secondary'],
            activeforeground=COLORS['accent'],
            relief=tk.FLAT,
            cursor='hand2',
            width=6,
            command=lambda: self.cycle_line_ending(endings)
        )
        self.ending_btn.pack(side=tk.LEFT, padx=(0, 15))

        send_btn = tk.Button(
            input_frame,
            text="SEND",
            font=('Consolas', 10, 'bold'),
            bg=COLORS['bg_input'],
            fg=COLORS['accent'],
            activebackground=COLORS['bg_secondary'],
            activeforeground=COLORS['accent'],
            relief=tk.FLAT,
            cursor='hand2',
            padx=20,
            pady=5,
            command=self.send_data
        )
        send_btn.pack(side=tk.RIGHT)

    def create_checkbox(self, parent, text, variable):
        frame = tk.Frame(parent, bg=COLORS['bg_secondary'])
        frame.pack(side=tk.LEFT, padx=(0, 15))

        cb = tk.Checkbutton(
            frame,
            text=text,
            variable=variable,
            font=('Consolas', 9),
            bg=COLORS['bg_secondary'],
            fg=COLORS['text_dim'],
            activebackground=COLORS['bg_secondary'],
            activeforeground=COLORS['text'],
            selectcolor=COLORS['bg_input'],
            highlightthickness=0,
            cursor='hand2'
        )
        cb.pack()

    def cycle_line_ending(self, endings):
        current = self.line_ending_var.get()
        idx = endings.index(current) if current in endings else 0
        self.line_ending_var.set(endings[(idx + 1) % len(endings)])

    def blink_cursor(self):
        if not self.running:
            return
        current = self.cursor_label.cget('fg')
        new_color = COLORS['bg'] if current == COLORS['accent'] else COLORS['accent']
        self.cursor_label.configure(fg=new_color)
        self.root.after(530, self.blink_cursor)

    def draw_status_dot(self, status):
        self.status_dot.delete('all')
        colors = {
            'online': COLORS['success'],
            'offline': COLORS['text_dim'],
            'reconnecting': COLORS['warning']
        }
        color = colors.get(status, COLORS['text_dim'])

        if status == 'online':
            self.status_dot.create_oval(0, 0, 12, 12, fill=color, outline='')
        else:
            self.status_dot.create_oval(2, 2, 10, 10, fill=color, outline='')

    def update_status(self, status, text):
        colors = {
            'online': COLORS['success'],
            'offline': COLORS['text_dim'],
            'reconnecting': COLORS['warning']
        }
        self.status_label.configure(text=text.upper(), fg=colors.get(status, COLORS['text_dim']))
        self.draw_status_dot(status)

    def auto_connect(self):
        self.log_message("══════════════════════════════════════════", tag='info')
        self.log_message("  SERIAL MONITOR INITIALIZED", tag='accent')
        self.log_message("══════════════════════════════════════════", tag='info')
        self.log_message(f"Connecting to {self.default_port} @ {self.default_baud}...", tag='info')
        self.connect()

    def connect(self):
        if self.connected:
            return

        port = self.port_var.get()
        try:
            baud = int(self.baud_var.get())
        except ValueError:
            baud = self.default_baud

        try:
            self.serial_port = serial.Serial(
                port=port,
                baudrate=baud,
                timeout=0.1,
                write_timeout=1
            )
            self.connected = True
            self.update_status('online', 'CONNECTED')
            self.connect_btn.configure(text="DISCONNECT", fg=COLORS['error'])
            self.log_message(f"Connected to {port} @ {baud}", tag='accent')

            self.read_thread = threading.Thread(target=self.read_serial, daemon=True)
            self.read_thread.start()

        except serial.SerialException as e:
            self.log_message(f"Connection failed: {e}", tag='error')
            self.connected = False
            if self.auto_reconnect.get():
                self.schedule_reconnect()

    def disconnect(self):
        self.connected = False
        if self.serial_port and self.serial_port.is_open:
            try:
                self.serial_port.close()
            except:
                pass
        self.serial_port = None
        self.update_status('offline', 'DISCONNECTED')
        self.connect_btn.configure(text="CONNECT", fg=COLORS['accent'])
        self.log_message("Disconnected", tag='warning')

    def toggle_connection(self):
        if self.connected:
            self.disconnect()
        else:
            self.connect()

    def read_serial(self):
        while self.running and self.connected:
            try:
                if self.serial_port and self.serial_port.is_open and self.serial_port.in_waiting:
                    data = self.serial_port.read(self.serial_port.in_waiting)
                    if data:
                        try:
                            text = data.decode('utf-8', errors='replace')
                            self.rx_queue.put(('rx', text))
                        except:
                            self.rx_queue.put(('rx', data.hex()))
                time.sleep(0.01)
            except serial.SerialException as e:
                self.rx_queue.put(('error', str(e)))
                self.connected = False
                break
            except:
                time.sleep(0.1)

        if self.running and self.auto_reconnect.get() and not self.connected:
            self.root.after(0, self.schedule_reconnect)

    def schedule_reconnect(self):
        if not self.running:
            return
        self.update_status('reconnecting', 'RECONNECTING')
        self.log_message("Reconnecting in 2s...", tag='warning')
        self.root.after(2000, self.attempt_reconnect)

    def attempt_reconnect(self):
        if not self.running or self.connected:
            return
        self.disconnect()
        self.connect()

    def process_rx_queue(self):
        try:
            while True:
                msg_type, data = self.rx_queue.get_nowait()
                if msg_type == 'error':
                    self.log_message(f"Error: {data}", tag='error')
                else:
                    self.log_message(data, tag='rx', is_raw=True)
        except queue.Empty:
            pass

        if self.running:
            self.root.after(50, self.process_rx_queue)

    def send_data(self, event=None):
        if not self.connected or not self.serial_port:
            self.log_message("Not connected!", tag='error')
            return

        data = self.input_entry.get()
        if not data:
            return

        ending_map = {"NONE": "", "LF": "\n", "CR": "\r", "CRLF": "\r\n"}
        line_ending = ending_map.get(self.line_ending_var.get(), "\r\n")
        data_to_send = data + line_ending

        try:
            self.serial_port.write(data_to_send.encode('utf-8'))
            self.log_message(f"< {data}", tag='tx')
            self.input_entry.delete(0, tk.END)
        except serial.SerialException as e:
            self.log_message(f"Send error: {e}", tag='error')

    def log_message(self, message, tag='rx', is_raw=False):
        self.output_text.configure(state=tk.NORMAL)

        if self.show_timestamp.get() and not is_raw:
            timestamp = datetime.now().strftime("[%H:%M:%S] ")
            self.output_text.insert(tk.END, timestamp, 'timestamp')

        if is_raw:
            self.output_text.insert(tk.END, message, tag)
        else:
            self.output_text.insert(tk.END, message + '\n', tag)

        if self.auto_scroll.get():
            self.output_text.see(tk.END)

        self.output_text.configure(state=tk.DISABLED)

    def clear_output(self):
        self.output_text.configure(state=tk.NORMAL)
        self.output_text.delete(1.0, tk.END)
        self.output_text.configure(state=tk.DISABLED)

    def on_closing(self):
        self.running = False
        self.disconnect()
        self.root.destroy()

    def run(self):
        self.root.mainloop()


if __name__ == "__main__":
    app = SerialMonitor()
    app.run()
