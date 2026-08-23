import os
import json
import sys
import traceback
from tkinter import Tk, ttk, messagebox, Label, Button, Entry, Toplevel, filedialog, StringVar

def global_exception_handler(exc_type, exc_value, exc_traceback):
    err_msg = "".join(traceback.format_exception(exc_type, exc_value, exc_traceback))
    print(err_msg)
    try:
        messagebox.showerror("Fatal Error", err_msg)
    except Exception:
        pass

sys.excepthook = global_exception_handler

def get_minecraft_default_dir():
    if sys.platform == "win32":
        appdata = os.getenv("APPDATA")
        if not appdata:
            return ""
        return os.path.join(appdata, ".minecraft")
    return ""

class VersionViewerApp:
    def __init__(self, root):
        self.root = root
        self.root.title("MMC-Launcher v1.1 [Version Viewer Only]")
        self.root.geometry("540x420")
        self.root.protocol("WM_DELETE_WINDOW", self.on_close)

        self.mc_default = get_minecraft_default_dir()
        self.version_root_list = []
        default_ver_folder = os.path.join(self.mc_default, "versions")
        if os.path.isdir(default_ver_folder):
            self.version_root_list.append(default_ver_folder)

        self.all_versions = []

        Label(root, text=f".minecraft path: {self.mc_default}", wraplength=520).pack(pady=3)

        frame_top = ttk.Frame(root)
        frame_top.pack(fill="x", padx=6)
        Label(frame_top, text="Filter:").pack(side="left")
        # 修复：StringVar来自tkinter顶层，不是ttk
        self.var_filter = StringVar()
        self.var_filter.trace_add("write", lambda *args: self.refresh_list())
        Entry(frame_top, textvariable=self.var_filter).pack(side="left", fill="x", expand=True, padx=5)

        frame_btn = ttk.Frame(root)
        frame_btn.pack(fill="x", padx=6, pady=3)
        Button(frame_btn, text="Add Versions Folder", command=self.add_versions_folder).pack(side="left", padx=2)
        Button(frame_btn, text="Open .minecraft", command=self.open_mc_dir).pack(side="left", padx=2)
        Button(frame_btn, text="Copy Version ID", command=self.copy_selected_id).pack(side="left", padx=2)

        self.tree = ttk.Treeview(root, columns=("verid", "srcdir"), show="headings")
        self.tree.heading("verid", text="Version ID")
        self.tree.heading("srcdir", text="Source Folder")
        self.tree.column("verid", width=260)
        self.tree.column("srcdir", width=240)
        self.tree.pack(fill="both", expand=True, padx=6, pady=4)
        self.tree.bind("<Double-1>", self.on_double_click)

        self.status_text = StringVar()
        ttk.Label(root, textvariable=self.status_text).pack(anchor="w", padx=6)

        self.refresh_list()

    def scan_versions_folder(self, folder_path):
        ver_result = []
        if not os.path.isdir(folder_path):
            return ver_result
        try:
            for name in os.listdir(folder_path):
                subdir = os.path.join(folder_path, name)
                if not os.path.isdir(subdir):
                    continue
                json_file = os.path.join(subdir, f"{name}.json")
                entry = {
                    "id": name,
                    "type": "unknown",
                    "inheritsFrom": None,
                    "assets": None,
                    "json_ok": False,
                    "jar_exists": False,
                    "jar_size": 0,
                    "source_folder": folder_path
                }
                jar_file = os.path.join(subdir, f"{name}.jar")
                if os.path.exists(jar_file):
                    entry["jar_exists"] = True
                    entry["jar_size"] = os.path.getsize(jar_file)
                if os.path.exists(json_file):
                    try:
                        with open(json_file, "r", encoding="utf-8") as f:
                            j = json.load(f)
                        entry["json_ok"] = True
                        entry["id"] = j.get("id", name)
                        entry["type"] = j.get("type", "unknown")
                        entry["inheritsFrom"] = j.get("inheritsFrom")
                        entry["assets"] = j.get("assets")
                    except Exception:
                        pass
                ver_result.append(entry)
        except Exception:
            pass
        return ver_result

    def refresh_list(self):
        for item in self.tree.get_children():
            self.tree.delete(item)
        self.all_versions.clear()
        for folder in self.version_root_list:
            vs = self.scan_versions_folder(folder)
            self.all_versions.extend(vs)
        filter_word = self.var_filter.get().lower()
        display_list = []
        for v in self.all_versions:
            vid = v["id"].lower()
            if filter_word and filter_word not in vid:
                continue
            display_list.append(v)
        for v in display_list:
            self.tree.insert("", "end", values=(v["id"], os.path.basename(v["source_folder"])))
        self.status_text.set(f"Total scanned versions: {len(display_list)} | Source folders: {len(self.version_root_list)}")

    def add_versions_folder(self):
        sel = filedialog.askdirectory(title="Select versions folder")
        if not sel:
            return
        sel = os.path.normpath(sel)
        if sel in self.version_root_list:
            messagebox.showinfo("Info","This folder is already added.")
            return
        self.version_root_list.append(sel)
        self.refresh_list()

    def on_double_click(self, event):
        sel = self.tree.selection()
        if not sel:
            return
        idx = self.tree.index(sel[0])
        ver_info = self.all_versions[idx]
        win = Toplevel(self.root)
        win.title(f"Version Detail: {ver_info['id']}")
        win.geometry("460x320")
        lines = []
        lines.append(f"Version ID: {ver_info['id']}")
        lines.append(f"Type: {ver_info['type']}")
        lines.append(f"InheritsFrom: {ver_info['inheritsFrom'] or 'None'}")
        lines.append(f"Assets index: {ver_info['assets'] or 'None'}")
        lines.append(f"JSON parsed ok: {ver_info['json_ok']}")
        lines.append(f"Jar file exists: {ver_info['jar_exists']}")
        sz_kb = round(ver_info["jar_size"] / 1024,1)
        lines.append(f"Jar size: {sz_kb} KB")
        lines.append(f"Source folder: {ver_info['source_folder']}")
        content = "\n".join(lines)
        Label(win, text=content, justify="left").pack(padx=12,pady=12)

    def copy_selected_id(self):
        sel = self.tree.selection()
        if not sel:
            messagebox.showwarning("Warning","Select one version first!")
            return
        idx = self.tree.index(sel[0])
        vid = self.all_versions[idx]["id"]
        try:
            self.root.clipboard_clear()
            self.root.clipboard_append(vid)
            messagebox.showinfo("Copied",f"Version ID copied:\n{vid}")
        except Exception:
            messagebox.showwarning("Warning","Clipboard access failed")

    def open_mc_dir(self):
        path = self.mc_default
        if os.path.isdir(path):
            os.startfile(path)
        else:
            messagebox.showwarning("Not found",".minecraft folder not found.")

    def on_close(self):
        self.root.destroy()

if __name__ == "__main__":
    root = Tk()
    app = VersionViewerApp(root)
    root.mainloop()
