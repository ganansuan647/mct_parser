"""
施工阶段解析器模块

处理LOAD-SEQ、STAGE-CTRL等命令
"""

from typing import Dict, List, Union, Optional, Any, Set, Tuple
import re

from ..models import (
    LoadSeq, StageCtrl
)


class StageParser:
    """施工阶段解析器类"""
    
    def __init__(self, parser):
        """
        初始化施工阶段解析器
        
        Args:
            parser: 父解析器引用
        """
        self.parser = parser
    
    def parse_load_seq(self, lines: List[str], line_nums: List[int]):
        """
        解析LOAD-SEQ命令
        
        Args:
            lines: 命令行列表
            line_nums: 行号列表
        """
        sequences = []
        current_seq = None
        
        # 跳过命令行
        i = 1
        while i < len(lines):
            line = lines[i].strip()
            if not line:
                i += 1
                continue
            
            parts = line.split()
            if len(parts) < 2:  # 至少需要序列ID和名称
                self.parser.model.errors.append(f"无效的荷载序列定义: {line}，行号 {line_nums[i]}")
                i += 1
                continue
            
            try:
                # 检查是否为序列定义行
                if parts[0].isdigit():
                    # 如果有前一个序列，保存它
                    if current_seq is not None:
                        sequences.append(current_seq)
                    
                    # 创建新的序列
                    seq_id = int(parts[0])
                    seq_name = parts[1]
                    
                    current_seq = {
                        'id': seq_id,
                        'name': seq_name,
                        'stages': []
                    }
                    
                    i += 1
                    # 查找序列中的阶段
                    while i < len(lines) and not lines[i].strip().startswith("*") and lines[i].strip():
                        stage_line = lines[i].strip()
                        stage_parts = stage_line.split()
                        
                        if len(stage_parts) < 3 or not stage_parts[0].isdigit():
                            break
                        
                        stage_id = int(stage_parts[0])
                        stage_type = stage_parts[1]
                        stage_name = stage_parts[2]
                        
                        # 解析可选参数
                        stage_options = {}
                        if len(stage_parts) > 3:
                            options_str = ' '.join(stage_parts[3:])
                            
                            for pattern in ['GTYPE=(\w+)', 'ACTIVE=(\w+)']:
                                match = re.search(pattern, options_str)
                                if match:
                                    key = pattern.split('=')[0].lower()
                                    stage_options[key] = match.group(1)
                        
                        current_seq['stages'].append({
                            'id': stage_id,
                            'type': stage_type,
                            'name': stage_name,
                            'options': stage_options
                        })
                        
                        i += 1
                else:
                    i += 1
            
            except ValueError as e:
                self.parser.model.errors.append(f"解析荷载序列定义时出错: {line}，行号 {line_nums[i]}，错误: {str(e)}")
                i += 1
        
        # 保存最后一个序列
        if current_seq is not None:
            sequences.append(current_seq)
        
        load_seq_data = LoadSeq(sequences=sequences, raw_lines=lines, line_nums=line_nums)
        self.parser.model.add_command("LOAD-SEQ", load_seq_data)
    
    def parse_stage_ctrl(self, lines: List[str], line_nums: List[int]):
        """
        解析STAGE-CTRL命令
        
        Args:
            lines: 命令行列表
            line_nums: 行号列表
        """
        if len(lines) < 2:
            self.parser.model.errors.append(f"无效的STAGE-CTRL命令: 缺少控制参数")
            return
        
        # 解析第一行的控制参数
        parts = lines[1].strip().split()
        
        # 至少需要4个参数：工况ID、施工阶段ID、时间和计算类型
        if len(parts) < 4:
            self.parser.model.errors.append(f"无效的STAGE-CTRL命令: 参数不足")
            return
        
        try:
            case_id = int(parts[0])
            stage_id = int(parts[1])
            time = float(parts[2])
            calc_type = parts[3]
            
            # 解析可选参数
            options = {}
            if len(parts) > 4:
                for i in range(4, len(parts)):
                    if "=" in parts[i]:
                        key, value = parts[i].split("=", 1)
                        options[key.lower()] = value
                    else:
                        options[f"option{i-3}"] = parts[i]
            
            stage_ctrl_data = StageCtrl(
                case_id=case_id,
                stage_id=stage_id,
                time=time,
                calc_type=calc_type,
                options=options,
                raw_lines=lines,
                line_nums=line_nums
            )
            
            self.parser.model.add_command("STAGE-CTRL", stage_ctrl_data)
        
        except ValueError as e:
            self.parser.model.errors.append(f"解析STAGE-CTRL命令时出错: {str(e)}")
