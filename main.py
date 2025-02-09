import os
import json
import uuid
import shutil
from zipfile import ZipFile
import tkinter as tk
from tkinter import filedialog, messagebox, simpledialog

# Get the user's Minecraft skin packs directory
MINECRAFT_SKIN_PACKS_PATH = os.path.join(
    os.getenv("LOCALAPPDATA"),
    "Packages",
    "Microsoft.MinecraftUWP_8wekyb3d8bbwe",
    "LocalState",
    "games",
    "com.mojang",
    "skin_packs"
)

class SkinPackApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Minecraft Skin Pack Generator")
        self.root.geometry("600x500")

        # Skin pack name input
        tk.Label(root, text="Enter Skin Pack Name:").pack(pady=5)
        self.pack_name_entry = tk.Entry(root, width=40)
        self.pack_name_entry.pack(pady=5)

        # Buttons
        tk.Button(root, text="Add Skin", command=self.add_skin).pack(pady=5)

        # Skin Listbox
        self.skins = []
        self.skin_listbox = tk.Listbox(root, width=50, height=10)
        self.skin_listbox.pack(pady=5)
        self.skin_listbox.bind("<Double-1>", self.edit_skin_name)

        tk.Button(root, text="Generate Skin Pack", command=self.generate_pack).pack(pady=10)
        tk.Button(root, text="Manage Existing Skin Packs", command=self.manage_skin_packs).pack(pady=5)

    def add_skin(self):
        file_path = filedialog.askopenfilename(filetypes=[("PNG files", "*.png")])
        if file_path:
            skin_name = os.path.basename(file_path).split('.')[0]
            variant = messagebox.askquestion("Select Variant", "Slim Skin?", icon='question')
            geometry_type = "geometry.humanoid.customSlim" if variant == "yes" else "geometry.humanoid.custom"
            self.skins.append({"name": skin_name, "file": file_path, "geometry": geometry_type})
            self.skin_listbox.insert(tk.END, f"{skin_name} ({'Slim' if variant == 'yes' else 'Normal'})")

    def edit_skin_name(self, event):
        try:
            selection = self.skin_listbox.curselection()[0]
            new_name = simpledialog.askstring("Edit Skin Name", "Enter new skin name:", initialvalue=self.skins[selection]["name"])
            if new_name:
                self.skins[selection]["name"] = new_name
                self.skin_listbox.delete(selection)
                self.skin_listbox.insert(selection, f"{new_name} ({'Slim' if self.skins[selection]['geometry'] == 'geometry.humanoid.customSlim' else 'Normal'})")
        except IndexError:
            pass  # Ignore if no selection is made

    def generate_pack(self):
        pack_name = self.pack_name_entry.get().strip()
        if not pack_name:
            messagebox.showerror("Error", "Please enter a skin pack name!")
            return

        if not self.skins:
            messagebox.showerror("Error", "Please add at least one skin!")
            return

        save_dir = filedialog.askdirectory(title="Select Save Location")
        if not save_dir:
            return  # User canceled

        output_folder = os.path.join(save_dir, pack_name)
        os.makedirs(output_folder, exist_ok=True)
        os.makedirs(f"{output_folder}/texts", exist_ok=True)

        # Generate manifest.json
        manifest_data = {
            "header": {
                "name": pack_name,
                "version": [1, 0, 0],
                "uuid": str(uuid.uuid4())
            },
            "modules": [
                {
                    "version": [1, 0, 0],
                    "type": "skin_pack",
                    "uuid": str(uuid.uuid4())
                }
            ],
            "format_version": 1
        }

        with open(f"{output_folder}/manifest.json", "w") as f:
            json.dump(manifest_data, f, indent=4)

        # Generate skins.json
        skins_list = []
        lang_entries = [f"skinpack.{pack_name}={pack_name} Pack"]
        for index, skin in enumerate(self.skins, start=1):
            texture_name = f"skin{index}.png"
            shutil.copy(skin["file"], f"{output_folder}/{texture_name}")

            skins_list.append({
                "localization_name": skin["name"],
                "geometry": skin["geometry"],
                "texture": texture_name,
                "type": "free"
            })

            lang_entries.append(f"skin.{pack_name}.skin{index}={skin['name']}")

        skins_json = {
            "serialize_name": pack_name,
            "localization_name": pack_name,
            "skins": skins_list
        }

        with open(f"{output_folder}/skins.json", "w") as f:
            json.dump(skins_json, f, indent=4)

        # Generate en_us.lang
        with open(f"{output_folder}/texts/en_us.lang", "w") as f:
            f.write("\n".join(lang_entries))

        # Create ZIP and rename to MCPACK
        zip_name = os.path.join(save_dir, f"{pack_name}.zip")
        mcpack_name = os.path.join(save_dir, f"{pack_name}.mcpack")

        with ZipFile(zip_name, "w") as zipf:
            for foldername, subfolders, filenames in os.walk(output_folder):
                for filename in filenames:
                    file_path = os.path.join(foldername, filename)
                    zipf.write(file_path, os.path.relpath(file_path, save_dir))

        shutil.move(zip_name, mcpack_name)
        messagebox.showinfo("Success", f"Skin pack created: {mcpack_name}")

    def manage_skin_packs(self):
        if not os.path.exists(MINECRAFT_SKIN_PACKS_PATH):
            messagebox.showerror("Error", "Minecraft skin packs folder not found!")
            return

        skin_packs = [d for d in os.listdir(MINECRAFT_SKIN_PACKS_PATH) if os.path.isdir(os.path.join(MINECRAFT_SKIN_PACKS_PATH, d))]
        if not skin_packs:
            messagebox.showinfo("Info", "No skin packs found.")
            return

        manage_window = tk.Toplevel(self.root)
        manage_window.title("Manage Skin Packs")
        manage_window.geometry("400x300")

        tk.Label(manage_window, text="Select a Skin Pack to Delete:").pack(pady=5)
        listbox = tk.Listbox(manage_window, width=50, height=10)
        listbox.pack(pady=5)
        for pack in skin_packs:
            listbox.insert(tk.END, pack)

        def delete_skin_pack():
            try:
                selected_index = listbox.curselection()[0]
                selected_pack = listbox.get(selected_index)
                full_path = os.path.join(MINECRAFT_SKIN_PACKS_PATH, selected_pack)
                if messagebox.askyesno("Confirm", f"Are you sure you want to delete '{selected_pack}'?"):
                    shutil.rmtree(full_path)
                    listbox.delete(selected_index)
                    messagebox.showinfo("Success", f"Deleted {selected_pack}")
            except IndexError:
                messagebox.showwarning("Warning", "No skin pack selected.")

        tk.Button(manage_window, text="Delete Selected Skin Pack", command=delete_skin_pack).pack(pady=5)

if __name__ == "__main__":
    root = tk.Tk()
    app = SkinPackApp(root)
    root.mainloop()
