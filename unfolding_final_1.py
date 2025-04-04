import networkx as nx
from pathlib import Path

def extract_base(node):
    """严格按第一个下划线拆分，n3_0_1 → n3"""
    return node.split('_')[0]

def unfold_graph(original_graph: nx.DiGraph, k: int) -> nx.DiGraph:
    if k < 1 or not isinstance(k, int):
        raise ValueError("k必须为正整数")
    
    # 检测约束边（具有constraint=false的边）
    constraint_edges = set()
    for u, v, data in original_graph.edges(data=True):
        if data.get('constraint') == 'false':
            constraint_edges.add((u, v))
    
    unfolded = nx.DiGraph()
    
    # 生成节点（保留原始标签）
    for cycle in range(k):
        for node in original_graph.nodes:
            base = extract_base(node)
            new_node = f"{base}_{cycle}"
            unfolded.add_node(new_node, **original_graph.nodes[node])
    
    # 边处理逻辑
    for cycle in range(k):
        for u, v, data in original_graph.edges(data=True):
            u_base = extract_base(u)
            v_base = extract_base(v)
            
            # 判断是否是约束边
            is_constraint = (u, v) in constraint_edges
            
            # 确定delta
            delta = 1 if is_constraint else 0
            dst_cycle = (cycle + delta) % k
            
            # 构建新边数据
            new_data = data.copy()
            
            # 处理约束边的属性
            if is_constraint:
                # 只有当是最后一个周期且目标周期为0时保留属性
                if cycle == k - 1 and dst_cycle == 0:
                    # 保留所有属性
                    pass
                else:
                    # 移除constraint, color, label属性
                    for attr in ['constraint', 'color', 'label']:
                        if attr in new_data:
                            del new_data[attr]
            else:
                # 确保非约束边不跨周期
                assert dst_cycle == cycle, "非约束边不能跨周期"
            
            # 处理label的格式（保留原始值，仅去除引号后重新包裹）
            if 'label' in new_data:
                cleaned_label = str(new_data['label']).replace('"', '')
                new_data['label'] = f'"{cleaned_label}"'
            
            # 添加边到展开图
            unfolded.add_edge(
                f"{u_base}_{cycle}",
                f"{v_base}_{dst_cycle}",
                **new_data
            )
    
    return unfolded

def process_unfolding(input_path: str, k: int, output_dir: str = None):
    input_path = Path(input_path)
    if not input_path.exists():
        raise FileNotFoundError(f"文件未找到: {input_path}")
    
    output_dir = Path(output_dir) if output_dir else input_path.parent
    output_dir.mkdir(parents=True, exist_ok=True)
    
    output_path = output_dir / f"{input_path.stem}_unfold{k}.dot"
    
    original = nx.nx_pydot.read_dot(input_path)
    unfolded = unfold_graph(original, k)
    
    with open(output_path, 'w') as f:
        f.write("digraph depgraph {\n")
        # 写入节点定义
        for node, data in unfolded.nodes(data=True):
            label = data.get('label', '')
            f.write(f'    {node} [label="{label}"];\n')
        # 写入边定义
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
    
    print(f"处理完成，结果已保存至: {output_path}")

# 使用示例
input_file = r"C:\self\Study\ss24\high level synthese\minitask2\input\ADPCMn-decode-771-791.dot"
output_path = r"C:\self\Study\ss24\high level synthese\minitask2\output"
process_unfolding(
    input_path=input_file,
    k=3,
    output_dir=output_path
)