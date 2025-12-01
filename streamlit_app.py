from typing import List

import matplotlib.pyplot as plt
import pandas as pd
import streamlit as st

from main import Graph, compute_multi_stop_route, create_example_graph


def _get_graph() -> Graph:
    # Cache graf agar tidak dibuat ulang setiap interaksi
    @st.cache_resource(show_spinner=False)
    def _build() -> Graph:
        return create_example_graph()

    return _build()


def _compute_route(graph: Graph, start: str, end: str, algorithm: str):
    solver = graph.dijkstra if algorithm == "Dijkstra" else graph.astar
    cost, path = solver(start, end)
    return cost, path

def _collect_unique_edges(graph: Graph) -> List[tuple[str, str]]:
    seen = set()
    edges = []
    for source, neighbors in graph.edges.items():
        for target, _ in neighbors:
            key = tuple(sorted((source, target)))
            if key in seen:
                continue
            seen.add(key)
            edges.append((source, target))
    return edges


def _render_graph(graph: Graph, highlight_paths: List[List[str]]):
    edges = _collect_unique_edges(graph)
    fig, ax = plt.subplots(figsize=(8, 6))
    ax.set_title("Graf Distribusi (skala sederhana)")

    for node_a, node_b in edges:
        coord_a = graph.coordinates.get(node_a)
        coord_b = graph.coordinates.get(node_b)
        if not coord_a or not coord_b:
            continue
        ax.plot([coord_a[0], coord_b[0]], [coord_a[1], coord_b[1]], color="#b0b0b0", linewidth=1.5, zorder=1)

    colors = ["#ff1c1c", "#ffa500", "#1c9cff", "#7ac70c", "#8a2be2"]
    for idx, path in enumerate(highlight_paths):
        coords = [graph.coordinates.get(node) for node in path]
        if any(coord is None for coord in coords) or len(coords) < 2:
            continue
        xs = [c[0] for c in coords]
        ys = [c[1] for c in coords]
        ax.plot(xs, ys, color=colors[idx % len(colors)], linewidth=3, zorder=2)

    for name, coord in graph.coordinates.items():
        node_type = "SPBU" if name.startswith("SPBU") else ("Depot" if "Depot" in name else "Simpang")
        if node_type == "Depot":
            color = "#009900"
            size = 120
        elif node_type == "SPBU":
            color = "#0066cc"
            size = 90
        else:
            color = "#666666"
            size = 70
        ax.scatter(coord[0], coord[1], s=size, color=color, edgecolors="white", linewidths=0.8, zorder=3)
        ax.text(coord[0], coord[1] + 0.0015, name, fontsize=9, ha="center", va="bottom", zorder=4)

    ax.set_xlabel("X")
    ax.set_ylabel("Y")
    ax.grid(True, alpha=0.3)
    ax.set_aspect("equal", adjustable="datalim")
    ax.margins(x=0.1, y=0.12)
    fig.tight_layout()
    return fig


st.set_page_config(page_title="Distribusi BBM Balikpapan", layout="wide")
st.title("Optimasi Jalur Distribusi BBM")

st.markdown(
    """
    Aplikasi ini membandingkan algoritma **Dijkstra** dan **A*** untuk menentukan rute tercepat
    dari depot ke SPBU tujuan. Data koordinat dan waktu tempuh masih berupa contoh—ganti dengan
    data lapangan agar hasil lebih akurat.
    """
)

graph = _get_graph()
all_locations = sorted(graph.nodes)
start_node = next((name for name in all_locations if "Depot" in name), all_locations[0])
dest_options = [name for name in all_locations if name != start_node]

if "highlight_routes" not in st.session_state:
    st.session_state["highlight_routes"] = []

with st.sidebar:
    st.header("Pengaturan")
    algorithm = st.radio("Algoritma", ["Dijkstra", "A*"])
    single_destination = st.selectbox("Tujuan tunggal", dest_options, index=0 if dest_options else None)
    multi_destinations = st.multiselect("Tujuan jamak", dest_options)
    enable_multi_stop = st.checkbox("Hitung rute multi tujuan (sekali jalan)")
    return_to_start = st.checkbox("Kembali ke depot setelah distribusi", value=False)

    st.caption("Hint: gunakan tombol di bawah untuk menjalankan perhitungan.")
    run_single = st.button("Cari rute tunggal")
    run_multi = st.button("Cari rute jamak")

col_result, col_map = st.columns([1, 1])

with col_result:
    st.subheader("Hasil Perhitungan")

    if run_single:
        cost, path = _compute_route(graph, start_node, single_destination, algorithm)
        if cost == float("inf") or not path:
            st.session_state["highlight_routes"] = []
            st.error(f"Tidak ada rute dari {start_node} ke {single_destination}.")
        else:
            st.session_state["highlight_routes"] = [path]
            st.success(f"{algorithm} {start_node} → {single_destination}")
            st.write({"rute": path, "total waktu (menit)": round(cost, 2)})

    if run_multi:
        if not multi_destinations:
            st.warning("Pilih minimal satu tujuan di daftar 'Tujuan jamak'.")
        else:
            rows = []
            highlights = []
            if enable_multi_stop:
                try:
                    total_cost, route_path = compute_multi_stop_route(
                        graph,
                        start_node,
                        multi_destinations,
                        algorithm,
                        return_to_start=return_to_start,
                    )
                except ValueError as exc:
                    st.error(str(exc))
                    st.session_state["highlight_routes"] = []
                else:
                    if total_cost == float("inf") or not route_path:
                        st.error("Tidak ditemukan rute yang mencakup semua tujuan.")
                        st.session_state["highlight_routes"] = []
                    else:
                        st.success(
                            f"Rute multi tujuan ({algorithm}) dengan total waktu {total_cost:.1f} menit"
                        )
                        st.write({"rute": route_path})
                        st.session_state["highlight_routes"] = [route_path]
                        rows.append(
                            {
                                "Tujuan": " → ".join([start_node] + multi_destinations + ([start_node] if return_to_start else [])),
                                "Status": "OK",
                                "Rute": route_path,
                                "Total waktu (menit)": round(total_cost, 2),
                            }
                        )
                        st.dataframe(pd.DataFrame(rows))
            else:
                for dest in multi_destinations:
                    cost, path = _compute_route(graph, start_node, dest, algorithm)
                    status = "OK"
                    if cost == float("inf") or not path:
                        status = "Tidak tersedia"
                    rows.append(
                        {
                            "Tujuan": dest,
                            "Status": status,
                            "Rute": path if status == "OK" else [],
                            "Total waktu (menit)": round(cost, 2) if status == "OK" else None,
                        }
                    )
                    if status == "OK":
                        highlights.append(path)
                st.dataframe(pd.DataFrame(rows))
                st.session_state["highlight_routes"] = highlights

with col_map:
    st.subheader("Visualisasi Graf")
    if not graph.coordinates:
        st.info("Belum ada koordinat yang terekam pada graf.")
    else:
        fig = _render_graph(graph, st.session_state.get("highlight_routes", []))
        st.pyplot(fig)

