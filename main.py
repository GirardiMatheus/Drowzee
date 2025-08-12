import tkinter as tk
from tkinter import ttk, messagebox
from PIL import Image, ImageTk 
import time
import threading
import subprocess
import sys
import os
import numpy as np

# Tweak: tempo padrão (minutos)
DEFAULT_FOCUS = 15
DEFAULT_BREAK = 5

# Caminho para um arquivo de som interno (gerado em runtime) ou o usuário pode escolher
EMBED_WAV = None  


def try_play_sound(path=None):
    played = False
    if path is None and EMBED_WAV:
        path = EMBED_WAV

    # 1) paplay
    try:
        if path and shutil_which("paplay"):
            print("[DEBUG] Tentando paplay...")
            subprocess.Popen(["paplay", path])
            played = True
    except Exception as e:
        print("[DEBUG] paplay falhou:", e)

    # 2) aplay
    try:
        if path and shutil_which("aplay"):
            print("[DEBUG] Tentando aplay...")
            subprocess.Popen(["aplay", path])
            played = True
    except Exception as e:
        print("[DEBUG] aplay falhou:", e)

    # 3) simpleaudio (pip)
    try:
        import simpleaudio as sa
        if path:
            print("[DEBUG] Tentando simpleaudio com arquivo...")
            wave_obj = sa.WaveObject.from_wave_file(path)
            wave_obj.play()
            played = True
        else:
            print("[DEBUG] Tentando simpleaudio com tom gerado...")
            try:
                freq = 880.0
                fs = 44100
                seconds = 0.4
                t = np.linspace(0, seconds, int(fs*seconds), False)
                note = (np.sin(freq * t * 2 * np.pi) * 0.3 * (2**15-1)).astype('int16')
                play_obj = sa.play_buffer(note, 1, 2, fs)
                played = True
            except ImportError:
                print("[DEBUG] numpy não está instalado. Instale com: pip install numpy")
    except Exception as e:
        print("[DEBUG] simpleaudio falhou:", e)

    # 4) fallback terminal bell
    if not played:
        try:
            print("[DEBUG] Tentando beep do terminal...")
            sys.stdout.write("\a")
            sys.stdout.flush()
            played = True
        except Exception as e:
            print("[DEBUG] Beep do terminal falhou:", e)

    return played


def shutil_which(cmd):
    """mini-which para evitar import desnecessário (compatível com Python >=3.3)"""
    from shutil import which
    return which(cmd)


class PomodoroApp:
    def __init__(self, root):

        DROWZEE_YELLOW = "#F7D560"
        DROWZEE_BROWN = "#6B4A1B"
        DROWZEE_LIGHT_BROWN = "#B88C4A"
        DROWZEE_DARK = "#222"
        DROWZEE_WHITE = "#fff"

        self.root = root
        root.title("Drowzee Pomodoro")
        root.geometry("340x320")
        root.resizable(False, False)
        root.configure(bg=DROWZEE_YELLOW)

        # Estilo ttk
        style = ttk.Style()
        style.theme_use("clam")
        style.configure("TFrame", background=DROWZEE_YELLOW)
        style.configure("TLabel", background=DROWZEE_YELLOW, foreground=DROWZEE_DARK)
        style.configure("Timer.TLabel", font=("Helvetica", 28, "bold"), background=DROWZEE_YELLOW, foreground=DROWZEE_DARK)
        style.configure("Mode.TLabel", font=("Helvetica", 10, "italic"), background=DROWZEE_YELLOW, foreground=DROWZEE_BROWN)
        style.configure("TButton",
                        background=DROWZEE_BROWN,
                        foreground=DROWZEE_WHITE,
                        borderwidth=1,
                        focusthickness=2,
                        focuscolor=DROWZEE_LIGHT_BROWN,
                        relief="flat")
        style.map("TButton",
                    background=[("active", DROWZEE_LIGHT_BROWN), ("disabled", "#cfcfcf")],
                    foreground=[("active", DROWZEE_WHITE), ("disabled", "#888")])
        style.configure("TSpinbox", fieldbackground=DROWZEE_WHITE, background=DROWZEE_LIGHT_BROWN, foreground=DROWZEE_DARK)
        style.configure("TEntry", fieldbackground=DROWZEE_WHITE, background=DROWZEE_LIGHT_BROWN, foreground=DROWZEE_DARK)

        icon_path = os.path.join(os.path.dirname(__file__), "drowzee.png")
        try:
            if os.path.exists(icon_path):
                icon_img = Image.open(icon_path)
                icon_img = icon_img.resize((64, 64), Image.LANCZOS)
                self.tk_icon = ImageTk.PhotoImage(icon_img)
                root.iconphoto(True, self.tk_icon)
            else:
                self.tk_icon = None
        except Exception:
            self.tk_icon = None  

        main = ttk.Frame(root, padding=10, style="TFrame")
        main.pack(fill=tk.BOTH, expand=True)

        img_path = None
        for ext in ("drowzee.png", "drowzee.jpg"):
            p = os.path.join(os.path.dirname(__file__), ext)
            if os.path.exists(p):
                img_path = p
                break
        try:
            if img_path:
                drowzee_img = Image.open(img_path)
                drowzee_img = drowzee_img.resize((90, 90), Image.LANCZOS)
                self.drowzee_photo = ImageTk.PhotoImage(drowzee_img)
                img_label = ttk.Label(main, image=self.drowzee_photo)
                img_label.pack(pady=(0, 4))
        except Exception:
            pass 

        # Inputs
        input_row = ttk.Frame(main, style="TFrame")
        input_row.pack(fill=tk.X, pady=(0, 8), padx=6)  # Adicione um padding horizontal

        ttk.Label(input_row, text="Foco (min):", style="TLabel").grid(row=0, column=0, sticky=tk.W)
        self.focus_var = tk.IntVar(value=DEFAULT_FOCUS)
        self.focus_spin = ttk.Spinbox(input_row, from_=1, to=180, width=5, textvariable=self.focus_var, style="TSpinbox")
        self.focus_spin.grid(row=0, column=1, padx=(6, 12))

        ttk.Label(input_row, text="Descanso (min):", style="TLabel").grid(row=0, column=2, sticky=tk.W)
        self.break_var = tk.IntVar(value=DEFAULT_BREAK)
        self.break_spin = ttk.Spinbox(input_row, from_=1, to=60, width=5, textvariable=self.break_var, style="TSpinbox")
        self.break_spin.grid(row=0, column=3, padx=(6, 0), sticky=tk.EW)  # Adicione sticky=tk.EW

        input_row.columnconfigure(3, weight=1)  # Permite que a última coluna expanda se necessário

        # Label de estado / tempo
        self.mode = "Foco"  
        self.running = False
        self.paused = False
        self._timer_thread = None
        self._stop_event = threading.Event()
        self.remaining = int(self.focus_var.get() * 60)

        self.time_label = ttk.Label(main, text=self.format_time(self.remaining), style="Timer.TLabel")
        self.time_label.pack(pady=(4, 6))

        self.mode_label = ttk.Label(main, text=f"{self.mode} - Canalize o poder do Drowzee!", style="Mode.TLabel")
        self.mode_label.pack()

        # Controls
        controls = ttk.Frame(main, style="TFrame")
        controls.pack(pady=(10, 0))

        button_width = 10  

        self.start_btn = ttk.Button(
            controls, text="Start", command=self.start, style="TButton",
            width=button_width
        )
        self.start_btn.grid(row=0, column=0, padx=6)

        self.pause_btn = ttk.Button(
            controls, text="Pause", command=self.pause, state=tk.DISABLED, style="TButton",
            width=button_width
        )
        self.pause_btn.grid(row=0, column=1, padx=6)

        self.reset_btn = ttk.Button(
            controls, text="Reset", command=self.reset, state=tk.DISABLED, style="TButton",
            width=button_width
        )
        self.reset_btn.grid(row=0, column=2, padx=6)

        # Caminhos fixos para os sons (coloque os arquivos na mesma pasta do main.py)
        self.sound_focus_path = os.path.join(os.path.dirname(__file__), "drowzee_1.mp3")
        self.sound_break_path = os.path.join(os.path.dirname(__file__), "drowzee_1.mp3")

        # Atualiza label de tempo quando spinboxes mudam
        self.focus_var.trace_add("write", self._on_time_change)
        self.break_var.trace_add("write", self._on_time_change)

        # close handling
        root.protocol("WM_DELETE_WINDOW", self._on_close)

    def _on_time_change(self, *args):
        if not self.running:
            try:
                self.remaining = int(self.focus_var.get()) * 60
                self.mode = "Foco"
                self.mode_label.config(text=f"{self.mode} - Canalize o poder do Drowzee!")
                self.time_label.config(text=self.format_time(self.remaining))
            except Exception:
                pass

    def start(self):
        if self.running:
            return
        # set remaining based on mode when starting first time
        try:
            self.remaining = int(self.focus_var.get()) * 60
        except Exception:
            self.remaining = DEFAULT_FOCUS * 60
        self.mode = "Foco"
        self.mode_label.config(text=f"{self.mode} - Canalize o poder do Drowzee!")

        self.running = True
        self.paused = False
        self.start_btn.config(state=tk.DISABLED)
        self.pause_btn.config(state=tk.NORMAL, text="Pause")
        self.reset_btn.config(state=tk.NORMAL)
        self._stop_event.clear()
        self._timer_thread = threading.Thread(target=self._run_timer, daemon=True)
        self._timer_thread.start()

    def pause(self):
        if not self.running:
            return
        self.paused = not self.paused
        if self.paused:
            self.pause_btn.config(text="Resume")
        else:
            self.pause_btn.config(text="Pause")

    def reset(self):
        # stop thread
        self._stop_event.set()
        self.running = False
        self.paused = False
        self.start_btn.config(state=tk.NORMAL)
        self.pause_btn.config(state=tk.DISABLED, text="Pause")
        self.reset_btn.config(state=tk.DISABLED)
        # reset to focus time
        try:
            self.remaining = int(self.focus_var.get()) * 60
        except Exception:
            self.remaining = DEFAULT_FOCUS * 60
        self.mode = "Foco"
        self.mode_label.config(text=f"{self.mode} - Canalize o poder do Drowzee!")
        self.time_label.config(text=self.format_time(self.remaining))

    def _run_timer(self):
        # main loop
        while not self._stop_event.is_set():
            if self.paused:
                time.sleep(0.2)
                continue
            if self.remaining <= 0:
                # Escolhe o som conforme o modo
                if self.mode == "Foco":
                    sound_path = self.sound_focus_path
                else:
                    sound_path = self.sound_break_path

                played = try_play_sound(sound_path)
                if not played:
                    self.root.after(0, lambda: messagebox.showwarning(
                        "Aviso",
                        "Não foi possível tocar nenhum som de alarme.\n"
                        "Verifique se há dispositivo de áudio disponível, se o beep do terminal está habilitado "
                        "ou se está rodando em ambiente gráfico com suporte a áudio.\n\n"
                        "Dicas:\n"
                        "- Teste o áudio do sistema fora do app.\n"
                        "- Teste o beep com: python3 -c 'print(\"\\a\")'\n"
                        "- Se estiver em WSL, container ou servidor remoto, pode não haver suporte a áudio."
                    ))
                # alternar modos
                if self.mode == "Foco":
                    self.mode = "Descanso"
                    self.remaining = int(self.break_var.get()) * 60
                else:
                    self.mode = "Foco"
                    self.remaining = int(self.focus_var.get()) * 60
                # update UI (execute on main thread)
                self.root.after(0, lambda: self.mode_label.config(text=f"{self.mode} - Canalize o poder do Drowzee!"))
                self.root.after(0, lambda: self.time_label.config(text=self.format_time(self.remaining)))
                time.sleep(0.5)
                continue

            # tick
            self.remaining -= 1
            # update label on main thread
            self.root.after(0, lambda r=self.remaining: self.time_label.config(text=self.format_time(r)))
            time.sleep(1)

        # when stop_event set, ensure UI buttons updated
        self.root.after(0, lambda: self.start_btn.config(state=tk.NORMAL))
        self.root.after(0, lambda: self.pause_btn.config(state=tk.DISABLED, text="Pause"))
        self.root.after(0, lambda: self.reset_btn.config(state=tk.DISABLED))
        self.running = False
        self.paused = False

    @staticmethod
    def format_time(total_seconds):
        m = total_seconds // 60
        s = total_seconds % 60
        return f"{int(m):02d}:{int(s):02d}"

    def _on_close(self):
        if self.running:
            if not messagebox.askokcancel("Sair", "O timer está rodando. Deseja realmente sair?"):
                return
        self._stop_event.set()
        self.root.destroy()


if __name__ == "__main__":
    import shutil  # math removido, shutil ainda é usado em shutil_which

    root = tk.Tk()
    app = PomodoroApp(root)
    root.mainloop()
    root.mainloop()
    self.root.after(0, lambda: self.reset_btn.config(state=tk.DISABLED))
    self.running = False
    self.paused = False

    @staticmethod
    def format_time(total_seconds):
        m = total_seconds // 60
        s = total_seconds % 60
        return f"{int(m):02d}:{int(s):02d}"

    def _on_close(self):
        if self.running:
            if not messagebox.askokcancel("Sair", "O timer está rodando. Deseja realmente sair?"):
                return
        self._stop_event.set()
        self.root.destroy()


if __name__ == "__main__":
    import shutil  # math removido, shutil ainda é usado em shutil_which

    root = tk.Tk()
    app = PomodoroApp(root)
    root.mainloop()
    root.mainloop()
