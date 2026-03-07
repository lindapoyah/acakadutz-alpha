import customtkinter as ctk
from tkinter import filedialog, messagebox
import os
import random
import subprocess
import threading
import time
import sys  # Untuk deteksi platform

ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("dark-blue")

# Flag untuk hide console di Windows
HIDE_WINDOW = subprocess.CREATE_NO_WINDOW if sys.platform.startswith('win') else 0

class VideoShufflerApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("Video Shuffler & Merger - MBX Edition")
        self.geometry("750x550")
        self.resizable(False, False)

        self.folder_sumber = ""
        self.folder_output = ""
        self.jumlah_video = ctk.IntVar(value=10)
        self.nama_output = ctk.StringVar(value="")

        self.status_text = ctk.StringVar(value="Siap render...")
        self.progress_value = ctk.DoubleVar(value=0.0)
        self.create_widgets()

    def create_widgets(self):
        left_frame = ctk.CTkFrame(self, corner_radius=10)
        left_frame.pack(side="left", fill="both", expand=True, padx=15, pady=15)

        ctk.CTkLabel(left_frame, text="Nama File Output:").pack(anchor="w", pady=(10,0))
        ctk.CTkEntry(left_frame, textvariable=self.nama_output, width=280).pack(pady=5)

        ctk.CTkLabel(left_frame, text="Folder Sumber Video:").pack(anchor="w", pady=(15,0))
        self.entry_sumber = ctk.CTkEntry(left_frame, width=280)
        self.entry_sumber.pack(pady=5)
        ctk.CTkButton(left_frame, text="Browse", width=120, command=self.pilih_folder_sumber).pack()

        ctk.CTkLabel(left_frame, text="Folder Output:").pack(anchor="w", pady=(15,0))
        self.entry_output = ctk.CTkEntry(left_frame, width=280)
        self.entry_output.pack(pady=5)
        ctk.CTkButton(left_frame, text="Browse", width=120, command=self.pilih_folder_output).pack()

        ctk.CTkLabel(left_frame, text="Jumlah Video yang Ingin Digabung:").pack(anchor="w", pady=(15,0))
        ctk.CTkEntry(left_frame, textvariable=self.jumlah_video, width=280).pack(pady=5)

        ctk.CTkButton(left_frame, text="MULAI PROSES", fg_color="#2ecc71", hover_color="#27ae60",
                      height=60, width=280, corner_radius=10, font=("Arial", 18, "bold"),
                      command=self.start_render_thread).pack(pady=40)

        right_frame = ctk.CTkFrame(self, corner_radius=10)
        right_frame.pack(side="right", fill="both", expand=True, padx=15, pady=15)

        self.label_status = ctk.CTkLabel(right_frame, textvariable=self.status_text, wraplength=320,
                                         justify="left", font=("Arial", 13))
        self.label_status.pack(anchor="nw", pady=15, padx=15)

        self.progress_bar = ctk.CTkProgressBar(right_frame, width=300, height=20, mode="determinate",
                                               variable=self.progress_value, fg_color="#333333", progress_color="#00cc66")
        self.progress_bar.pack(pady=10, padx=15)
        self.progress_bar.set(0)

        self.percent_label = ctk.CTkLabel(right_frame, text="0%", font=("Arial", 16, "bold"))
        self.percent_label.pack(pady=5)

    def pilih_folder_sumber(self):
        folder = filedialog.askdirectory(title="Pilih Folder Sumber Video")
        if folder:
            self.folder_sumber = folder
            self.entry_sumber.delete(0, "end")
            self.entry_sumber.insert(0, folder)
            self.update_status()

    def pilih_folder_output(self):
        folder = filedialog.askdirectory(title="Pilih Folder Output")
        if folder:
            self.folder_output = folder
            self.entry_output.delete(0, "end")
            self.entry_output.insert(0, folder)

    def update_status(self):
        if not self.folder_sumber:
            return
        videos = [f for f in os.listdir(self.folder_sumber) if f.lower().endswith(('.mp4', '.mov', '.avi', '.mkv'))]
        total = len(videos)
        self.status_text.set(f"Folder dipilih:\n{self.folder_sumber}\n\nTotal video ditemukan: {total} file")
        if total == 0:
            messagebox.showwarning("Peringatan", "Tidak ada video yang didukung di folder tersebut!")

    def start_render_thread(self):
        if not self.folder_sumber or not self.folder_output:
            messagebox.showerror("Error", "Pilih folder sumber dan output terlebih dahulu!")
            return
        threading.Thread(target=self.proses_render, daemon=True).start()

    def proses_render(self):
        self.status_text.set("Memulai proses...\n")
        self.progress_value.set(0)
        self.percent_label.configure(text="0%")
        self.update_idletasks()

        try:
            jumlah = self.jumlah_video.get()
            if jumlah <= 0:
                raise ValueError("Jumlah video harus lebih dari 0")

            videos = [f for f in os.listdir(self.folder_sumber) if f.lower().endswith(('.mp4', '.mov', '.avi', '.mkv'))]
            if len(videos) < jumlah:
                raise ValueError(f"Hanya ada {len(videos)} video, kurang dari {jumlah}!")

            random.seed(os.urandom(16) + str(time.time()).encode() + str(os.getpid()).encode())
            random.shuffle(videos)

            selected = videos[:jumlah]

            self.status_text.set("Normalisasi timescale setiap video..")
            self.progress_bar.configure(mode="indeterminate")
            self.progress_bar.start()
            self.update_idletasks()

            normalized_files = []
            for idx, v in enumerate(selected):
                input_path = os.path.join(self.folder_sumber, v).replace('\\', '/')
                norm_path = os.path.join(self.folder_output, f"norm_{idx}_{os.path.basename(v)}")
                norm_cmd = [
                    'ffmpeg', '-y', '-i', input_path,
                    '-c', 'copy', '-video_track_timescale', '60000',
                    '-fflags', '+genpts', norm_path
                ]
                result_norm = subprocess.run(norm_cmd, capture_output=True, text=True, creationflags=HIDE_WINDOW)
                if result_norm.returncode != 0:
                    raise RuntimeError(f"Normalisasi gagal pada {v}: {result_norm.stderr}")

                normalized_files.append(norm_path)

                progress = (idx + 1) / len(selected)
                self.progress_value.set(progress)
                self.percent_label.configure(text=f"{int(progress * 100)}%")
                self.update_idletasks()

            self.progress_bar.stop()
            self.progress_bar.configure(mode="determinate")

            list_path = os.path.join(self.folder_output, 'temp_concat_list.txt')
            with open(list_path, 'w', encoding='utf-8') as f:
                for nf in normalized_files:
                    safe_path = nf.replace('\\', '/')
                    f.write(f"file '{safe_path}'\n")

            output_file = os.path.join(self.folder_output, f"{self.nama_output.get()}.mp4").replace('\\', '/')

            self.status_text.set(f"Merender {jumlah} video...\nMenggabungkan...\nOutput: {output_file}")

            cmd = [
                'ffmpeg', '-y', '-f', 'concat', '-safe', '0',
                '-i', list_path, '-c', 'copy', output_file
            ]

            result = subprocess.run(cmd, capture_output=True, text=True, creationflags=HIDE_WINDOW)

            # Simulasi progress akhir
            for i in range(101):
                self.progress_value.set(i / 100)
                self.percent_label.configure(text=f"{i}%")
                self.update_idletasks()
                time.sleep(0.01)

            # Cleanup
            if os.path.exists(list_path):
                os.remove(list_path)
            for nf in normalized_files:
                if os.path.exists(nf):
                    os.remove(nf)

            if result.returncode == 0:
                self.status_text.set(f"SUKSES!\nFile: {output_file}")
                messagebox.showinfo("Sukses", f"Render selesai!\n{output_file}")
            else:
                error_msg = result.stderr.strip() or "Gagal tanpa detail."
                log_path = os.path.join(self.folder_output, 'render_log.txt')
                with open(log_path, 'w', encoding='utf-8') as log:
                    log.write(f"Command: {' '.join(cmd)}\n\nError:\n{error_msg}\n\nFiles used:\n" + "\n".join(selected))
                self.status_text.set(f"GAGAL!\nCek render_log.txt.\nDetail: {error_msg[:200]}...")
                messagebox.showerror("Error FFmpeg", error_msg)

        except Exception as e:
            self.status_text.set(f"ERROR: {str(e)}")
            messagebox.showerror("Error", str(e))
        finally:
            self.progress_bar.stop()
            self.progress_bar.configure(mode="determinate")
            self.progress_value.set(0)
            self.percent_label.configure(text="0%")

if __name__ == "__main__":
    app = VideoShufflerApp()
    app.mainloop()