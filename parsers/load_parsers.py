"""
荷载解析器模块

处理STLDCASE、USE-STLD、SELFWEIGHT、BEAMLOAD、CONLOAD等荷载命令
"""

from typing import Dict, List, Union, Optional, Any, Set, Tuple
import re

from ..models import (
    StldCase, UseStld, SelfWeight, BeamLoad, ConLoad, 
    SystemPer, BsTemper, EffWidth, LoadToMass, LoadComb
)


class LoadParser:
    """荷载解析器类"""
    
    def __init__(self, parser):
        """
        初始化荷载解析器
        
        Args:
            parser: 父解析器引用
        """
        self.parser = parser
    
    def parse_stldcase(self, lines: List[str], line_nums: List[int]):
        """
        解析STLDCASE命令
        
        Args:
            lines: 命令行列表
            line_nums: 行号列表
        """
        # 处理荷载工况定义
        if len(lines) < 2:
            self.parser.model.errors.append("无效的STLDCASE命令: 缺少荷载工况定义")
            return
        
        # 解析第一行的工况ID和名称
        parts = lines[1].strip().split()
        if len(parts) < 2:
            self.parser.model.errors.append("无效的STLDCASE命令: 缺少工况ID或名称")
            return
        
        try:
            case_id = int(parts[0])
            case_name = ' '.join(parts[1:])
            
            # 创建荷载工况数据
            case_data = StldCase(
                case_id=case_id,
                case_name=case_name,
                raw_lines=lines,
                line_nums=line_nums
            )
            
            self.parser.model.add_command("STLDCASE", case_data)
        
        except ValueError:
            self.parser.model.errors.append(f"无效的STLDCASE命令: 工况ID必须是整数")
    
    def parse_use_stld(self, lines: List[str], line_nums: List[int]):
        """
        解析USE-STLD命令
        
        Args:
            lines: 命令行列表
            line_nums: 行号列表
        """
        # 处理使用荷载工况命令
        if len(lines) < 2:
            self.parser.model.errors.append("无效的USE-STLD命令: 缺少荷载工况ID")
            return
        
        try:
            case_id = int(lines[1].strip())
            
            use_stld_data = UseStld(case_id=case_id, raw_lines=lines, line_nums=line_nums)
            self.parser.model.add_command("USE-STLD", use_stld_data)
        
        except ValueError:
            self.parser.model.errors.append(f"无效的USE-STLD命令: 荷载工况ID必须是整数")
    
    def parse_selfweight(self, lines: List[str], line_nums: List[int]):
        """
        解析SELFWEIGHT命令
        
        Args:
            lines: 命令行列表
            line_nums: 行号列表
        """
        if len(lines) < 2:
            self.parser.model.errors.append(f"无效的SELFWEIGHT命令: 缺少自重定义")
            return
        
        # 解析第一行的自重定义
        parts = lines[1].strip().split()
        if len(parts) < 1:
            self.parser.model.errors.append(f"无效的SELFWEIGHT命令: 缺少自重定义")
            return
        
        try:
            # 解析自重系数向量
            factors = []
            for i in range(min(3, len(parts))):
                try:
                    factors.append(float(parts[i]))
                except ValueError:
                    factors.append(0.0)  # 默认为0
            
            # 确保有3个分量
            while len(factors) < 3:
                factors.append(0.0)
            
            # 解析可选参数
            options = {}
            if len(parts) > 3:
                options_str = ' '.join(parts[3:])
                
                for pattern in [r'GROUP=(\w+)', r'ACTIVE=(\w+)']:
                    match = re.search(pattern, options_str)
                    if match:
                        key = pattern.split('=')[0].lower()
                        options[key] = match.group(1)
            
            selfweight_data = SelfWeight(factors=factors, options=options, raw_lines=lines, line_nums=line_nums)
            self.parser.model.add_command("SELFWEIGHT", selfweight_data)
        
        except Exception as e:
            self.parser.model.errors.append(f"解析SELFWEIGHT命令时出错: {str(e)}")
    
    def parse_systemper(self, lines: List[str], line_nums: List[int]):
        """
        解析SYSTEMPER命令
        
        Args:
            lines: 命令行列表
            line_nums: 行号列表
        """
        periods = []
        
        # 跳过命令行
        for i, line in enumerate(lines[1:], 1):
            line = line.strip()
            if not line:
                continue
            
            parts = re.split(r'\s*,\s*', line)
            if len(parts) < 1:  # 至少需要一个周期值
                self.parser.model.errors.append(f"无效的系统周期定义: {line}，行号 {line_nums[i]}")
                continue
            
            try:
                period = float(parts[0])
                periods.append(period)
            
            except ValueError as e:
                self.parser.model.errors.append(f"解析系统周期定义时出错: {line}，行号 {line_nums[i]}，错误: {str(e)}")
        
        systemper_data = SystemPer(periods=periods, raw_lines=lines, line_nums=line_nums)
        self.parser.model.add_command("SYSTEMPER", systemper_data)
    
    def parse_bstemper(self, lines: List[str], line_nums: List[int]):
        """
        解析BSTEMPER命令
        
        格式:
        *BSTEMPER    ; Beam Section Temperature
        ; ELEM_LIST, DIR, REF, NUM, GROUP, bPSC              ; line 1
        ;   TYPE1, ELAST1, THERMAL1, B1, H11, T11, H21, T21  ; line 2
        ;   ...
        ;   TYPEn, ELASTn, THERMALn, Bn, H1n, T1n, H2n, T2n  ; line n+1
        ;   TYPE, ELAST, THERMAL, REF, BOPT, B, H1OPT, H1, H2OPT, H2, T1, T2 ; line 2(PSC)
        
        Args:
            lines: 命令行列表
            line_nums: 行号列表
        """
        temperatures = []
        current_element_data = None
        i = 1  # 跳过命令行
        
        while i < len(lines):
            line = lines[i].strip()
            if not line:
                i += 1
                continue
            
            # 检查是否是元素定义行
            if not line.strip().startswith('INPUT'):  # 元素定义行
                # 使用逗号分隔字段，由于字段间可能有空格
                parts = [part.strip() for part in line.split(',')]
                
                if len(parts) < 5:
                    self.parser.model.errors.append(f"无效的梁温度荷载定义: {line}，行号 {line_nums[i]}，至少需要5个参数")
                    i += 1
                    continue
                
                try:
                    # 解析元素编号
                    elem_id = int(parts[0])
                    
                    # 解析方向和参考点
                    direction = parts[1]
                    ref_point = parts[2]
                    
                    # 解析分段数量
                    num_sections = int(parts[3])
                    
                    # 解析组名
                    group = parts[4] if len(parts) > 4 and parts[4].strip() else ""
                    
                    # 解析是否使用PSC
                    is_psc = parts[5].strip().upper() == "YES" if len(parts) > 5 and parts[5].strip() else False
                    
                    # 创建元素温度数据
                    current_element_data = {
                        'elem_id': elem_id,
                        'direction': direction, 
                        'ref_point': ref_point,
                        'num_sections': num_sections,
                        'group': group,
                        'is_psc': is_psc,
                        'sections': []
                    }
                    
                except ValueError as e:
                    self.parser.model.errors.append(f"解析温度荷载定义时出错: {line}，行号 {line_nums[i]}，错误: {str(e)}")
                    i += 1
                    continue
            else:  # INPUT行，包含截面数据
                if not current_element_data:
                    self.parser.model.errors.append(f"遇到INPUT行但没有先定义元素数据: {line}，行号 {line_nums[i]}")
                    i += 1
                    continue
                
                parts = line.strip().split()
                if len(parts) < 8:  # INPUT后至少需要7个参数
                    self.parser.model.errors.append(f"无效的温度截面定义: {line}，行号 {line_nums[i]}，至少需要7个参数")
                    i += 1
                    continue
                
                try:
                    # 跳过INPUT关键字
                    data_parts = parts[1:]
                    
                    # 解析截面类型和材料特性
                    section_type = data_parts[0]
                    elasticity = float(data_parts[1])
                    thermal = float(data_parts[2])
                    
                    # 解析几何参数
                    width = float(data_parts[3])
                    height1 = float(data_parts[4])
                    temp1 = float(data_parts[5])
                    height2 = float(data_parts[6])
                    temp2 = float(data_parts[7]) if len(data_parts) > 7 else 0.0
                    
                    # 创建截面数据
                    section_data = {
                        'type': section_type,
                        'elasticity': elasticity,
                        'thermal': thermal,
                        'width': width,
                        'height1': height1,
                        'temp1': temp1,
                        'height2': height2,
                        'temp2': temp2
                    }
                    
                    # 添加到当前元素的截面列表
                    current_element_data['sections'].append(section_data)
                    
                    # 如果已收集够足够的截面数据，添加完整元素数据
                    if len(current_element_data['sections']) == current_element_data['num_sections']:
                        temperatures.append(current_element_data)
                        current_element_data = None
                        
                except ValueError as e:
                    self.parser.model.errors.append(f"解析温度荷载定义时出错: {line}，行号 {line_nums[i]}，错误: {str(e)}")
            
            i += 1
        
        # 检查是否有未完成的元素数据
        if current_element_data and current_element_data['sections']:
            if len(current_element_data['sections']) < current_element_data['num_sections']:
                self.parser.model.errors.append(f"元素 {current_element_data['elem_id']} 的温度截面数据不足，期望 {current_element_data['num_sections']} 个，实际只有 {len(current_element_data['sections'])} 个")
            temperatures.append(current_element_data)
            
        # 创建并添加命令数据
        bstemper_data = BsTemper(temperatures=temperatures, raw_lines=lines, line_nums=line_nums)
        self.parser.model.add_command("BSTEMPER", bstemper_data)
    
    def parse_beamload(self, lines: List[str], line_nums: List[int]):
        """
        解析BEAMLOAD命令
        
        Args:
            lines: 命令行列表
            line_nums: 行号列表
        """
        beamloads = []
        
        # 跳过命令行
        for i, line in enumerate(lines[1:], 1):
            line = line.strip()
            if not line:
                continue
            
            parts = re.split(r'\s*,\s*', line)
            if len(parts) < 4:  # 至少需要单元索引、荷载类型、方向和荷载值
                self.parser.model.errors.append(f"无效的梁荷载定义: {line}，行号 {line_nums[i]}")
                continue
            
            try:
                # 解析单元索引表达式
                index_expr = parts[0]
                elem_ids = self.parser._parse_index_list(index_expr)
                
                # 解析荷载类型
                load_type = parts[1]
                
                # 解析荷载方向
                direction = parts[2]
                
                # 解析荷载值
                load_values = []
                for j in range(3, min(len(parts), 5)):
                    try:
                        load_values.append(float(parts[j]))
                    except ValueError:
                        load_values.append(0.0)  # 默认为0
                
                # 确保有足够的荷载值分量
                while len(load_values) < 2:
                    load_values.append(0.0)
                
                # 解析可选参数
                options = {}
                if len(parts) > 5:
                    options_str = ' '.join(parts[5:])
                    
                    for pattern in [r'GROUP=(\w+)', r'LOCAL=(\d+)', r'ACTIVE=(\w+)']:
                        match = re.search(pattern, options_str)
                        if match:
                            key = pattern.split('=')[0].lower()
                            options[key] = match.group(1)
                
                beamloads.append({
                    'elem_ids': elem_ids,
                    'type': load_type,
                    'direction': direction,
                    'values': load_values,
                    'options': options
                })
            
            except ValueError as e:
                self.parser.model.errors.append(f"解析梁荷载定义时出错: {line}，行号 {line_nums[i]}，错误: {str(e)}")
        
        beamload_data = BeamLoad(beamloads=beamloads, raw_lines=lines, line_nums=line_nums)
        self.parser.model.add_command("BEAMLOAD", beamload_data)
    
    def parse_prestress(self, lines: List[str], line_nums: List[int]):
        """
        解析PRESTRESS命令
        
        根据MCT文档，PRESTRESS命令格式为：
        ELEM_LIST, LTYPE, TENS, DI, DM, DJ, GROUP
        
        参数说明：
        - ELEM_LIST: 单元编号
        - LTYPE: 梁单元预应力荷载的形式 {1}
          (不适用于桁架单元/只受拉单元/只受压单元)
          = PRE: 考虑施加Prestress过程中的状态时(Prestress条件)
          = POST: 考虑施加Prestress后的条件时(Post-stress条件)
        - TENS: Prestress Tension Force
        - DI: 梁单元i端的单元坐标系z方向Cable Drape
        - DM: 梁单元中点的单元坐标系z方向Cable Drape
        - DJ: 梁单元j端的单元坐标系z方向Cable Drape
        - GROUP: Load Group Name
        
        Args:
            lines: 命令行列表
            line_nums: 行号列表
        """
        prestresses = []
        
        # 跳过命令行
        for i, line in enumerate(lines[1:], 1):
            line = line.strip()
            if not line:
                continue
            
            parts = re.split(r'\s*,\s*', line)
            if len(parts) < 6:  # 至少需要单元索引、荷载类型、拉力和三个drape值
                self.parser.model.errors.append(f"无效的预应力定义: {line}，行号 {line_nums[i]}")
                continue
            
            try:
                # 解析单元索引表达式
                index_expr = parts[0]
                elem_ids = self.parser._parse_index_list(index_expr)
                
                # 解析荷载类型
                load_type = parts[1]
                
                # 解析拉力和drape值
                tension = float(parts[2])
                drape_i = float(parts[3])
                drape_m = float(parts[4])
                drape_j = float(parts[5])
                
                # 解析组名
                group = parts[6].strip() if len(parts) > 6 and parts[6].strip() else ""
                
                prestresses.append({
                    'elem_ids': elem_ids,
                    'type': load_type,
                    'tension': tension,
                    'drape_i': drape_i,
                    'drape_m': drape_m,
                    'drape_j': drape_j,
                    'group': group
                })
            
            except ValueError as e:
                self.parser.model.errors.append(f"解析预应力定义时出错: {line}，行号 {line_nums[i]}，错误: {str(e)}")
        
        prestress_data = {
            'prestresses': prestresses,
            'raw_lines': lines,
            'line_nums': line_nums
        }
        
        self.parser.model.add_command("PRESTRESS", prestress_data)

    def parse_conload(self, lines: List[str], line_nums: List[int]):
        """
        解析CONLOAD命令（节点荷载）
        
        根据MCT文档，CONLOAD命令格式为：
        NODE_LIST, FX, FY, FZ, MX, MY, MZ, GROUP
        
        参数说明：
        - NODE_LIST: 节点编号
        - FX: 全局坐标系X轴方向的集中荷载分量
        - FY: 全局坐标系Y轴方向的集中荷载分量
        - FZ: 全局坐标系Z轴方向的集中荷载分量
        - MX: 全局坐标系X轴方向的集中弯矩分量
        - MY: 全局坐标系Y轴方向的集中弯矩分量
        - MZ: 全局坐标系Z轴方向的集中弯矩分量
        - GROUP: Load Group Name
        
        Args:
            lines: 命令行列表
            line_nums: 行号列表
        """
        print("正在解析CONLOAD命令...")
        
        conloads = []
        
        # 跳过命令行
        for i, line in enumerate(lines[1:], 1):
            line = line.strip()
            if not line or line.startswith(';'):  # 跳过空行和注释行
                continue
            
            parts = re.split(r'\s*,\s*', line)
            if len(parts) < 2:  # 至少需要节点索引和至少一个荷载值
                self.parser.model.errors.append(f"无效的节点荷载定义: {line}，行号 {line_nums[i]}")
                continue
            
            try:
                # 解析节点索引表达式
                index_expr = parts[0]
                node_ids = self.parser._parse_index_list(index_expr)
                
                # 解析荷载值，默认为0
                load_values = []
                for j in range(1, min(len(parts), 7)):
                    try:
                        if parts[j].strip():
                            load_values.append(float(parts[j]))
                        else:
                            load_values.append(0.0)
                    except ValueError:
                        load_values.append(0.0)  # 默认为0
                
                # 确保有6个荷载分量
                while len(load_values) < 6:
                    load_values.append(0.0)
                
                # 解析组名
                group = parts[7].strip() if len(parts) > 7 and parts[7].strip() else ""
                
                # 创建荷载数据
                for node_id in node_ids:
                    conloads.append({
                        'node_id': node_id,
                        'fx': load_values[0],
                        'fy': load_values[1],
                        'fz': load_values[2],
                        'mx': load_values[3],
                        'my': load_values[4],
                        'mz': load_values[5],
                        'group': group
                    })
            
            except ValueError as e:
                self.parser.model.errors.append(f"解析节点荷载定义时出错: {line}，行号 {line_nums[i]}，错误: {str(e)}")
        
        # 创建并添加命令数据
        conload_data = ConLoad(loads=conloads, raw_lines=lines, line_nums=line_nums)
        self.parser.model.add_command("CONLOAD", conload_data)
    
    def parse_pressure(self, lines: List[str], line_nums: List[int]):
        """
        解析PRESSURE命令（面单元压力荷载）
        
        根据MCT文档，PRESSURE命令格式为：
        ELEM_LIST, P1, P2, P3, P4, GROUP
        
        参数说明：
        - ELEM_LIST: 单元编号
        - P1: 第一个节点压力值
        - P2: 第二个节点压力值
        - P3: 第三个节点压力值
        - P4: 第四个节点压力值
        - GROUP: Load Group Name
        
        Args:
            lines: 命令行列表
            line_nums: 行号列表
        """
        pressures = []
        
        # 跳过命令行
        for i, line in enumerate(lines[1:], 1):
            line = line.strip()
            if not line or line.startswith(';'):  # 跳过空行和注释行
                continue
            
            parts = re.split(r'\s*,\s*', line)
            if len(parts) < 2:  # 至少需要单元索引和至少一个压力值
                self.parser.model.errors.append(f"无效的压力荷载定义: {line}，行号 {line_nums[i]}")
                continue
            
            try:
                # 解析单元索引表达式
                index_expr = parts[0]
                elem_ids = self.parser._parse_index_list(index_expr)
                
                # 解析压力值，默认为0
                pressure_values = []
                for j in range(1, min(len(parts), 5)):
                    try:
                        if parts[j].strip():
                            pressure_values.append(float(parts[j]))
                        else:
                            pressure_values.append(0.0)
                    except ValueError:
                        pressure_values.append(0.0)  # 默认为0
                
                # 确保有4个压力值
                while len(pressure_values) < 4:
                    pressure_values.append(pressure_values[-1] if pressure_values else 0.0)
                
                # 解析组名
                group = parts[5].strip() if len(parts) > 5 and parts[5].strip() else ""
                
                # 创建压力荷载数据
                for elem_id in elem_ids:
                    pressures.append({
                        'elem_id': elem_id,
                        'p1': pressure_values[0],
                        'p2': pressure_values[1],
                        'p3': pressure_values[2],
                        'p4': pressure_values[3],
                        'group': group
                    })
            
            except ValueError as e:
                self.parser.model.errors.append(f"解析压力荷载定义时出错: {line}，行号 {line_nums[i]}，错误: {str(e)}")
        
        # 创建并添加命令数据，为保持一致，假设ConLoad class也有类似结构
        pressure_data = {
            'pressures': pressures,
            'raw_lines': lines,
            'line_nums': line_nums
        }
        
        self.parser.model.add_command("PRESSURE", pressure_data)
    
    def parse_eff_width(self, lines: List[str], line_nums: List[int]):
        """
        解析EFF-WIDTH命令（有效宽度因子）
        
        根据MCT文档，EFF-WIDTH命令格式为：
        ELEM_LIST, SCALE, GROUP
        
        参数说明：
        - ELEM_LIST: 考虑有效宽度的单元编号
        - SCALE: 输入对于Iy的增减系数
        - GROUP: Boundary Group Name
        
        Args:
            lines: 命令行列表
            line_nums: 行号列表
        """
        factors = {}
        
        # 跳过命令行
        for i, line in enumerate(lines[1:], 1):
            line = line.strip()
            if not line or line.startswith(';'):  # 跳过空行和注释行
                continue
            
            parts = re.split(r'\s*,\s*', line)
            if len(parts) < 2:  # 至少需要单元索引和缩放系数
                self.parser.model.errors.append(f"无效的有效宽度定义: {line}，行号 {line_nums[i]}")
                continue
            
            try:
                # 解析单元索引表达式
                index_expr = parts[0]
                elem_ids = self.parser._parse_index_list(index_expr)
                
                # 解析缩放系数
                scale_factor = float(parts[1])
                
                # 将每个单元ID映射到其缩放系数
                for elem_id in elem_ids:
                    factors[elem_id] = scale_factor
            
            except ValueError as e:
                self.parser.model.errors.append(f"解析有效宽度定义时出错: {line}，行号 {line_nums[i]}，错误: {str(e)}")
        
        # 导入模型类
        from ..models import EffWidth
        
        # 创建并添加命令数据
        eff_width_data = EffWidth(factors=factors, raw_lines=lines, line_nums=line_nums)
        self.parser.model.add_command("EFF-WIDTH", eff_width_data)
    
    def parse_loadtomass(self, lines: List[str], line_nums: List[int]):
        """
        解析LOADTOMASS命令（荷载转质量）
        
        根据MCT文档，LOADTOMASS命令格式为：
        *LOADTOMASS, DIR, bNODAL, bBEAM, bFLOOR, bPRES, GRAV
        LCNAME1, FACTOR1, LCNAME2, FACTOR2, ... (from line 1)
        
        参数说明：
        - DIR: 指定所要转换的质量的方向 {XY}
        - bNODAL: 选择是否转换节点荷载 (YES/NO) {YES}
        - bBEAM: 选择是否转换梁荷载(YES/NO) {YES}
        - bFLOOR: 选择是否转换楼板荷载(YES/NO) {YES}
        - bPRES: 选择是否转换输入荷载(YES/NO) {YES}
        - GRAV: 重力加速度 {9.806 m/sec²}
        - LCNAME1: 选择所要转换荷载的Load Case
        - FACTOR1: 输入在把荷载转换为质量时所采用的增减系数{1}
        
        Args:
            lines: 命令行列表
            line_nums: 行号列表
        """
        if len(lines) < 2:
            self.parser.model.errors.append("无效的LOADTOMASS命令: 缺少参数")
            return
        
        # 处理第一行参数
        header_line = lines[1].strip()
        if not header_line or header_line.startswith(';'):
            self.parser.model.errors.append("无效的LOADTOMASS命令: 缺少参数")
            return
        
        header_parts = re.split(r'\s*,\s*', header_line)
        
        # 解析方向和配置参数
        dir_str = header_parts[0] if len(header_parts) > 0 else "XY"
        b_nodal = header_parts[1].upper() == "YES" if len(header_parts) > 1 else True
        b_beam = header_parts[2].upper() == "YES" if len(header_parts) > 2 else True
        b_floor = header_parts[3].upper() == "YES" if len(header_parts) > 3 else True
        b_pres = header_parts[4].upper() == "YES" if len(header_parts) > 4 else True
        grav = float(header_parts[5]) if len(header_parts) > 5 else 9.806
        
        # 处理荷载工况和系数
        factors = {}
        
        for i, line in enumerate(lines[2:], 2):
            line = line.strip()
            if not line or line.startswith(';'):  # 跳过空行和注释行
                continue
            
            # 可能有多个荷载工况和系数对
            load_factor_pairs = re.split(r'\s*,\s*', line)
            
            # 处理每对荷载和系数
            j = 0
            while j < len(load_factor_pairs) - 1:
                lc_name = load_factor_pairs[j].strip()
                factor_str = load_factor_pairs[j+1].strip()
                
                if lc_name and factor_str:
                    try:
                        factor = float(factor_str)
                        factors[lc_name] = {"factor": factor}
                    except ValueError:
                        self.parser.model.errors.append(f"解析LOADTOMASS系数时出错: {line}，行号 {line_nums[i]}")
                
                j += 2
        
        # 创建配置和荷载系数字典
        loadtomass_data = {
            "config": {
                "direction": dir_str,
                "use_nodal": b_nodal,
                "use_beam": b_beam,
                "use_floor": b_floor,
                "use_pressure": b_pres,
                "gravity": grav
            },
            "factors": factors,
            "raw_lines": lines,
            "line_nums": line_nums
        }
        
        # 导入模型类并创建命令
        from ..models import LoadToMass
        loadtomass_obj = LoadToMass(factors=factors, raw_lines=lines, line_nums=line_nums)
        self.parser.model.add_command("LOADTOMASS", loadtomass_obj)
    
    def parse_loadcomb(self, lines: List[str], line_nums: List[int]):
        """
        解析LOADCOMB命令（荷载组合）
        
        根据MCT文档，LOADCOMB命令格式为：
        NAME=NAME, KIND, bACTIVE, iTYPE, DESC (line 1)
        ANAL1, LCNAME1, FACT1, ... (from line 2)
        
        参数说明：
        - NAME: 荷载组合条件的名称
          = gLCB: General LCB
          = cLCB: Concrete LCB
          = sLCB: Steel LCB
          = rLCB: SRC LCB
          = fLCB: Footing LCB
        - KIND: 荷载组合的种类
          = GEN: General
          = STEEL: Steel Design
          = CONC: Concrete Design
          = SRC: SRC Design
          = FDN: Footing Design
        - bACTIVE: 选择设计时所要使用的荷载组合条件(YES/NO)
        - iTYPE: 指定荷载组合方式
          = 0: Linear
          = 1: +SRSS
          = 2: -SRSS
        - DESC: 简单说明
        - ANAL1: 单位荷载条件的种类
          = ST: Static
          = RS: Response Spectrum
          = TH: Time History
          = MV: Moving
          = SM: Settlement
        - LCNAME1: 单位荷载条件的名称
        - FACT1: 输入单位荷载条件的荷载系数
        
        Args:
            lines: 命令行列表
            line_nums: 行号列表
        """
        if len(lines) < 2:
            self.parser.model.errors.append("无效的LOADCOMB命令: 缺少组合定义")
            return
        
        # 处理第一行，获取组合名称、类型、活跃状态等
        header_line = lines[1].strip()
        if not header_line:
            self.parser.model.errors.append("无效的LOADCOMB命令: 缺少组合名称")
            return
        
        # 先检查并记录可能的错误，但仍继续处理
        error_log = f"解析LOADCOMB第一行: {header_line}，行号 {line_nums[1]}"
        
        # 处理NAME=XXXX格式
        name_match = re.match(r'NAME\s*=\s*([^,]+)', header_line, re.IGNORECASE)
        if name_match:
            comb_name = name_match.group(1).strip()
            # 移除NAME=部分
            header_line = re.sub(r'NAME\s*=\s*[^,]+', '', header_line, 1).strip()
            # 去掉可能遗留的开头逗号
            if header_line.startswith(','):
                header_line = header_line[1:].strip()
        else:
            # 假设第一个字段就是名称
            parts = re.split(r'\s*,\s*', header_line)
            comb_name = parts[0].strip()
            header_line = ','.join(parts[1:]).strip()
        
        # 拆分剩余参数
        header_parts = re.split(r'\s*,\s*', header_line)
        
        # 初始化参数，设置默认值
        kind = header_parts[0].strip() if len(header_parts) > 0 else "GEN"
        active = header_parts[1].strip() if len(header_parts) > 1 else "YES"
        itype = header_parts[2].strip() if len(header_parts) > 2 else "0"
        desc = ','.join(header_parts[3:]).strip() if len(header_parts) > 3 else ""
        
        # 处理组合系数
        combinations = {}
        
        for i, line in enumerate(lines[2:], 2):
            line = line.strip()
            if not line or line.startswith(';'):  # 跳过空行和注释行
                continue
                
            # 如果行以CB,开头，表示这是一个特殊格式的组合行
            if line.startswith('CB,'):
                # 记录这行有问题但继续
                self.parser.model.errors.append(f"解析LOADCOMB系数时出错: {line}，行号 {line_nums[i]}")
                continue
                
            # 处理一般格式
            parts = re.split(r'\s*,\s*', line)
            if not parts:
                continue
            
            # 处理每组荷载和系数
            j = 0
            while j < len(parts):
                # 确保我们至少有两个项目可以处理 (LCNAME, FACTOR)
                if j + 1 < len(parts):
                    anal_type = parts[j].strip()
                    lc_name = parts[j+1].strip() if j+1 < len(parts) else ""
                    
                    # 检查是否有荷载系数
                    if j + 2 < len(parts):
                        factor_str = parts[j+2].strip()
                        
                        try:
                            # 尝试将系数转换为浮点数
                            if factor_str and factor_str != "-":
                                factor = float(factor_str)
                                
                                # 存储组合信息
                                key = f"{anal_type}_{lc_name}"
                                combinations[key] = factor
                            
                            # 移动到下一组
                            j += 3
                        except ValueError:
                            # 如果转换失败，可能是特殊格式或者缺失项
                            self.parser.model.errors.append(f"解析LOADCOMB系数时出错: {line}，行号 {line_nums[i]}")
                            j += 1  # 只移动一个位置，尝试找到新的组合开始
                    else:
                        # 缺少系数部分
                        j += 2  # 移动到下一个可能的组合开始
                else:
                    # 不够一个完整的组合
                    j += 1
        
        # 创建组合数据
        loadcomb_data = {
            "name": comb_name,
            "kind": kind,
            "active": active.upper() == "YES",
            "type": int(itype) if itype.isdigit() else 0,
            "description": desc,
            "combinations": combinations,
            "raw_lines": lines,
            "line_nums": line_nums
        }
        
        # 导入模型类并创建命令
        from ..models.commands import LoadComb
        loadcomb_obj = LoadComb(combinations=combinations, raw_lines=lines, line_nums=line_nums)
        self.parser.model.add_command("LOADCOMB", loadcomb_obj)
