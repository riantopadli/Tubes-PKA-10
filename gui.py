import tkinter as tk
from tkinter import ttk, messagebox
from main import create_example_graph, location_coords

class MapGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Aplikasi Mapping Pengantar BBM - Graph Map GUI")
        self.graph = create_example_graph()
        self.locations = list(location_coords.keys())
        # Scaling and canvas size setup
        self.margin = 50
        self.size = 600
        self.scale = 40  # scale factor for coords
        self.canvas = tk.Canvas(root, width=self.size + self.margin*2, height=self.size + self.margin*2, bg="white")
        self.canvas.pack()

        form = tk.Frame(root)
        form.pack(pady=5)
        self.selected_alg = tk.StringVar(value="Dijkstra")
        tk.Label(form, text="Asal:").pack(side=tk.LEFT)
        self.combo_from = ttk.Combobox(form, values=self.locations, state="readonly")
        self.combo_from.set(self.locations[0])
        self.combo_from.pack(side=tk.LEFT)
        tk.Label(form, text="Tujuan:").pack(side=tk.LEFT)
        self.combo_to = ttk.Combobox(form, values=self.locations, state="readonly")
        self.combo_to.set(self.locations[1])
        self.combo_to.pack(side=tk.LEFT)

        self.alg_option = ttk.Combobox(form, values=["Dijkstra", "A*"] , state="readonly", textvariable=self.selected_alg)
        self.alg_option.pack(side=tk.LEFT, padx=10)
        btn = tk.Button(form, text="Cari Rute", command=self.find_route)
        btn.pack(side=tk.LEFT, padx=5)
        
        self.draw_map()
        self.route_line = None

    def get_canvas_xy(self, coord):
        # convert (x, y) to canvas XY
        x, y = coord
        # agar layout lebih proper, kayak map
        cx = self.margin + x * self.scale
        cy = self.margin + (self.size//self.scale - y) * self.scale
        return cx, cy

    def draw_map(self):
        self.canvas.delete("all")
        # Draw edges
        for n in self.locations:
            for neighbor, _ in self.graph.edges[n]:
                if self.locations.index(neighbor) > self.locations.index(n):
                    x1, y1 = self.get_canvas_xy(location_coords[n])
                    x2, y2 = self.get_canvas_xy(location_coords[neighbor])
                    self.canvas.create_line(x1, y1, x2, y2, fill="#b0b0b0", width=2)
        # Draw nodes
        for node, coord in location_coords.items():
            x, y = self.get_canvas_xy(coord)
            color = "blue" if node.startswith("Pom") else ("green" if node == "Depot" else "gray")
            r = 15
            self.canvas.create_oval(x-r, y-r, x+r, y+r, fill=color)
            self.canvas.create_text(x, y, text=node, fill="white")

    def find_route(self):
        src = self.combo_from.get()
        dst = self.combo_to.get()
        alg = self.selected_alg.get()
        if src == dst:
            messagebox.showinfo("Info", "Asal dan tujuan tidak boleh sama!")
            return
        if alg == "Dijkstra":
            _, path = self.graph.dijkstra(src, dst)
        else:
            _, path = self.graph.astar(src, dst)
        self.draw_map()
        if len(path)>1:
            # highlight path
            for i in range(len(path)-1):
                x1, y1 = self.get_canvas_xy(location_coords[path[i]])
                x2, y2 = self.get_canvas_xy(location_coords[path[i+1]])
                self.canvas.create_line(x1, y1, x2, y2, fill="#ff1c1c", width=5)
            # Bring nodes to front again
            for node, coord in location_coords.items():
                x, y = self.get_canvas_xy(coord)
                color = "blue" if node.startswith("Pom") else ("green" if node == "Depot" else "gray")
                r = 15
                self.canvas.create_oval(x-r, y-r, x+r, y+r, fill=color)
                self.canvas.create_text(x, y, text=node, fill="white")
        # Show popup
        messagebox.showinfo("Hasil Rute", f"Rute terbaik: {path}")

if __name__ == "__main__":
    root = tk.Tk()
    app = MapGUI(root)
    root.mainloop()

