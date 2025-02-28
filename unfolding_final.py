import networkx as nx
from pathlib import Path

def unfold_graph(original_graph: nx.DiGraph, k: int) -> nx.DiGraph:
    """
    Unfold a periodic graph into k temporal copies with cycle wrapping.
    
    Args:
        original_graph: Input graph with 'label' attributes on edges
        k: Unfolding factor (positive integer)
    
    Returns:
        Unfolded graph with node naming: nx_y (x=base node id, y=cycle)
    """
    if k < 1 or not isinstance(k, int):
        raise ValueError("k must be a positive integer")
    
    unfolded = nx.DiGraph()
    
    # Create temporal nodes
    for cycle in range(k):
        for node in original_graph.nodes:
            parts = node.split('_')
            if len(parts) > 1 and parts[-1].isdigit():
                base_name = '_'.join(parts[:-1])
            else:
                base_name = node
            unfolded.add_node(f"{base_name}_{cycle}")
    
    # Create temporal edges
    for cycle in range(k):
        for u, v, data in original_graph.edges(data=True):
            new_data = {}
            delta = None
            
            # 处理时间标签
            if 'label' in data:
                delta_str = data['label'].strip('"')
                try:
                    delta = int(delta_str)
                except ValueError:
                    raise ValueError(f"Invalid label value '{delta_str}' on edge {u}->{v}")
                if delta < 0:
                    raise ValueError(f"Negative delta {delta} on edge {u}->{v}")
                dst_cycle = (cycle + delta) % k
                new_data['label'] = data['label']  # 保留原始标签格式
            else:
                dst_cycle = cycle  # 没有时间标签时保持当前周期
            
            # 复制其他属性
            for attr in ['constraint', 'color']:
                if attr in data:
                    new_data[attr] = data[attr]
            
            # 处理节点基名称
            u_base = '_'.join(u.split('_')[:-1]) if len(u.split('_')) > 1 and u.split('_')[-1].isdigit() else u
            v_base = '_'.join(v.split('_')[:-1]) if len(v.split('_')) > 1 and v.split('_')[-1].isdigit() else v
            
            src = f"{u_base}_{cycle}"
            dst = f"{v_base}_{dst_cycle}"
            
            unfolded.add_edge(src, dst, **new_data)
    
    return unfolded

def process_unfolding(input_path: str, k: int, output_dir: str = None):
    """
    Complete processing pipeline for graph unfolding
    """
    input_path = Path(input_path.replace('\\', '/'))
    if not input_path.exists():
        raise FileNotFoundError(f"Input file not found: {input_path}")
    
    output_dir = Path(output_dir) if output_dir else input_path.parent
    output_dir.mkdir(parents=True, exist_ok=True)
    
    base_name = input_path.stem
    if "_unfoldingFactor_" in base_name:
        new_name = base_name.rsplit("_", 1)[0] + f"_unfoldingFactor_{k}"
    else:
        new_name = f"{base_name}_unfoldingFactor_{k}"
    output_path = output_dir / f"{new_name}.dot"
    
    original = nx.nx_pydot.read_dot(input_path)
    unfolded = unfold_graph(original, k)
    
    # 自定义DOT格式输出
    with open(output_path, 'w') as f:
        f.write("digraph depgraph {\n")
        for u, v, data in unfolded.edges(data=True):
            attrs = []
            # 按指定顺序处理属性
            if 'constraint' in data:
                attrs.append(f'constraint={data["constraint"]}')
            if 'color' in data:
                attrs.append(f'color={data["color"]}')
            if 'label' in data:
                label = str(data["label"]).strip('"')
                attrs.append(f'label="{label}"')
            f.write(f"    {u} -> {v}")
            if attrs:
                f.write(f" [{', '.join(attrs)}]")
            f.write(";\n")
        f.write("}\n")
    
    print(f"Unfolding completed. Results saved to: {output_path}")


# Usage example

input_file = r"C:\self\Study\ss24\high level synthese\minitask2\scheduler-framework\scheduler-framework for Moodle\unfoldingExamples\testCyclic_unfoldingFactor_1.dot"

process_unfolding(
    input_path=input_file,
    k=3,  # Unfolding factor
    output_dir=r"C:\self\Study\ss24\high level synthese\minitask2\output"
)
