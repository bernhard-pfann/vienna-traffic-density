import os
from typing import Dict, List, Tuple

import matplotlib.pyplot as plt
import networkx as nx
import seaborn as sns
from matplotlib.cm import register_cmap
from matplotlib.colors import LinearSegmentedColormap

import params.config as conf


def get_colors(n: int) -> None:
    """A function to set a color map for charts in matplotlib."""
    
    color_dict = {
        "orange": "#ffd166", 
        "green": "#06d6a0", 
        "red": "#ef476f"
    }

    color_list = list(color_dict.values())
    cmap = LinearSegmentedColormap.from_list(name="custom", colors=color_list)
    register_cmap("vienna-roads", cmap)
    
    if n: cmap = sns.color_palette(palette="vienna-roads", n_colors=n, desat=1)
    return cmap

def plot_graph(
    G: nx.Graph, 
    pos: Dict[int, Tuple[float, float]], 
    colors: List[str], 
    filename: str
) -> None:

    plt.figure(figsize=(15,12))
    nx.draw(
        G,
        pos=pos, 
        with_labels=False,
        edge_color=colors,
        width=0.5,
        node_color="gray",
        node_size=0
    )
    filepath = os.path.join(conf.root_img, filename)
    plt.savefig(filepath, dpi=600)
