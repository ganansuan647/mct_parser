"""
截面解析器模块

处理SECTION、SECT-COLOR、SECT-PSCVALUE等命令
"""

from typing import Dict, List, Union, Optional, Any, Set, Tuple
import re

from ..models import (
    Section, SectColor, SectPscvalue, DgnSect, DgnSectPscvalue, CompGenSectPscDesign
)


class SectionParser:
    """截面解析器类"""
    
    def __init__(self, parser):
        """
        初始化截面解析器
        
        Args:
            parser: 父解析器引用
        """
        self.parser = parser
    
    def parse_section(self, lines: List[str], line_nums: List[int]):
        """
        解析SECTION命令
        
        格式示例:
        *SECTION
        1, RECT, 400, 800  ; ID, 类型, 参数1, 参数2, ...
        2, CIRCLE, 600     ; ID, 类型, 直径
        
        Args:
            lines: 命令行列表
            line_nums: 行号列表
        """
        sections = {}
        
        for line, line_num in zip(lines, line_nums):
            line = self.parser._preprocess_line(line)
            if not line or line.startswith(';'):
                continue
            
            parts = re.split(r'\s*,\s*', line)
            if len(parts) < 3:  # 至少需要截面ID、类型和至少一个参数
                self.parser.model.errors.append(f"无效的截面定义: {line}，行号 {line_num}")
                continue
            
            try:
                section_id = int(parts[0])
            except ValueError as e:
                self.parser.model.errors.append(f"解析截面命令时出错: {line}，行号 {line_num}，错误: {str(e)}")
                continue
                
            section_type = parts[1].strip()
            
            # 根据不同截面类型解析参数
            params = {}
            
            if section_type in ["DBSECC", "DBSECT"]:  # 数据库截面
                params["db_type"] = parts[2].strip()
                
                # 后续参数
                for j in range(3, len(parts)):
                    param = parts[j].strip()
                    if not param:
                        continue
                        
                    if "=" in param:
                        key, value = param.split("=", 1)
                        params[key.lower().strip()] = value.strip()
                    else:
                        params[f"param{j-2}"] = param
            
            elif section_type in ["TAPERED", "VARIABLE"]:  # 变截面
                try:
                    params["start_section"] = int(parts[2])
                except ValueError as e:
                    self.parser.model.errors.append(f"解析截面命令时出错: {line}，行号 {line_num}，错误: {str(e)}")
                    continue
                    
                if len(parts) > 3:
                    try:
                        params["end_section"] = int(parts[3])
                    except ValueError as e:
                        self.parser.model.errors.append(f"解析截面命令时出错: {line}，行号 {line_num}，错误: {str(e)}")
                        continue
                        
                if len(parts) > 4:
                    params["interpolation"] = parts[4].strip()
            
            elif section_type in ["COMPOSITE", "COMP"]:  # 组合截面
                params["sections"] = []
                for j in range(2, len(parts)):
                    part = parts[j].strip()
                    if not part:
                        continue
                        
                    try:
                        if part.isdigit():
                            params["sections"].append(int(part))
                    except ValueError:
                        break  # 非数字，可能是其他参数
            
            else:  # 其他直接定义的截面类型
                # 解析参数数组
                param_list = []
                for j in range(2, len(parts)):
                    part = parts[j].strip()
                    if not part:
                        continue
                        
                    try:
                        param_list.append(float(part))
                    except ValueError:
                        param_list.append(part)  # 非数字参数
                
                params["params"] = param_list
            
            sections[section_id] = {
                "id": section_id,
                "type": section_type,
                "params": params
            }
        
        section_data = Section(sections=sections, raw_lines=lines, line_nums=line_nums)
        self.parser.model.add_command("SECTION", section_data)
    
    def parse_sect_color(self, lines: List[str], line_nums: List[int]):
        """
        解析SECT-COLOR命令
        
        Args:
            lines: 命令行列表
            line_nums: 行号列表
        """
        colors = {}
        
        # 跳过命令行
        for i, line in enumerate(lines[1:], 1):
            line = line.strip()
            if not line:
                continue
            
            parts = re.split(r'\s*,\s*', line)
            if len(parts) < 4:  # 至少需要截面ID和RGB值
                self.parser.model.errors.append(f"无效的截面颜色定义: {line}，行号 {line_nums[i]}")
                continue
            
            try:
                section_id = int(parts[0])
                r = int(parts[1])
                g = int(parts[2])
                b = int(parts[3])
                
                colors[section_id] = [r, g, b]
            
            except ValueError as e:
                self.parser.model.errors.append(f"解析截面颜色定义时出错: {line}，行号 {line_nums[i]}，错误: {str(e)}")
        
        sect_color_data = SectColor(colors=colors, raw_lines=lines, line_nums=line_nums)
        self.parser.model.add_command("SECT-COLOR", sect_color_data)
    
    def parse_sect_pscvalue(self, lines: List[str], line_nums: List[int]):
        """
        解析SECT-PSCVALUE命令
        
        格式示例:
        *SECT-PSCVALUE
        SECT=1, BPAR=500, HPAR=1000
        OPOLY=0,0, 500,0, 500,1000, 0,1000
        
        Args:
            lines: 命令行列表
            line_nums: 行号列表
        """
        sections = {}
        current_section = None
        collecting_polygon = False
        polygon_data = []
        
        for line, line_num in zip(lines, line_nums):
            line = self.parser._preprocess_line(line)
            if not line or line.startswith(';'):
                continue
            
            if line.startswith("SECT="):
                # 开始新截面定义
                if collecting_polygon and current_section:
                    # 保存之前的多边形数据
                    if "polygons" not in sections[current_section]:
                        sections[current_section]["polygons"] = []
                    sections[current_section]["polygons"].append(polygon_data)
                    collecting_polygon = False
                    polygon_data = []
                
                # 解析SECT行
                parts = line.split(',')
                sect_part = parts[0].split('=', 1)
                if len(sect_part) != 2:
                    continue
                
                try:
                    sect_id = int(sect_part[1].strip())
                    current_section = sect_id
                    sections[sect_id] = {"params": {}}
                    
                    # 添加其他参数
                    for i, param in enumerate(parts[1:], 1):
                        param = param.strip()
                        if not param:
                            continue
                        
                        if '=' in param:
                            k, v = param.split('=', 1)
                            sections[sect_id]["params"][k.strip()] = v.strip()
                        else:
                            sections[sect_id]["params"][f"param{i}"] = param
                except ValueError:
                    self.parser.model.errors.append(f"解析SECT-PSCVALUE截面ID出错: {line}，行号 {line_num}")
                    continue
            
            elif line.startswith("OPOLY=") or line.startswith("IPOLY=") or line.startswith("VERTEX="):
                # 开始多边形定义
                collecting_polygon = True
                polygon_type = line.split('=', 1)[0].strip()
                polygon_data = {"type": polygon_type, "points": []}
                
                # 解析坐标点
                data_part = line.split('=', 1)[1].strip()
                coords = re.split(r'\s*,\s*', data_part)
                
                # 检查是否有标志位(适用于TAPERED)
                if coords and coords[0].upper() in ["YES", "NO", "TRUE", "FALSE"]:
                    polygon_data["flag"] = coords[0].upper() in ["YES", "TRUE"]
                    coords = coords[1:]
                
                # 处理坐标点
                for i in range(0, len(coords), 2):
                    if i+1 < len(coords):
                        try:
                            x = float(coords[i])
                            y = float(coords[i+1])
                            polygon_data["points"].append((x, y))
                        except ValueError:
                            continue
            
            elif collecting_polygon and line.startswith("LINE="):
                # 处理线段定义
                data_part = line.split('=', 1)[1].strip()
                line_data = re.split(r'\s*,\s*', data_part)
                
                if len(line_data) >= 4:
                    polygon_data["lines"] = line_data
            
            elif current_section and not collecting_polygon:
                # 处理其他数据行(如刚度、截面参数等)
                if "data_lines" not in sections[current_section]:
                    sections[current_section]["data_lines"] = []
                sections[current_section]["data_lines"].append(line)
        
        # 处理最后一个多边形
        if collecting_polygon and current_section:
            if "polygons" not in sections[current_section]:
                sections[current_section]["polygons"] = []
            sections[current_section]["polygons"].append(polygon_data)
        
        sect_pscvalue_data = SectPscvalue(sections=sections, raw_lines=lines, line_nums=line_nums)
        self.parser.model.add_command("SECT-PSCVALUE", sect_pscvalue_data)
    
    def parse_dgn_sect(self, lines: List[str], line_nums: List[int]):
        """
        解析DGN-SECT命令
        
        Args:
            lines: 命令行列表
            line_nums: 行号列表
        """
        dgn_sects = {}
        
        # 跳过命令行
        i = 1
        while i < len(lines):
            line = lines[i].strip()
            if not line:
                i += 1
                continue
            
            parts = re.split(r'\s*,\s*', line)
            if len(parts) < 3:  # 至少需要截面ID、设计类型和材料ID
                self.parser.model.errors.append(f"无效的DGN-SECT定义: {line}，行号 {line_nums[i]}")
                i += 1
                continue
            
            try:
                section_id = int(parts[0])
                design_type = parts[1]
                material_id = int(parts[2])
                
                # 解析设计参数
                params = {}
                if len(parts) > 3:
                    for j in range(3, len(parts)):
                        if "=" in parts[j]:
                            key, value = parts[j].split("=", 1)
                            params[key.lower()] = value
                        else:
                            params[f"param{j-2}"] = parts[j]
                
                dgn_sects[section_id] = {
                    "id": section_id,
                    "design_type": design_type,
                    "material_id": material_id,
                    "params": params
                }
            
            except ValueError as e:
                self.parser.model.errors.append(f"解析DGN-SECT定义时出错: {line}，行号 {line_nums[i]}，错误: {str(e)}")
            
            i += 1
        
        dgn_sect_data = DgnSect(dgn_sects=dgn_sects, raw_lines=lines, line_nums=line_nums)
        self.parser.model.add_command("DGN-SECT", dgn_sect_data)
    
    def parse_dgn_sect_pscvalue(self, lines: List[str], line_nums: List[int]):
        """
        解析DGN-SECT-PSCVALUE命令
        
        Args:
            lines: 命令行列表
            line_nums: 行号列表
        """
        pscvalues = {}
        
        # 跳过命令行
        for i, line in enumerate(lines[1:], 1):
            line = line.strip()
            if not line:
                continue
            
            parts = re.split(r'\s*,\s*', line)
            if len(parts) < 2:  # 至少需要截面ID和至少一个参数
                self.parser.model.errors.append(f"无效的DGN-SECT-PSCVALUE定义: {line}，行号 {line_nums[i]}")
                continue
            
            try:
                section_id = int(parts[0])
                
                # 解析后续参数
                params = []
                for j in range(1, len(parts)):
                    try:
                        param = float(parts[j])
                    except ValueError:
                        param = parts[j]  # 非数字参数
                    params.append(param)
                
                pscvalues[section_id] = params
            
            except ValueError as e:
                self.parser.model.errors.append(f"解析DGN-SECT-PSCVALUE定义时出错: {line}，行号 {line_nums[i]}，错误: {str(e)}")
        
        dgn_sect_pscvalue_data = DgnSectPscvalue(pscvalues=pscvalues, raw_lines=lines, line_nums=line_nums)
        self.parser.model.add_command("DGN-SECT-PSCVALUE", dgn_sect_pscvalue_data)
    
    def parse_comp_gen_sect_psc_design(self, lines: List[str], line_nums: List[int]):
        """
        解析COMP-GEN-SECT-PSC-DESIGN命令
        
        Args:
            lines: 命令行列表
            line_nums: 行号列表
        """
        designs = {}
        
        # 跳过命令行
        i = 1
        while i < len(lines):
            line = lines[i].strip()
            if not line:
                i += 1
                continue
            
            parts = re.split(r'\s*,\s*', line)
            if len(parts) < 2:  # 至少需要截面ID和设计类型
                self.parser.model.errors.append(f"无效的COMP-GEN-SECT-PSC-DESIGN定义: {line}，行号 {line_nums[i]}")
                i += 1
                continue
            
            try:
                section_id = int(parts[0])
                design_type = parts[1]
                
                # 解析设计参数
                params = {}
                if len(parts) > 2:
                    for j in range(2, len(parts)):
                        if "=" in parts[j]:
                            key, value = parts[j].split("=", 1)
                            params[key.lower()] = value
                        else:
                            params[f"param{j-1}"] = parts[j]
                
                # 检查是否有后续参数行
                additional_params = []
                while i + 1 < len(lines) and not lines[i + 1].strip().startswith("*"):
                    i += 1
                    param_line = lines[i].strip()
                    param_parts = param_line.split()
                    for part in param_parts:
                        try:
                            additional_params.append(float(part))
                        except ValueError:
                            additional_params.append(part)
                
                if additional_params:
                    params["additional_params"] = additional_params
                
                designs[section_id] = {
                    "id": section_id,
                    "design_type": design_type,
                    "params": params
                }
            
            except ValueError as e:
                self.parser.model.errors.append(f"解析COMP-GEN-SECT-PSC-DESIGN定义时出错: {line}，行号 {line_nums[i]}，错误: {str(e)}")
            
            i += 1
        
        comp_gen_sect_psc_design_data = CompGenSectPscDesign(designs=designs, raw_lines=lines, line_nums=line_nums)
        self.parser.model.add_command("COMP-GEN-SECT-PSC-DESIGN", comp_gen_sect_psc_design_data)
