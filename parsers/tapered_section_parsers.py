"""
变截面组解析器模块

处理TS-GROUP命令，这是一个重要的命令用于定义变截面组
"""

from typing import Dict, List, Union, Optional, Any, Set, Tuple
import re

from ..models import TsGroup


class TaperedSectionParser:
    """变截面组解析器类"""
    
    def __init__(self, parser):
        """
        初始化变截面组解析器
        
        Args:
            parser: 父解析器引用
        """
        self.parser = parser
    
    def parse_ts_group(self, lines: List[str], line_nums: List[int]):
        """
        解析TS-GROUP命令
        
        Args:
            lines: 命令行列表
            line_nums: 行号列表
        """
        if len(lines) < 2:
            self.parser.model.errors.append(f"无效的TS-GROUP命令: 缺少变截面组信息")
            return
        
        # 解析第一行获取组ID和名称
        header_line = lines[1].strip()
        header_parts = re.split(r'\s*,\s*', header_line)
        
        if len(header_parts) < 2:
            self.parser.model.errors.append(f"无效的TS-GROUP命令: 缺少组ID或名称，行号 {line_nums[1]}")
            return
        
        try:
            group_id = int(header_parts[0])
            name = header_parts[1]
        except ValueError:
            self.parser.model.errors.append(f"无效的TS-GROUP命令: 组ID必须是整数，行号 {line_nums[1]}")
            return
        
        # 解析变截面定义行
        elements = []
        sections = []
        positions = []
        
        i = 2
        while i < len(lines):
            line = lines[i].strip()
            if not line:
                i += 1
                continue
            
            # 检查是否为ELEM=行
            if line.startswith("ELEM="):
                elem_text = line[5:].strip()
                elem_ids = self.parser._parse_index_list(elem_text)
                elements.extend(elem_ids)
                i += 1
                continue
            
            # 解析截面定义行
            parts = re.split(r'\s*,\s*', line)
            if len(parts) < 2:
                self.parser.model.warnings.append(f"忽略无效的TS-GROUP行: {line}，行号 {line_nums[i]}")
                i += 1
                continue
            
            try:
                section_id = int(parts[0])
            except ValueError as e:
                self.parser.model.errors.append(f"解析TS-GROUP命令时出错: {line}，行号 {line_nums[i]}，错误: {str(e)}")
                i += 1
                continue
                
            try:
                position = float(parts[1])
            except ValueError as e:
                self.parser.model.errors.append(f"解析TS-GROUP命令时出错: {line}，行号 {line_nums[i]}，错误: {str(e)}")
                i += 1
                continue
                
            sections.append(section_id)
            positions.append(position)
            
            i += 1
        
        # 创建变截面组数据模型
        ts_group_data = TsGroup(
            id=group_id,
            name=name,
            elements=elements,
            sections=sections,
            positions=positions,
            raw_lines=lines,
            line_nums=line_nums
        )
        
        self.parser.model.add_command(f"TS-GROUP_{group_id}", ts_group_data)
