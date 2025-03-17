"""
边界条件解析器模块

处理CONSTRAINT、SPRING等命令
"""

from typing import Dict, List, Union, Optional, Any, Set, Tuple
import re

from ..models import (
    Constraint, Spring
)


class ConstraintParser:
    """边界条件解析器类"""
    
    def __init__(self, parser):
        """
        初始化边界条件解析器
        
        Args:
            parser: 父解析器引用
        """
        self.parser = parser
    
    def parse_constraint(self, lines: List[str], line_nums: List[int]):
        """
        解析CONSTRAINT命令
        
        Args:
            lines: 命令行列表
            line_nums: 行号列表
        """
        constraints = []
        
        # 跳过命令行
        for i, line in enumerate(lines[1:], 1):
            line = line.strip()
            if not line:
                continue
            
            parts = re.split(r'\s*,\s*', line)
            if len(parts) < 2:  # 至少需要节点/单元索引和约束类型
                self.parser.model.errors.append(f"无效的约束定义: {line}，行号 {line_nums[i]}")
                continue
            
            try:
                # 解析节点/单元索引表达式
                index_expr = parts[0]
                ids = self.parser._parse_index_list(index_expr)
                
                # 解析约束类型
                constraint_type = parts[1]
                
                # 解析自由度约束
                dof_values = [0] * 6  # 默认为0，表示不约束
                if len(parts) > 2:
                    for j in range(2, min(8, len(parts))):
                        try:
                            dof_values[j-2] = int(parts[j])
                        except (ValueError, IndexError):
                            pass
                
                # 解析可选参数
                options = {}
                if len(parts) > 8:
                    options_str = ' '.join(parts[8:])
                    
                    for pattern in [r'GROUP=(\w+)', r'LOCAL=(\d+)', r'ACTIVE=(\w+)']:
                        match = re.search(pattern, options_str)
                        if match:
                            key = pattern.split('=')[0].lower()
                            options[key] = match.group(1)
                
                constraints.append({
                    'ids': ids,
                    'type': constraint_type,
                    'dof': dof_values,
                    'options': options
                })
            
            except ValueError as e:
                self.parser.model.errors.append(f"解析约束定义时出错: {line}，行号 {line_nums[i]}，错误: {str(e)}")
        
        constraint_data = Constraint(constraints=constraints, raw_lines=lines, line_nums=line_nums)
        self.parser.model.add_command("CONSTRAINT", constraint_data)
    
    def parse_spring(self, lines: List[str], line_nums: List[int]):
        """
        解析SPRING命令
        
        Args:
            lines: 命令行列表
            line_nums: 行号列表
        """
        springs = []
        
        # 跳过命令行
        for i, line in enumerate(lines[1:], 1):
            line = line.strip()
            if not line:
                continue
            
            parts = re.split(r'\s*,\s*', line)
            if len(parts) < 8:  # 至少需要节点索引和6个刚度值
                self.parser.model.errors.append(f"无效的弹簧定义: {line}，行号 {line_nums[i]}")
                continue
            
            try:
                # 解析节点索引表达式
                index_expr = parts[0]
                ids = self.parser._parse_index_list(index_expr)
                
                # 解析6个刚度值
                spring_values = []
                for j in range(1, 7):
                    try:
                        spring_values.append(float(parts[j]))
                    except (ValueError, IndexError):
                        spring_values.append(0.0)  # 默认为0
                
                # 解析可选参数
                options = {}
                if len(parts) > 7:
                    options_str = ' '.join(parts[7:])
                    
                    for pattern in [r'LOCAL=(\d+)', r'ACTIVE=(\w+)']:
                        match = re.search(pattern, options_str)
                        if match:
                            key = pattern.split('=')[0].lower()
                            options[key] = match.group(1)
                
                springs.append({
                    'ids': ids,
                    'stiffness': spring_values,
                    'options': options
                })
            
            except ValueError as e:
                self.parser.model.errors.append(f"解析弹簧定义时出错: {line}，行号 {line_nums[i]}，错误: {str(e)}")
        
        spring_data = Spring(springs=springs, raw_lines=lines, line_nums=line_nums)
        self.parser.model.add_command("SPRING", spring_data)
