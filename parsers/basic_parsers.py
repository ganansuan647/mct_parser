"""
基本命令解析器模块

处理VERSION、UNIT、PROJINFO等基本命令
"""

from typing import Dict, List, Union, Optional, Any, Set, Tuple
import re
from enum import Enum

from ..models import (
    Version, Unit, ProjInfo, StructType, CutLine, MCTCommand
)


class BasicCommandParser:
    """基本命令解析器类"""
    
    def __init__(self, parser):
        """
        初始化基本命令解析器
        
        Args:
            parser: 父解析器引用
        """
        self.parser = parser
    
    def parse_version(self, lines: List[str], line_nums: List[int]):
        """
        解析VERSION命令
        
        Args:
            lines: 命令行列表
            line_nums: 行号列表
        """
        if len(lines) < 2:
            self.parser.model.errors.append(f"无效的VERSION命令: 缺少版本信息")
            return
        
        version = lines[1].strip()
        version_data = Version(version=version, raw_lines=lines, line_nums=line_nums)
        self.parser.model.add_command(MCTCommand.VERSION.value, version_data)
    
    def parse_unit(self, lines: List[str], line_nums: List[int]):
        """
        解析UNIT命令
        
        Args:
            lines: 命令行列表
            line_nums: 行号列表
        """
        if len(lines) < 2:
            self.parser.model.errors.append(f"无效的UNIT命令: 缺少单位信息")
            return
        
        unit_line = lines[1].strip()
        parts = re.split(r'\s*,\s*', unit_line)
        
        unit_data = Unit(
            force=parts[0] if len(parts) > 0 else "tonf",
            length=parts[1] if len(parts) > 1 else "m",
            heat=parts[2] if len(parts) > 2 else "",
            temperature=parts[3] if len(parts) > 3 else "",
            raw_lines=lines,
            line_nums=line_nums
        )
        
        self.parser.model.add_command(MCTCommand.UNIT.value, unit_data)
    
    def parse_projinfo(self, lines: List[str], line_nums: List[int]):
        """
        解析PROJINFO命令
        
        Args:
            lines: 命令行列表
            line_nums: 行号列表
        """
        info = {}
        
        # 跳过命令行
        for line in lines[1:]:
            line = line.strip()
            if '=' in line:
                key, value = line.split('=', 1)
                info[key.strip()] = value.strip()
        
        projinfo_data = ProjInfo(info=info, raw_lines=lines, line_nums=line_nums)
        self.parser.model.add_command("PROJINFO", projinfo_data)
    
    def parse_structype(self, lines: List[str], line_nums: List[int]):
        """
        解析STRUCTYPE命令
        
        Args:
            lines: 命令行列表
            line_nums: 行号列表
        """
        struct_re = re.compile(r'\s*,\s*')
        
        for i, line in enumerate(lines):
            line = self.parser._preprocess_line(line)
            if not line or line.startswith(';') or line.startswith('*'):
                continue
            
            parts = re.split(r'\s*,\s*', line)
            
            # 解析各参数，处理可能的缺失情况
            try:
                istruct_type = int(parts[0]) if len(parts) > 0 and parts[0].strip().isdigit() else 0
            except ValueError as e:
                self.parser.model.errors.append(f"解析structype命令时出错: {line}，行号 {line_nums[i]}，错误: {str(e)}")
                continue
                
            try:
                imass = int(parts[1]) if len(parts) > 1 and parts[1].strip().isdigit() else 0
            except ValueError as e:
                self.parser.model.errors.append(f"解析structype命令时出错: {line}，行号 {line_nums[i]}，错误: {str(e)}")
                continue
                
            try:
                igeomnl = int(parts[2]) if len(parts) > 2 and parts[2].strip().isdigit() else 0
            except ValueError as e:
                self.parser.model.errors.append(f"解析structype命令时出错: {line}，行号 {line_nums[i]}，错误: {str(e)}")
                continue
                
            try:
                igeom = int(parts[3]) if len(parts) > 3 and parts[3].strip().isdigit() else 0
            except ValueError as e:
                self.parser.model.errors.append(f"解析structype命令时出错: {line}，行号 {line_nums[i]}，错误: {str(e)}")
                continue
                
            try:
                ianaly = int(parts[4]) if len(parts) > 4 and parts[4].strip().isdigit() else 0
            except ValueError as e:
                self.parser.model.errors.append(f"解析structype命令时出错: {line}，行号 {line_nums[i]}，错误: {str(e)}")
                continue
                
            try:
                imatrl = int(parts[5]) if len(parts) > 5 and parts[5].strip().isdigit() else 0
            except ValueError as e:
                self.parser.model.errors.append(f"解析structype命令时出错: {line}，行号 {line_nums[i]}，错误: {str(e)}")
                continue
                
            try:
                isoil = int(parts[6]) if len(parts) > 6 and parts[6].strip().isdigit() else 0
            except ValueError as e:
                self.parser.model.errors.append(f"解析structype命令时出错: {line}，行号 {line_nums[i]}，错误: {str(e)}")
                continue
                
            try:
                idimen = int(parts[7]) if len(parts) > 7 and parts[7].strip().isdigit() else 0
            except ValueError as e:
                self.parser.model.errors.append(f"解析structype命令时出错: {line}，行号 {line_nums[i]}，错误: {str(e)}")
                continue
            
            struct_data = StructType(
                istruct_type=istruct_type,
                imass=imass,
                igeomnl=igeomnl,
                igeom=igeom,
                ianaly=ianaly,
                imatrl=imatrl,
                isoil=isoil,
                idimen=idimen,
                raw_lines=lines,
                line_nums=line_nums
            )
            
            self.parser.model.add_command("STRUCTYPE", struct_data)
    
    def parse_cutline(self, lines: List[str], line_nums: List[int]):
        """
        解析CUTLINE命令
        
        Args:
            lines: 命令行列表
            line_nums: 行号列表
        """
        if len(lines) < 2:
            self.parser.model.errors.append(f"无效的CUTLINE命令: 缺少切线信息")
            return
        
        cutline_line = lines[1].strip()
        parts = re.split(r'\s*,\s*', cutline_line)
        
        if len(parts) < 9:
            self.parser.model.errors.append(f"无效的CUTLINE命令: 参数不足")
            return
        
        name = parts[0]
        direction = parts[1]
        try:
            pt1x = float(parts[2])
        except ValueError as e:
            self.parser.model.errors.append(f"解析cutline命令时出错: {cutline_line}，行号 {line_nums[1]}，错误: {str(e)}")
            return
        
        try:
            pt1y = float(parts[3])
        except ValueError as e:
            self.parser.model.errors.append(f"解析cutline命令时出错: {cutline_line}，行号 {line_nums[1]}，错误: {str(e)}")
            return
        
        try:
            pt1z = float(parts[4])
        except ValueError as e:
            self.parser.model.errors.append(f"解析cutline命令时出错: {cutline_line}，行号 {line_nums[1]}，错误: {str(e)}")
            return
        
        try:
            pt2x = float(parts[5])
        except ValueError as e:
            self.parser.model.errors.append(f"解析cutline命令时出错: {cutline_line}，行号 {line_nums[1]}，错误: {str(e)}")
            return
        
        try:
            pt2y = float(parts[6])
        except ValueError as e:
            self.parser.model.errors.append(f"解析cutline命令时出错: {cutline_line}，行号 {line_nums[1]}，错误: {str(e)}")
            return
        
        try:
            pt2z = float(parts[7])
        except ValueError as e:
            self.parser.model.errors.append(f"解析cutline命令时出错: {cutline_line}，行号 {line_nums[1]}，错误: {str(e)}")
            return
        
        # 解析颜色值
        try:
            r = int(parts[8])
        except ValueError as e:
            self.parser.model.errors.append(f"解析cutline命令时出错: {cutline_line}，行号 {line_nums[1]}，错误: {str(e)}")
            return
        
        try:
            g = int(parts[9]) if len(parts) > 9 else 0
        except ValueError as e:
            self.parser.model.errors.append(f"解析cutline命令时出错: {cutline_line}，行号 {line_nums[1]}，错误: {str(e)}")
            return
        
        try:
            b = int(parts[10]) if len(parts) > 10 else 0
        except ValueError as e:
            self.parser.model.errors.append(f"解析cutline命令时出错: {cutline_line}，行号 {line_nums[1]}，错误: {str(e)}")
            return
        
        cutline_data = CutLine(
            name=name,
            direction=direction,
            point1=[pt1x, pt1y, pt1z],
            point2=[pt2x, pt2y, pt2z],
            color=[r, g, b],
            raw_lines=lines,
            line_nums=line_nums
        )
        
        self.parser.model.add_command("CUTLINE", cutline_data)
        
    def parse_enddata(self, lines: List[str], line_nums: List[int]):
        """
        解析ENDDATA命令
        
        Args:
            lines: 命令行列表
            line_nums: 行号列表
        """
        # ENDDATA命令通常不需要特殊处理，只需记录它的存在
        # 创建一个简单的CommandData对象
        from mct_parser.models.base import CommandData
        
        enddata = CommandData(raw_lines=lines, line_nums=line_nums)
        self.parser.model.add_command("ENDDATA", enddata)
