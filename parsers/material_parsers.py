"""
材料解析器模块

处理MATERIAL、MATL-COLOR、TDM-TYPE、TDM-ELAST、TDM-LINK等命令
"""

from typing import List
import re

from ..models import (
    Material, MaterialCommand, MaterialType, MatlColor,
    TdmType, TdmElast, TdmLink, ElemDepmatl
)


class MaterialParser:
    """材料解析器类"""
    
    def __init__(self, parser):
        """
        初始化材料解析器
        
        Args:
            parser: 父解析器引用
        """
        self.parser = parser
    
    def parse_material(self, lines: List[str], line_nums: List[int]):
        """
        解析MATERIAL命令
        
        格式示例:
        *MATERIAL
        1, CONC, C40, 0.28, 1.63, ELASTO-PLASTIC, C, YES, 0.05, 1, GB, C40, JGJT, YES, 34500
        
        Args:
            lines: 命令行列表
            line_nums: 行号列表
        """
        materials = {}
        
        for i, (line, line_num) in enumerate(zip(lines, line_nums)):
            line = self.parser._preprocess_line(line)
            if not line or line.startswith(';'):
                continue
            
            parts = re.split(r'\s*,\s*', line)
            if len(parts) < 11:  # 基本参数数量
                self.parser.model.errors.append(f"无效的材料定义: {line}，行号 {line_nums[i]}")
                continue
            
            try:
                mat_id = int(parts[0])
            except ValueError as e:
                self.parser.model.errors.append(f"解析材料命令时出错: {line}，行号 {line_nums[i]}，错误: {str(e)}")
                continue
                
            mat_type = parts[1].strip()
            mat_name = parts[2].strip()
            
            # 尝试转换为枚举类型
            try:
                material_type = MaterialType(mat_type)
            except ValueError:
                # 如果无法转换，则保留字符串
                material_type = mat_type
            
            # 解析各种类型的材料属性
            properties = {}
            
            # 保存主要参数
            try:
                specific_heat = float(parts[3]) if parts[3].strip() else 0.0
            except ValueError as e:
                self.parser.model.errors.append(f"解析材料命令时出错: {line}，行号 {line_nums[i]}，错误: {str(e)}")
                continue
                
            try:
                heat_coefficient = float(parts[4]) if parts[4].strip() else 0.0
            except ValueError as e:
                self.parser.model.errors.append(f"解析材料命令时出错: {line}，行号 {line_nums[i]}，错误: {str(e)}")
                continue
                
            plastic = parts[5].strip()
            temperature_unit = parts[6].strip()
            mass_considered = parts[7].upper() == "YES"
            
            try:
                damping_ratio = float(parts[8]) if parts[8].strip() else 0.0
            except ValueError as e:
                self.parser.model.errors.append(f"解析材料命令时出错: {line}，行号 {line_nums[i]}，错误: {str(e)}")
                continue
            
            # 根据材料类型处理特定属性
            try:
                data_type = int(parts[9]) if parts[9].strip() else 0
            except ValueError as e:
                self.parser.model.errors.append(f"解析材料命令时出错: {line}，行号 {line_nums[i]}，错误: {str(e)}")
                continue
            
            properties["data_type"] = data_type
            
            if mat_type in ["STEEL", "CONC", "USER"]:
                if data_type == 1:  # 标准类型
                    properties["code"] = parts[10].strip()
                    properties["product"] = parts[11].strip() if len(parts) > 11 else ""
                    properties["db"] = parts[12].strip() if len(parts) > 12 else ""
                    properties["use_elast"] = parts[13].upper() == "YES" if len(parts) > 13 else False
                    properties["elast"] = float(parts[14]) if len(parts) > 14 and parts[14].strip() else 0.0
                elif data_type == 2:  # 自定义参数
                    properties["elast"] = float(parts[10]) if parts[10].strip() else 0.0
                    properties["poisson"] = float(parts[11]) if len(parts) > 11 and parts[11].strip() else 0.0
                    properties["thermal"] = float(parts[12]) if len(parts) > 12 and parts[12].strip() else 0.0
                    properties["density"] = float(parts[13]) if len(parts) > 13 and parts[13].strip() else 0.0
                    properties["mass"] = float(parts[14]) if len(parts) > 14 and parts[14].strip() else 0.0
                elif data_type == 3:  # 正交各向异性
                    # 添加正交各向异性特定属性...
                    pass
            elif mat_type == "SRC":
                # 处理SRC特定属性...
                pass
            
            # 创建材料对象并添加到字典
            materials[mat_id] = Material(
                id=mat_id,
                type=material_type,
                name=mat_name,
                specific_heat=specific_heat,
                heat_coefficient=heat_coefficient,
                plastic=plastic,
                temperature_unit=temperature_unit,
                mass_considered=mass_considered,
                damping_ratio=damping_ratio,
                properties=properties
            )
        
        material_command = MaterialCommand(materials=materials, raw_lines=lines, line_nums=line_nums)
        self.parser.model.add_command("MATERIAL", material_command)
    
    def parse_matl_color(self, lines: List[str], line_nums: List[int]):
        """
        解析MATL-COLOR命令
        
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
            if len(parts) < 4:  # 至少需要材料ID和RGB值
                self.parser.model.errors.append(f"无效的材料颜色定义: {line}，行号 {line_nums[i]}")
                continue
            
            try:
                material_id = int(parts[0])
                r = int(parts[1])
                g = int(parts[2])
                b = int(parts[3])
                
                colors[material_id] = [r, g, b]
            
            except ValueError as e:
                self.parser.model.errors.append(f"解析材料颜色定义时出错: {line}，行号 {line_nums[i]}，错误: {str(e)}")
        
        matl_color_data = MatlColor(colors=colors, raw_lines=lines, line_nums=line_nums)
        self.parser.model.add_command("MATL-COLOR", matl_color_data)
    
    def parse_rebar_matl_code(self, lines: List[str], line_nums: List[int]):
        """
        解析REBAR-MATL-CODE命令
        
        Args:
            lines: 命令行列表
            line_nums: 行号列表
        """
        # 这里实现REBAR-MATL-CODE命令的解析
        pass
    
    def parse_tdm_func(self, lines: List[str], line_nums: List[int]):
        """
        解析TDM-FUNC命令
        
        Args:
            lines: 命令行列表
            line_nums: 行号列表
        """
        # 这里实现TDM-FUNC命令的解析
        pass
    
    def parse_tdm_type(self, lines: List[str], line_nums: List[int]):
        """
        解析TDM-TYPE命令
        
        Args:
            lines: 命令行列表
            line_nums: 行号列表
        """
        tdm_types = []
        
        # 跳过命令行
        for i, line in enumerate(lines[1:], 1):
            line = line.strip()
            if not line:
                continue
            
            parts = re.split(r'\s*,\s*', line)
            if len(parts) < 3:  # 至少需要ID、名称和类型
                self.parser.model.errors.append(f"无效的TDM-TYPE定义: {line}，行号 {line_nums[i]}")
                continue
            
            try:
                tdm_id = int(parts[0])
                name = parts[1]
                type_str = parts[2]
                
                # 解析可选的附加参数
                options = {}
                if len(parts) > 3:
                    options_str = ' '.join(parts[3:])
                    
                    if 'PARAM=' in options_str:
                        param_match = re.search(r'PARAM=(\d+)', options_str)
                        if param_match:
                            options['param'] = int(param_match.group(1))
                
                tdm_types.append({
                    'id': tdm_id,
                    'name': name,
                    'type': type_str,
                    'options': options
                })
            
            except ValueError as e:
                self.parser.model.errors.append(f"解析TDM-TYPE定义时出错: {line}，行号 {line_nums[i]}，错误: {str(e)}")
        
        tdm_type_data = TdmType(types=tdm_types, raw_lines=lines, line_nums=line_nums)
        self.parser.model.add_command("TDM-TYPE", tdm_type_data)
    
    def parse_tdm_elast(self, lines: List[str], line_nums: List[int]):
        """
        解析TDM-ELAST命令
        
        Args:
            lines: 命令行列表
            line_nums: 行号列表
        """
        tdm_elasts = []
        
        # 跳过命令行
        for i, line in enumerate(lines[1:], 1):
            line = line.strip()
            if not line:
                continue
            
            parts = re.split(r'\s*,\s*', line)
            if len(parts) < 4:  # 至少需要ID、名称和两个参数
                self.parser.model.errors.append(f"无效的TDM-ELAST定义: {line}，行号 {line_nums[i]}")
                continue
            
            try:
                tdm_id = int(parts[0])
                material_id = int(parts[1])
                
                # 解析参数
                params = []
                for j in range(2, len(parts)):
                    try:
                        param = float(parts[j])
                        params.append(param)
                    except ValueError:
                        break  # 非数字，可能是选项
                
                tdm_elasts.append({
                    'id': tdm_id,
                    'material_id': material_id,
                    'params': params
                })
            
            except ValueError as e:
                self.parser.model.errors.append(f"解析TDM-ELAST定义时出错: {line}，行号 {line_nums[i]}，错误: {str(e)}")
        
        tdm_elast_data = TdmElast(elasts=tdm_elasts, raw_lines=lines, line_nums=line_nums)
        self.parser.model.add_command("TDM-ELAST", tdm_elast_data)
    
    def parse_tdm_link(self, lines: List[str], line_nums: List[int]):
        """
        解析TDM-LINK命令
        
        Args:
            lines: 命令行列表
            line_nums: 行号列表
        """
        tdm_links = []
        
        # 跳过命令行
        for i, line in enumerate(lines[1:], 1):
            line = line.strip()
            if not line:
                continue
            
            parts = re.split(r'\s*,\s*', line)
            if len(parts) < 3:  # 至少需要ID、类型和一个参数
                self.parser.model.errors.append(f"无效的TDM-LINK定义: {line}，行号 {line_nums[i]}")
                continue
            
            try:
                tdm_id = int(parts[0])
                link_type = parts[1]
                
                # 解析参数
                params = []
                for j in range(2, len(parts)):
                    try:
                        param = float(parts[j])
                        params.append(param)
                    except ValueError:
                        break  # 非数字，可能是选项
                
                tdm_links.append({
                    'id': tdm_id,
                    'type': link_type,
                    'params': params
                })
            
            except ValueError as e:
                self.parser.model.errors.append(f"解析TDM-LINK定义时出错: {line}，行号 {line_nums[i]}，错误: {str(e)}")
        
        tdm_link_data = TdmLink(links=tdm_links, raw_lines=lines, line_nums=line_nums)
        self.parser.model.add_command("TDM-LINK", tdm_link_data)
    
    def parse_elem_depmatl(self, lines: List[str], line_nums: List[int]):
        """
        解析ELEM-DEPMATL命令
        
        Args:
            lines: 命令行列表
            line_nums: 行号列表
        """
        elem_depmats = []
        
        # 跳过命令行
        for i, line in enumerate(lines[1:], 1):
            line = line.strip()
            if not line:
                continue
            
            parts = re.split(r'\s*,\s*', line)
            if len(parts) < 2:  # 至少需要单元索引和材料ID
                self.parser.model.errors.append(f"无效的ELEM-DEPMATL定义: {line}，行号 {line_nums[i]}")
                continue
            
            try:
                # 解析单元索引表达式
                elem_expr = parts[0]
                elem_ids = self.parser._parse_index_list(elem_expr)
                
                material_id = int(parts[1])
                
                elem_depmats.append({
                    'elem_ids': elem_ids,
                    'material_id': material_id
                })
            
            except ValueError as e:
                self.parser.model.errors.append(f"解析ELEM-DEPMATL定义时出错: {line}，行号 {line_nums[i]}，错误: {str(e)}")
        
        elem_depmatl_data = ElemDepmatl(depmats=elem_depmats, raw_lines=lines, line_nums=line_nums)
        self.parser.model.add_command("ELEM-DEPMATL", elem_depmatl_data)
