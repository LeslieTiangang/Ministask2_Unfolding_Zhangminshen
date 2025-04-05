import networkx as nx
from pathlib import Path

def extract_base(node):
    """Strictly split by the first underscore, n3_0_1 → n3"""
    return node.split('_')[0]

def unfold_graph(original_graph: nx.DiGraph, k: int) -> nx.DiGraph:
    if k < 1 or not isinstance(k, int):
        raise ValueError("k must be a positive integer")
    
    # Detect constraint edges (edges with constraint=false)
    constraint_edges = set()
    for u, v, data in original_graph.edges(data=True):
        if data.get('constraint') == 'false':
            constraint_edges.add((u, v))
    
    unfolded = nx.DiGraph()
    
    # Generate nodes (preserve original labels)
    for cycle in range(k):
        for node in original_graph.nodes:
            base = extract_base(node)
            new_node = f"{base}_{cycle}"
            unfolded.add_node(new_node, **original_graph.nodes[node])
    
    # Edge processing logic
    for cycle in range(k):
        for u, v, data in original_graph.edges(data=True):
            u_base = extract_base(u)
            v_base = extract_base(v)
            
            # Check if it's a constraint edge
            is_constraint = (u, v) in constraint_edges
            
            # Determine delta
            delta = 1 if is_constraint else 0
            dst_cycle = (cycle + delta) % k
            
            # Build new edge data
            new_data = data.copy()
            
            # Handle constraint edge attributes
            if is_constraint:
                # Only retain attributes when it's the last cycle and destination cycle is 0
                if cycle == k - 1 and dst_cycle == 0:
                    # Keep all attributes
                    pass
                else:
                    # Remove constraint, color, label attributes
                    for attr in ['constraint', 'color', 'label']:
                        if attr in new_data:
                            del new_data[attr]
            else:
                # Ensure non-constraint edges don't cross cycles
                assert dst_cycle == cycle, "Non-constraint edges cannot cross cycles"
            
            # Handle label formatting (preserve original value, just remove and re-add quotes)
            if 'label' in new_data:
                cleaned_label = str(new_data['label']).replace('"', '')
                new_data['label'] = f'"{cleaned_label}"'
            
            # Add edge to unfolded graph
            unfolded.add_edge(
                f"{u_base}_{cycle}",
                f"{v_base}_{dst_cycle}",
                **new_data
            )
    
    return unfolded

def process_unfolding(input_path: str, k: int, output_dir: str = None):
    input_path = Path(input_path)
    if not input_path.exists():
        raise FileNotFoundError(f"File not found: {input_path}")
    
    output_dir = Path(output_dir) if output_dir else input_path.parent
    output_dir.mkdir(parents=True, exist_ok=True)
    
    output_path = output_dir / f"{input_path.stem}_unfold{k}.dot"
    
    original = nx.nx_pydot.read_dot(input_path)
    unfolded = unfold_graph(original, k)
    
    with open(output_path, 'w') as f:
        f.write("digraph depgraph {\n")
        # Write node definitions
        for node, data in unfolded.nodes(data=True):
            label = data.get('label', '')
            f.write(f'    {node} [label="{label}"];\n')
        # Write edge definitions
        for u, v, data in unfolded.edges(data=True):
            attrs = []
            for attr in ['constraint', 'color', 'label']:
                if attr in data:
                    value = str(data[attr]).strip('"')
                    if attr == 'label':
                        attrs.append(f'label="{value}"')
                    else:
                        attrs.append(f'{attr}={value}')
            edge_str = f"    {u} -> {v}"
            if attrs:
                edge_str += f" [{', '.join(attrs)}]"
            edge_str += ";\n"
            f.write(edge_str)
        f.write("}\n")
    
    print(f"Processing complete, results saved to: {output_path}")

# Usage example
input_file = r"C:\self\Study\ss24\high level synthese\minitask2\input\ADPCMn-decode-771-791.dot"
output_path = r"C:\self\Study\ss24\high level synthese\minitask2\output"
process_unfolding(
    input_path=input_file,
    k=3,
    output_dir=output_path
)
