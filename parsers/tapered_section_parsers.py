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
    
    def parse_element_list(self, elem_list_str: str) -> List[int]:
        """
        解析元素列表字符串，支持多种表达式格式
        
        Args:
            elem_list_str: 元素列表字符串，例如 "1409to1421by4 1410to1422by4"
            
        Returns:
            元素ID列表
        """
        result = []
        
        # 处理空格或特殊格式的多个元素组
        elem_groups = re.split(r'\s+', elem_list_str)
        
        for group in elem_groups:
            group = group.strip()
            if not group:
                continue
                
            # 处理范围形式 "1409to1421by4"
            to_match = re.match(r'(\d+)to(\d+)by(\d+)', group)
            if to_match:
                start = int(to_match.group(1))
                end = int(to_match.group(2))
                step = int(to_match.group(3))
                result.extend(range(start, end + 1, step))
                continue
            
            # 处理范围形式但没有步长 "7to21"
            to_match_no_step = re.match(r'(\d+)to(\d+)', group)
            if to_match_no_step:
                start = int(to_match_no_step.group(1))
                end = int(to_match_no_step.group(2))
                result.extend(range(start, end + 1))
                continue
                
            # 处理单个数字
            if re.match(r'^\d+$', group):
                result.append(int(group))
        
        return result
    
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
        
        # 跳过命令标题和注释行
        i = 0
        while i < len(lines):
            line = lines[i].strip()
            if line and not line.startswith(';') and not line.startswith('*TS-GROUP'):
                break
            i += 1
        
        # 遍历解析每一行的变截面组定义
        while i < len(lines):
            line = lines[i].strip()
            if not line or line.startswith(';'):
                i += 1
                continue
            
            # 解析每一行TS-GROUP数据
            ts_group_data = self.parse_ts_group_line(line, line_nums[i])
            if ts_group_data:
                # 添加到模型
                group_id = len(self.parser.model.get_commands_by_type('TS-GROUP'))
                self.parser.model.add_command(f"TS-GROUP_{group_id}", ts_group_data)
            
            i += 1
    
    def parse_ts_group_line(self, line: str, line_num: int) -> Optional[TsGroup]:
        """
        解析单行TS-GROUP数据
        
        Args:
            line: 要解析的TS-GROUP命令行
            line_num: 行号
            
        Returns:
            解析后的变截面数据
        """
        try:
            # 移除可能的续行标记 '\'
            line = line.replace('\\', '').strip()
            
            # 按逗号分割
            parts = [p.strip() for p in line.split(',')]
            
            if len(parts) < 7:
                self.parser.model.warnings.append(f"忽略无效的TS-GROUP行: 格式不正确，行号 {line_num}")
                return None
                
            name = parts[0]
            elem_list_str = parts[1]
            
            # 解析变截面Z方向信息
            z_variation = {
                "type": parts[2].strip().lower(),  # LINEAR 或 QUADRATIC
                "exponent": parts[3].strip() if len(parts) > 3 and parts[3].strip() else None,
                "from_direction": parts[4].strip() if len(parts) > 4 and parts[4].strip() else None,
                "distance": parts[5].strip() if len(parts) > 5 and parts[5].strip() else None
            }
            
            # 解析变截面Y方向信息
            y_variation = {
                "type": parts[6].strip().lower(),  # LINEAR 或 QUADRATIC
                "exponent": parts[7].strip() if len(parts) > 7 and parts[7].strip() else None,
                "from_direction": parts[8].strip() if len(parts) > 8 and parts[8].strip() else None,
                "distance": parts[9].strip() if len(parts) > 9 and parts[9].strip() else None
            }
            
            # 解析截面控制方式
            section_control_method = parts[10].strip() if len(parts) > 10 and parts[10].strip() else "0"
            
            # 解析元素列表
            elements = self.parse_element_list(elem_list_str)
            
            # 创建变截面组数据模型
            ts_group_data = TsGroup(
                id=len(self.parser.model.get_commands_by_type('TS-GROUP')),
                name=name,
                elements=elements,
                z_variation=z_variation,
                y_variation=y_variation,
                section_control_method=section_control_method,
                raw_lines=[line],
                line_nums=[line_num]
            )
            
            return ts_group_data
        except Exception as e:
            self.parser.model.errors.append(f"解析TS-GROUP命令时出错: {line}，行号 {line_num}，错误: {str(e)}")
            return None
