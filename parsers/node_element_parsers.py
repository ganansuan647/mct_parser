"""
节点和单元解析器模块

处理NODE、ELEMENT、GROUP等命令
"""

from typing import List
import re

from ..models import (
    Node, NodeCommand, Element, ElementCommand, ElementType,
    Group, BndrGroup, LoadGroup
)


class NodeElementParser:
    """节点和单元解析器类"""
    
    def __init__(self, parser):
        """
        初始化节点和单元解析器
        
        Args:
            parser: 父解析器引用
        """
        self.parser = parser
    
    def parse_node(self, lines: List[str], line_nums: List[int]):
        """
        解析NODE命令
        
        格式: 节点ID,X坐标,Y坐标,Z坐标
        
        Args:
            lines: 命令行列表
            line_nums: 行号列表
        """
        nodes = {}
        
        for i, line in enumerate(lines):
            # 预处理行，移除注释等
            line = self.parser._preprocess_line(line)
            if not line or line.startswith(';') or line.startswith('*'):
                continue
            
            # 使用逗号分隔字段，与旧实现保持一致
            parts = re.split(r'\s*,\s*', line)
            if len(parts) < 4:
                self.parser.model.errors.append(f"无效的节点定义: {line}，行号 {line_nums[i]}，至少需要4个字段")
                continue
            
            # 解析节点ID
            try:
                node_id = int(parts[0])
            except ValueError as e:
                self.parser.model.errors.append(f"解析节点定义时出错: {line}，行号 {line_nums[i]}，错误: {str(e)}")
                continue
            
            # 解析节点坐标
            try:
                x = float(parts[1])
            except ValueError as e:
                self.parser.model.errors.append(f"解析节点定义时出错: {line}，行号 {line_nums[i]}，错误: {str(e)}")
                continue
                
            try:
                y = float(parts[2])
            except ValueError as e:
                self.parser.model.errors.append(f"解析节点定义时出错: {line}，行号 {line_nums[i]}，错误: {str(e)}")
                continue
                
            try:
                z = float(parts[3])
            except ValueError as e:
                self.parser.model.errors.append(f"解析节点定义时出错: {line}，行号 {line_nums[i]}，错误: {str(e)}")
                continue
            
            # 解析旋转特性等其他可选参数
            cs_id = int(parts[4]) if len(parts) > 4 and parts[4].isdigit() else 0
            has_rotation = parts[5] == 'YES' if len(parts) > 5 else False
            rx = float(parts[6]) if len(parts) > 6 and parts[6].lower() != 'yes' and parts[6].lower() != 'no' else 0.0
            ry = float(parts[7]) if len(parts) > 7 else 0.0
            rz = float(parts[8]) if len(parts) > 8 else 0.0
            
            nodes[node_id] = {
                'id': node_id,
                'x': x,
                'y': y,
                'z': z,
                'cs_id': cs_id,
                'has_rotation': has_rotation,
                'rx': rx,
                'ry': ry,
                'rz': rz
            }
        
        if nodes:
            self.parser.model.add_command("NODE", {"nodes": nodes, "raw_lines": lines, "line_nums": line_nums})

    def parse_gridline(self, lines: List[str], line_nums: List[int]):
        """
        解析GRIDLINE命令
        
        Args:
            lines: 命令行列表
            line_nums: 行号列表
        """
        # 这里实现GRIDLINE命令的解析
        pass

    def parse_element(self, lines: List[str], line_nums: List[int]):
        """
        解析ELEMENT命令
        
        格式: 单元ID,类型,材料ID,截面ID,节点1,节点2,...
        
        Args:
            lines: 命令行列表
            line_nums: 行号列表
        """
        elements = {}
        
        for i, line in enumerate(lines):
            # 预处理行，移除注释等
            line = self.parser._preprocess_line(line)
            if not line or line.startswith(';') or line.startswith('*'):
                continue
            
            # 使用逗号分隔字段，与旧实现保持一致
            parts = re.split(r'\s*,\s*', line)
            if len(parts) < 7:  # elemID, type, matID, sectID, node1, node2, optional nodes
                self.parser.model.errors.append(f"无效的单元定义: {line}，行号 {line_nums[i]}，至少需要7个字段")
                continue
            
            # 解析单元ID
            try:
                elem_id = int(parts[0])
            except ValueError as e:
                self.parser.model.errors.append(f"解析单元定义时出错: {line}，行号 {line_nums[i]}，错误: {str(e)}")
                continue
            
            # 获取单元类型
            elem_type = parts[1].upper()
            
            # 解析材料ID
            try:
                mat_id = int(parts[2])
            except ValueError as e:
                self.parser.model.errors.append(f"解析单元定义时出错: {line}，行号 {line_nums[i]}，错误: {str(e)}")
                continue
            
            # 解析截面ID
            try:
                sect_id = int(parts[3])
            except ValueError as e:
                self.parser.model.errors.append(f"解析单元定义时出错: {line}，行号 {line_nums[i]}，错误: {str(e)}")
                continue
            
            # 解析节点ID列表
            nodes = []
            has_error = False
            for j in range(4, len(parts)):
                try:
                    node_id = int(parts[j])
                    nodes.append(node_id)
                except ValueError:
                    # 可能是后面的选项，而不是节点ID
                    break
            
            if len(nodes) < 2:
                self.parser.model.errors.append(f"无效的单元定义: {line}，行号 {line_nums[i]}，至少需要2个节点")
                continue
            
            elements[elem_id] = {
                'id': elem_id,
                'type': elem_type,
                'mat_id': mat_id,
                'sect_id': sect_id,
                'nodes': nodes
            }
            
            # 解析其他选项
            for j in range(4 + len(nodes), len(parts)):
                if parts[j].upper() == 'BETA':
                    if j + 1 < len(parts):
                        try:
                            elements[elem_id]['beta'] = float(parts[j+1])
                        except ValueError:
                            pass
                elif parts[j].upper() == 'LOCAL':
                    elements[elem_id]['local'] = True
        
        if elements:
            self.parser.model.add_command("ELEMENT", {"elements": elements, "raw_lines": lines, "line_nums": line_nums})

    def parse_group(self, lines: List[str], line_nums: List[int]):
        """
        解析GROUP命令
        
        格式: 组名[,节点列表][,单元列表][,平面类型]
        
        Args:
            lines: 命令行列表
            line_nums: 行号列表
        """
        groups = {}
        current_group = None
        
        for i, line in enumerate(lines):
            # 预处理行，移除注释等
            line = self.parser._preprocess_line(line)
            if not line or line.startswith(';') or line.startswith('*'):
                continue
            
            if line.startswith('NAME='):
                # 新分组定义
                name_parts = line.split('=', 1)
                if len(name_parts) > 1:
                    group_name = name_parts[1].strip()
                    current_group = {
                        'name': group_name,
                        'nodes': [],
                        'elements': []
                    }
                    groups[group_name] = current_group
            elif line.startswith('NODE=') and current_group is not None:
                # 节点定义
                node_parts = line.split('=', 1)
                if len(node_parts) > 1:
                    node_str = node_parts[1].strip()
                    node_ranges = node_str.split()
                    for node_range in node_ranges:
                        if '-' in node_range:
                            # 范围定义
                            range_parts = node_range.split('-')
                            try:
                                start = int(range_parts[0])
                                end = int(range_parts[1])
                                current_group['nodes'].extend(range(start, end + 1))
                            except (ValueError, IndexError):
                                self.parser.model.errors.append(f"无效的节点范围定义: {node_range}，行号 {line_nums[i]}")
                        else:
                            # 单个节点
                            try:
                                node_id = int(node_range)
                                current_group['nodes'].append(node_id)
                            except ValueError:
                                self.parser.model.errors.append(f"无效的节点ID定义: {node_range}，行号 {line_nums[i]}")
            elif line.startswith('ELEM=') and current_group is not None:
                # 单元定义
                elem_parts = line.split('=', 1)
                if len(elem_parts) > 1:
                    elem_str = elem_parts[1].strip()
                    elem_ranges = elem_str.split()
                    for elem_range in elem_ranges:
                        if '-' in elem_range:
                            # 范围定义
                            range_parts = elem_range.split('-')
                            try:
                                start = int(range_parts[0])
                                end = int(range_parts[1])
                                current_group['elements'].extend(range(start, end + 1))
                            except (ValueError, IndexError):
                                self.parser.model.errors.append(f"无效的单元范围定义: {elem_range}，行号 {line_nums[i]}")
                        else:
                            # 单个单元
                            try:
                                elem_id = int(elem_range)
                                current_group['elements'].append(elem_id)
                            except ValueError:
                                self.parser.model.errors.append(f"无效的单元ID定义: {elem_range}，行号 {line_nums[i]}")
        
        if groups:
            self.parser.model.add_command("GROUP", {"groups": groups, "raw_lines": lines, "line_nums": line_nums})

    def parse_bndr_group(self, lines: List[str], line_nums: List[int]):
        """
        解析BNDR-GROUP命令
        
        格式: 组名[,自动类型]
        
        Args:
            lines: 命令行列表
            line_nums: 行号列表
        """
        if not lines:
            self.parser.model.errors.append("BNDR-GROUP命令缺少数据行")
            return
        
        for i, line in enumerate(lines):
            # 预处理行，移除注释等
            line = self.parser._preprocess_line(line)
            if not line or line.startswith(';') or line.startswith('*'):
                continue
            
            # 使用逗号分隔字段
            parts = re.split(r'\s*,\s*', line)
            if len(parts) < 1:
                self.parser.model.errors.append("BNDR-GROUP命令至少需要名称参数")
                continue
            
            name = parts[0].strip()
            auto_type = 0
            
            if len(parts) > 1 and parts[1].strip():
                try:
                    auto_type = int(parts[1])
                except ValueError:
                    auto_type = parts[1]
                    self.parser.model.errors.append(f"解析命令 'BNDR-GROUP' 字段auto_type时遇到非整数值: '{parts[1]}'")
            
            bndr_group = BndrGroup(
                name=name,
                auto_type=auto_type,
                raw_lines=lines,
                line_nums=line_nums
            )
            
            self.parser.model.add_command("BNDR-GROUP", bndr_group)

    def parse_load_group(self, lines: List[str], line_nums: List[int]):
        """
        解析LOAD-GROUP命令
        
        格式: 每行一个荷载组名称
        
        Args:
            lines: 命令行列表
            line_nums: 行号列表
        """
        names = []
        
        for line in lines:
            line = self.parser._preprocess_line(line)
            if not line or line.startswith(';') or line.startswith('*'):
                continue
            
            names.append(line)
        
        load_group = LoadGroup(
            names=names,
            raw_lines=lines,
            line_nums=line_nums
        )
        
        self.parser.model.add_command("LOAD-GROUP", load_group)
