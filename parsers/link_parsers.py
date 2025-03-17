"""
连接单元解析器模块

处理ELASTICLINK、RIGIDLINK、VLINK和FRICTION等连接单元命令
"""

from typing import Dict, List, Union, Optional, Any, Set, Tuple
import re

from ..models import (
    ElasticLink, RigidLink, VLink, Friction
)


class LinkParser:
    """连接单元解析器类"""
    
    def __init__(self, parser):
        """
        初始化连接单元解析器
        
        Args:
            parser: 父解析器引用
        """
        self.parser = parser
    
    def parse_elasticlink(self, lines: List[str], line_nums: List[int]):
        """
        解析ELASTICLINK命令 - 弹性连接
        
        支持以下格式:
        - iNO, iNODE1, iNODE2, LINK, ANGLE, R_SDx, R_SDy, R_SDz, R_SRx, R_SRy, R_SRz, SDx, SDy, SDz, SRx, SRy, SRz ... (GEN)
        - iNO, iNODE1, iNODE2, LINK, ANGLE, bSHEAR, DRy, DRz, GROUP (RIGID,SADDLE)
        - iNO, iNODE1, iNODE2, LINK, ANGLE, SDx, bSHEAR, DRy, DRz, GROUP (TENS,COMP)
        - iNO, iNODE1, iNODE2, LINK, ANGLE, DIR, FUNCTION, bSHEAR, DRENDI, GROUP (MULTI LINEAR)
        
        Args:
            lines: 命令行列表
            line_nums: 行号列表
        """
        links = {}
        
        for i, line in enumerate(lines):
            line = self.parser._preprocess_line(line)
            if not line or line.startswith(';') or line.startswith('*'):
                continue
            
            # 使用逗号分隔字段
            parts = re.split(r'\s*,\s*', line)
            if len(parts) < 5:  # 至少需要ID、主节点、从节点、LINK类型和ANGLE
                self.parser.model.errors.append(f"无效的弹性连接定义: {line}，行号 {line_nums[i]}，至少需要5个字段")
                continue
            
            try:
                link_id = int(parts[0])
                master_node = int(parts[1])
                slave_node = int(parts[2])
                link_type = parts[3].strip().upper()
                angle = float(parts[4]) if parts[4].strip() else 0.0
                
                # 根据链接类型解析不同格式
                options = {}
                
                if link_type == "GEN":
                    # 处理GEN类型：获取所有刚度值
                    stiffness = []
                    for j in range(5, min(17, len(parts))):
                        if parts[j].strip():
                            try:
                                k = float(parts[j])
                            except ValueError:
                                k = 0.0  # 无效刚度值视为0
                            stiffness.append(k)
                    
                    # 补全可能缺失的刚度值
                    while len(stiffness) < 12:
                        stiffness.append(0.0)
                    
                    options["stiffness"] = stiffness
                    
                    # 解析GROUP（如果存在）
                    if len(parts) > 17 and parts[17].strip():
                        options["group"] = parts[17].strip()
                
                elif link_type in ["RIGID", "SADDLE"]:
                    # 解析RIGID或SADDLE类型
                    if len(parts) > 5:
                        options["bSHEAR"] = parts[5].strip().upper() == "YES"
                    
                    if len(parts) > 6 and parts[6].strip():
                        try:
                            options["DRy"] = float(parts[6])
                        except ValueError:
                            pass
                    
                    if len(parts) > 7 and parts[7].strip():
                        try:
                            options["DRz"] = float(parts[7])
                        except ValueError:
                            pass
                    
                    if len(parts) > 8 and parts[8].strip():
                        options["group"] = parts[8].strip()
                
                elif link_type in ["TENS", "COMP"]:
                    # 解析TENS或COMP类型
                    if len(parts) > 5 and parts[5].strip():
                        try:
                            options["SDx"] = float(parts[5])
                        except ValueError:
                            pass
                    
                    if len(parts) > 6:
                        options["bSHEAR"] = parts[6].strip().upper() == "YES"
                    
                    if len(parts) > 7 and parts[7].strip():
                        try:
                            options["DRy"] = float(parts[7])
                        except ValueError:
                            pass
                    
                    if len(parts) > 8 and parts[8].strip():
                        try:
                            options["DRz"] = float(parts[8])
                        except ValueError:
                            pass
                    
                    if len(parts) > 9 and parts[9].strip():
                        options["group"] = parts[9].strip()
                
                elif "MULTI" in link_type:
                    # 解析MULTI LINEAR类型
                    if len(parts) > 5 and parts[5].strip():
                        options["DIR"] = parts[5].strip()
                    
                    if len(parts) > 6 and parts[6].strip():
                        options["FUNCTION"] = parts[6].strip()
                    
                    if len(parts) > 7:
                        options["bSHEAR"] = parts[7].strip().upper() == "YES"
                    
                    if len(parts) > 8 and parts[8].strip():
                        try:
                            options["DRENDI"] = float(parts[8])
                        except ValueError:
                            pass
                    
                    if len(parts) > 9 and parts[9].strip():
                        options["group"] = parts[9].strip()
                
                else:
                    # 未知链接类型的通用处理
                    for j in range(5, len(parts)):
                        if parts[j].strip():
                            options[f"param{j-5}"] = parts[j].strip()
                
                links[link_id] = {
                    'id': link_id,
                    'master_node': master_node,
                    'slave_node': slave_node,
                    'link_type': link_type,
                    'angle': angle,
                    'options': options
                }
            
            except ValueError as e:
                self.parser.model.errors.append(f"解析弹性连接定义时出错: {line}，行号 {line_nums[i]}，错误: {str(e)}")
        
        elastic_link_data = ElasticLink(links=links, raw_lines=lines, line_nums=line_nums)
        self.parser.model.add_command("ELASTICLINK", elastic_link_data)
    
    def parse_rigidlink(self, lines: List[str], line_nums: List[int]):
        """
        解析RIGIDLINK命令 - 刚性连接
        
        Args:
            lines: 命令行列表
            line_nums: 行号列表
        """
        links = []
        
        # 跳过命令行
        for i, line in enumerate(lines[1:], 1):
            line = line.strip()
            if not line:
                continue
            
            parts = line.split()
            if len(parts) < 3:  # 至少需要ID、主节点、从节点
                self.parser.model.errors.append(f"无效的刚性连接定义: {line}，行号 {line_nums[i]}")
                continue
            
            try:
                link_id = int(parts[0])
                master_node = int(parts[1])
                
                # 解析从节点列表
                slave_nodes = []
                for j in range(2, len(parts)):
                    if parts[j].isdigit():
                        slave_nodes.append(int(parts[j]))
                    else:
                        break  # 非数字，可能是选项参数
                
                # 解析可选的附加参数
                options = {}
                if len(parts) > 2 + len(slave_nodes):
                    options_str = ' '.join(parts[2 + len(slave_nodes):])
                    
                    if 'DOF=' in options_str:
                        dof_match = re.search(r'DOF=(\w+)', options_str)
                        if dof_match:
                            options['dof'] = dof_match.group(1)
                    
                    if 'TYPE=' in options_str:
                        type_match = re.search(r'TYPE=(\w+)', options_str)
                        if type_match:
                            options['type'] = type_match.group(1)
                    
                    if 'ACTIVE=' in options_str:
                        active_match = re.search(r'ACTIVE=(\w+)', options_str)
                        if active_match:
                            options['active'] = active_match.group(1)
                
                links.append({
                    'id': link_id,
                    'master_node': master_node,
                    'slave_nodes': slave_nodes,
                    'options': options
                })
            
            except ValueError as e:
                self.parser.model.errors.append(f"解析刚性连接定义时出错: {line}，行号 {line_nums[i]}，错误: {str(e)}")
        
        rigid_link_data = RigidLink(links=links, raw_lines=lines, line_nums=line_nums)
        self.parser.model.add_command("RIGIDLINK", rigid_link_data)
    
    def parse_vlink(self, lines: List[str], line_nums: List[int]):
        """
        解析VLINK命令 - 虚拟连接
        
        Args:
            lines: 命令行列表
            line_nums: 行号列表
        """
        links = []
        
        # 跳过命令行
        for i, line in enumerate(lines[1:], 1):
            line = line.strip()
            if not line:
                continue
            
            parts = line.split()
            if len(parts) < 3:  # 至少需要ID、主节点和方向
                self.parser.model.errors.append(f"无效的虚拟连接定义: {line}，行号 {line_nums[i]}")
                continue
            
            try:
                link_id = int(parts[0])
                node_id = int(parts[1])
                direction = parts[2]
                
                # 解析可选的附加参数
                offset = []
                if len(parts) > 3:
                    for j in range(3, min(6, len(parts))):
                        try:
                            val = float(parts[j])
                        except ValueError:
                            val = 0.0  # 无效值视为0
                        offset.append(val)
                
                # 补全可能缺失的偏移值
                while len(offset) < 3:
                    offset.append(0.0)
                
                options = {}
                if len(parts) > 6:
                    options_str = ' '.join(parts[6:])
                    
                    if 'TYPE=' in options_str:
                        type_match = re.search(r'TYPE=(\w+)', options_str)
                        if type_match:
                            options['type'] = type_match.group(1)
                    
                    if 'ACTIVE=' in options_str:
                        active_match = re.search(r'ACTIVE=(\w+)', options_str)
                        if active_match:
                            options['active'] = active_match.group(1)
                
                links.append({
                    'id': link_id,
                    'node_id': node_id,
                    'direction': direction,
                    'offset': offset,
                    'options': options
                })
            
            except ValueError as e:
                self.parser.model.errors.append(f"解析虚拟连接定义时出错: {line}，行号 {line_nums[i]}，错误: {str(e)}")
        
        vlink_data = VLink(links=links, raw_lines=lines, line_nums=line_nums)
        self.parser.model.add_command("VLINK", vlink_data)
    
    def parse_friction(self, lines: List[str], line_nums: List[int]):
        """
        解析FRICTION命令 - 摩擦连接
        
        Args:
            lines: 命令行列表
            line_nums: 行号列表
        """
        frictions = []
        
        # 跳过命令行
        for i, line in enumerate(lines[1:], 1):
            line = line.strip()
            if not line:
                continue
            
            parts = line.split()
            if len(parts) < 5:  # 至少需要ID、方向、两个节点和摩擦系数
                self.parser.model.errors.append(f"无效的摩擦连接定义: {line}，行号 {line_nums[i]}")
                continue
            
            try:
                friction_id = int(parts[0])
                direction = parts[1]
                node1 = int(parts[2])
                node2 = int(parts[3])
                coefficient = float(parts[4])
                
                # 解析可选的stiffness参数
                stiffness = float(parts[5]) if len(parts) > 5 else 0.0
                
                # 解析可选的附加参数
                options = {}
                if len(parts) > 6:
                    options_str = ' '.join(parts[6:])
                    
                    if 'LOCALID=' in options_str:
                        local_match = re.search(r'LOCALID=(\d+)', options_str)
                        if local_match:
                            options['local_id'] = int(local_match.group(1))
                    
                    if 'GAP=' in options_str:
                        gap_match = re.search(r'GAP=([\d.]+)', options_str)
                        if gap_match:
                            options['gap'] = float(gap_match.group(1))
                    
                    if 'ACTIVE=' in options_str:
                        active_match = re.search(r'ACTIVE=(\w+)', options_str)
                        if active_match:
                            options['active'] = active_match.group(1)
                
                frictions.append({
                    'id': friction_id,
                    'direction': direction,
                    'node1': node1,
                    'node2': node2,
                    'coefficient': coefficient,
                    'stiffness': stiffness,
                    'options': options
                })
            
            except ValueError as e:
                self.parser.model.errors.append(f"解析摩擦连接定义时出错: {line}，行号 {line_nums[i]}，错误: {str(e)}")
        
        friction_data = Friction(frictions=frictions, raw_lines=lines, line_nums=line_nums)
        self.parser.model.add_command("FRICTION", friction_data)
