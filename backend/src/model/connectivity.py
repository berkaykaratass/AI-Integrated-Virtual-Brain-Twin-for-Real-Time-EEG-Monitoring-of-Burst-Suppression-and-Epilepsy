import networkx as nx
import numpy as np

def generate_brain_network(n_nodes: int, method: str = 'small_world', **kwargs) -> np.ndarray:
    """
    Generates a connectivity matrix representing a brain network.
    
    Args:
        n_nodes (int): Number of nodes (regions/populations).
        method (str): 'small_world', 'random', or 'fully_connected'.
        **kwargs: Additional arguments for networkx generators.
        
    Returns:
        np.ndarray: Adjacency matrix (A_ij).
    """
    if method == 'small_world':
        # Watts-Strogatz small-world graph
        # k: Each node is joined with its k nearest neighbors in a ring topology.
        # p: The probability of rewiring each edge.
        k = kwargs.get('k', 4)
        p = kwargs.get('p', 0.1)
        G = nx.watts_strogatz_graph(n=n_nodes, k=k, p=p)
        
    elif method == 'random':
        # Erdos-Renyi random graph
        p = kwargs.get('p', 0.2)
        G = nx.erdos_renyi_graph(n=n_nodes, p=p)
        
    elif method == 'fully_connected':
        G = nx.complete_graph(n=n_nodes)
        
    else:
        raise ValueError(f"Unknown method: {method}")
        
    # Get adjacency matrix as numpy array
    adj_matrix = nx.to_numpy_array(G)
    
    # Optional: ensure symmetry (undirected) - networkx generators usually do this
    # Optional: remove self-loops (diagonal = 0)
    np.fill_diagonal(adj_matrix, 0)
    
    return adj_matrix
