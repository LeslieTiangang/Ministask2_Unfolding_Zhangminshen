import networkx as nx
from pathlib import Path
import re

def extract_base(node):
    """严格按第一个下划线拆分，n3_0_1 → n3"""
    return node.split('_')[0]

def unfold_graph(original_graph: nx.DiGraph, k: int) -> nx.DiGraph:
    if k < 1 or not isinstance(k, int):
        raise ValueError("k必须为正整数")
    
    # 检测约束边（具有 constraint=false 的边）
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
            
            # 确定 delta
            delta = 1 if is_constraint else 0
            dst_cycle = (cycle + delta) % k
            
            # 构建新边数据
            new_data = data.copy()
            
            # 处理约束边的属性
            if is_constraint:
                # 只有当是最后一个周期且目标周期为0时保留属性
                if cycle == k - 1 and dst_cycle == 0:
                    pass  # 保留所有属性
                else:
                    # 移除 constraint, color, label 属性
                    for attr in ['constraint', 'color', 'label']:
                        if attr in new_data:
                            del new_data[attr]
            else:
                # 确保非约束边不跨周期
                assert dst_cycle == cycle, "非约束边不能跨周期"
            
            # 处理 label 的格式（保留原始值，仅去除引号后重新包裹）
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
    
    with open(output_path, 'w', encoding="utf-8") as f:
        f.write("digraph depgraph {\n")
        # 写入节点定义
        for node, data in unfolded.nodes(data=True):
            label = data.get('label', '""')  # 默认空标签为双引号 ""
            f.write(f'    {node} [label={label}];\n')  # 直接使用 label，不加额外引号
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

def process_second_pass(input_path: str, output_dir: str = None):
    """
    对第一次展开生成的 DOT 文件进行二次处理：
    保留原有的 DOT 文件内容，只是将每个节点的处理结果，格式为
      iteration:label_value;
    添加到 'digraph depgraph {' 后面（即图内容的开始处）。
    例如，节点定义 "n0_0 [label="465:ISHL"];" 中提取的结果为 "0:465:ISHL;"
    """
    input_path = Path(input_path)
    if not input_path.exists():
        raise FileNotFoundError(f"文件未找到: {input_path}")
    
    # 读取全部行
    with open(input_path, "r", encoding="utf-8") as f:
        lines = f.readlines()
    
    # 根据正则匹配节点定义行，提取节点名和 label
    new_node_lines = []  # 保存转换后新格式的节点信息
    pattern = re.compile(r'^\s*(\S+)\s+\[label="([^"]+)"\];')
    for line in lines:
        match = pattern.match(line)
        if match:
            node_name = match.group(1)
            label_val = match.group(2)
            # 从节点名提取迭代数，节点名格式形如 n0_0, n1_2 等
            parts = node_name.split('_')
            iteration = parts[-1] if len(parts) >= 2 else ""
            # 构造新格式："iteration:label_value;"
            new_line = f"    {iteration}:{label_val};\n"
            new_node_lines.append(new_line)
    
    # 查找 "digraph depgraph {" 的行号，将新的节点行插入至此行之后
    header_index = None
    for i, line in enumerate(lines):
        # 这里匹配包含 digraph 和 { 字符的行
        if re.search(r'\bdigraph\b', line) and '{' in line:
            header_index = i
            break
    
    if header_index is None:
        raise ValueError("没有找到 digraph depgraph { 的定义")
    
    # 组合新的文件内容：先写入头部，再插入新节点定义，再写入剩余内容
    new_lines = []
    new_lines.extend(lines[:header_index+1])
    new_lines.extend(new_node_lines)
    new_lines.extend(lines[header_index+1:])
    
    output_dir = Path(output_dir) if output_dir else input_path.parent
    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = output_dir / f"{input_path.stem}_with_nodename.dot"
    with open(output_path, "w", encoding="utf-8") as f:
        f.writelines(new_lines)
    
    print(f"二次处理完成，结果已保存至: {output_path}")

# 使用示例

# 第一次展开：将输入 DOT 文件展开为 k=3 个周期的图，并保存输出文件
input_file = r"C:\self\Study\ss24\high level synthese\minitask2\input\ADPCMn-decode-425-472.dot"
output_dir = r"C:\self\Study\ss24\high level synthese\minitask2\output"
k_val = 3
process_unfolding(
    input_path=input_file,
    k=k_val,
    output_dir=output_dir
)

# 根据输入文件名和 k 值构造第一次输出的文件名
unfolded_file = Path(output_dir) / f"{Path(input_file).stem}_unfold{k_val}.dot"

# 调用二次处理函数，将节点转换为 iteration:label 的新格式后，插入到原始 DOT 内容内部
process_second_pass(
    input_path=str(unfolded_file),
    output_dir=output_dir
)
